"""ADK tool functions for AlloyDB operations."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text

from .db import get_engine, serialize


def list_users() -> list:
    """List all available users in the system.

    Returns:
        List of users with id, name, and email.
    """
    query = text("SELECT id, name, email FROM users ORDER BY id")
    with get_engine().connect() as conn:
        rows = conn.execute(query).mappings().all()
        return [dict(r) for r in rows]


def get_user_profile(user_id: int) -> dict:
    """Get a user's profile including name, email, timezone, and work hours.

    Args:
        user_id: The ID of the user to look up.

    Returns:
        dict with id, name, email, timezone, work_start_hour, work_end_hour.
    """
    query = text("""
        SELECT id, name, email, timezone, work_start_hour, work_end_hour
        FROM users WHERE id = :user_id
    """)
    with get_engine().connect() as conn:
        row = conn.execute(query, {"user_id": user_id}).mappings().first()
        if not row:
            return {"error": f"User {user_id} not found"}
        return serialize(dict(row))


def get_user_tasks(user_id: int) -> list:
    """Get all tasks for a user, ordered by priority (highest first).

    Args:
        user_id: The user ID to get tasks for.

    Returns:
        List of tasks with id, title, description, due_at, priority_score,
        estimated_minutes, status.
    """
    query = text("""
        SELECT id, title, description, due_at, priority_score,
               estimated_minutes, status
        FROM tasks
        WHERE user_id = :user_id
        ORDER BY priority_score DESC, due_at ASC
    """)
    with get_engine().connect() as conn:
        rows = conn.execute(query, {"user_id": user_id}).mappings().all()
        return serialize([dict(r) for r in rows])


def get_user_calendar(user_id: int) -> list:
    """Get all calendar events for a user, ordered by start time.

    Args:
        user_id: The user ID to get calendar events for.

    Returns:
        List of events with id, title, start_time, end_time, source.
    """
    query = text("""
        SELECT id, title, start_time, end_time, source
        FROM calendar_events
        WHERE user_id = :user_id
        ORDER BY start_time ASC
    """)
    with get_engine().connect() as conn:
        rows = conn.execute(query, {"user_id": user_id}).mappings().all()
        return serialize([dict(r) for r in rows])


def plan_day_schedule(user_id: int, goal: str = "Plan my day") -> dict:
    """Generate a complete day plan for a user with time-blocked schedule.

    Fetches the user's profile, tasks, and calendar events from AlloyDB,
    then generates an optimized schedule based on task priorities and
    available work hours.

    Args:
        user_id: The user ID to plan for.
        goal: The planning goal or objective.

    Returns:
        dict with user info, top_priorities, schedule_plan, and recommendation.
    """
    user = get_user_profile(user_id)
    if "error" in user:
        return user

    tasks = get_user_tasks(user_id)
    events = get_user_calendar(user_id)

    top_tasks = tasks[:3]

    work_start = user.get("work_start_hour", 9)
    work_end = user.get("work_end_hour", 18)

    day_start = datetime.utcnow().replace(
        hour=work_start, minute=0, second=0, microsecond=0
    )
    day_end = datetime.utcnow().replace(
        hour=work_end, minute=0, second=0, microsecond=0
    )

    cursor = day_start
    schedule_plan = []

    for task in top_tasks:
        duration = task.get("estimated_minutes", 60) or 60
        planned_end = cursor + timedelta(minutes=duration)

        if planned_end > day_end:
            break

        schedule_plan.append({
            "task": task["title"],
            "start": cursor.isoformat(),
            "end": planned_end.isoformat(),
            "duration_minutes": duration,
            "priority_score": task["priority_score"],
        })

        cursor = planned_end

    recommendation = (
        "Complete the highest-priority task first and protect focus time."
    )
    if len(events) >= 3:
        recommendation = (
            "Your calendar is already busy. "
            "Focus on the top task first and avoid context switching."
        )
    if not top_tasks:
        recommendation = (
            "No tasks found for this user. Add tasks first before planning."
        )

    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "timezone": user["timezone"],
        },
        "goal": goal,
        "top_priorities": [
            {
                "title": t["title"],
                "priority_score": t["priority_score"],
                "estimated_minutes": t["estimated_minutes"],
            }
            for t in top_tasks
        ],
        "calendar_event_count": len(events),
        "schedule_plan": schedule_plan,
        "recommendation": recommendation,
    }


def add_calendar_event(
    user_id: int, title: str, start_time: str, end_time: str, source: str = "manual"
) -> dict:
    """Add a new calendar event for a user.

    Args:
        user_id: The user ID to create the event for.
        title: Title/name of the event (e.g. 'Team standup').
        start_time: Start time in ISO format (e.g. '2026-04-09T09:00:00').
        end_time: End time in ISO format (e.g. '2026-04-09T09:30:00').
        source: Source of the event (default 'manual').

    Returns:
        dict with the created event id and details.
    """
    query = text("""
        INSERT INTO calendar_events (user_id, title, start_time, end_time, source)
        VALUES (:user_id, :title, :start_time, :end_time, :source)
        RETURNING id, title, start_time, end_time, source
    """)
    with get_engine().connect() as conn:
        row = conn.execute(query, {
            "user_id": user_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "source": source,
        }).mappings().first()
        conn.commit()
        return {"status": "created", "event": serialize(dict(row))}


def update_calendar_event(
    event_id: int,
    title: str = "",
    start_time: str = "",
    end_time: str = "",
) -> dict:
    """Update an existing calendar event. Only non-empty fields are changed.

    Args:
        event_id: The ID of the calendar event to update.
        title: New title (leave empty to keep current).
        start_time: New start time in ISO format (leave empty to keep current).
        end_time: New end time in ISO format (leave empty to keep current).

    Returns:
        dict with the updated event details.
    """
    sets = []
    params: dict[str, Any] = {"event_id": event_id}
    if title:
        sets.append("title = :title")
        params["title"] = title
    if start_time:
        sets.append("start_time = :start_time")
        params["start_time"] = start_time
    if end_time:
        sets.append("end_time = :end_time")
        params["end_time"] = end_time
    if not sets:
        return {"error": "No fields to update"}
    query = text(
        f"UPDATE calendar_events SET {', '.join(sets)} "
        "WHERE id = :event_id "
        "RETURNING id, title, start_time, end_time, source"
    )
    with get_engine().connect() as conn:
        row = conn.execute(query, params).mappings().first()
        conn.commit()
        if not row:
            return {"error": f"Event {event_id} not found"}
        return {"status": "updated", "event": serialize(dict(row))}


def delete_calendar_event(event_id: int) -> dict:
    """Delete a calendar event by its ID.

    Args:
        event_id: The ID of the calendar event to delete.

    Returns:
        dict confirming deletion.
    """
    query = text(
        "DELETE FROM calendar_events WHERE id = :event_id RETURNING id"
    )
    with get_engine().connect() as conn:
        row = conn.execute(query, {"event_id": event_id}).mappings().first()
        conn.commit()
        if not row:
            return {"error": f"Event {event_id} not found"}
        return {"status": "deleted", "event_id": row["id"]}


def add_task(
    user_id: int,
    title: str,
    description: str = "",
    due_at: str = "",
    priority_score: int = 5,
    estimated_minutes: int = 60,
    status: str = "pending",
) -> dict:
    """Add a new task for a user.

    Args:
        user_id: The user ID to create the task for.
        title: Title of the task.
        description: Detailed description (optional).
        due_at: Due date/time in ISO format (optional).
        priority_score: Priority from 1 (low) to 10 (high), default 5.
        estimated_minutes: Estimated time in minutes, default 60.
        status: Task status, default 'pending'.

    Returns:
        dict with the created task details.
    """
    query = text("""
        INSERT INTO tasks (user_id, title, description, due_at,
                          priority_score, estimated_minutes, status)
        VALUES (:user_id, :title, :description,
                CASE WHEN :due_at = '' THEN NULL ELSE :due_at::timestamp END,
                :priority_score, :estimated_minutes, :status)
        RETURNING id, title, description, due_at, priority_score,
                  estimated_minutes, status
    """)
    with get_engine().connect() as conn:
        row = conn.execute(query, {
            "user_id": user_id,
            "title": title,
            "description": description,
            "due_at": due_at,
            "priority_score": priority_score,
            "estimated_minutes": estimated_minutes,
            "status": status,
        }).mappings().first()
        conn.commit()
        return {"status": "created", "task": serialize(dict(row))}


def update_task(
    task_id: int,
    title: str = "",
    description: str = "",
    due_at: str = "",
    priority_score: int = 0,
    estimated_minutes: int = 0,
    status: str = "",
) -> dict:
    """Update an existing task. Only non-empty/non-zero fields are changed.

    Args:
        task_id: The ID of the task to update.
        title: New title (leave empty to keep current).
        description: New description (leave empty to keep current).
        due_at: New due date in ISO format (leave empty to keep current).
        priority_score: New priority 1-10 (0 to keep current).
        estimated_minutes: New estimate (0 to keep current).
        status: New status e.g. 'pending', 'in_progress', 'done' (leave empty to keep).

    Returns:
        dict with the updated task details.
    """
    sets = []
    params: dict[str, Any] = {"task_id": task_id}
    if title:
        sets.append("title = :title")
        params["title"] = title
    if description:
        sets.append("description = :description")
        params["description"] = description
    if due_at:
        sets.append("due_at = :due_at::timestamp")
        params["due_at"] = due_at
    if priority_score:
        sets.append("priority_score = :priority_score")
        params["priority_score"] = priority_score
    if estimated_minutes:
        sets.append("estimated_minutes = :estimated_minutes")
        params["estimated_minutes"] = estimated_minutes
    if status:
        sets.append("status = :status")
        params["status"] = status
    if not sets:
        return {"error": "No fields to update"}
    query = text(
        f"UPDATE tasks SET {', '.join(sets)} "
        "WHERE id = :task_id "
        "RETURNING id, title, description, due_at, priority_score, "
        "estimated_minutes, status"
    )
    with get_engine().connect() as conn:
        row = conn.execute(query, params).mappings().first()
        conn.commit()
        if not row:
            return {"error": f"Task {task_id} not found"}
        return {"status": "updated", "task": serialize(dict(row))}
