"""Mock LLM fallback system and before_model callbacks."""

import os
import threading
import time

from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.genai import types as genai_types

from .config import logger

# =========================================================
# MOCK LLM FALLBACK  (rate-limit aware)
# =========================================================
_call_lock = threading.Lock()
_call_timestamps: list[float] = []
_rate_limited_until: float = 0
_MAX_CALLS_PER_MINUTE = int(os.getenv("MAX_LLM_CALLS_PER_MINUTE", "2"))
_COOLDOWN_SECONDS = int(os.getenv("MOCK_COOLDOWN_SECONDS", "3600"))


def _should_use_mock() -> bool:
    """Return True only when MOCK_LLM env var is explicitly set."""
    return os.getenv("MOCK_LLM", "").lower() in ("true", "1", "yes")


def _track_real_call():
    """Count a real model call; trigger mock mode if threshold exceeded."""
    global _rate_limited_until
    now = time.time()
    with _call_lock:
        _call_timestamps[:] = [t for t in _call_timestamps if now - t < 60]
        _call_timestamps.append(now)
        if len(_call_timestamps) >= _MAX_CALLS_PER_MINUTE:
            _rate_limited_until = now + _COOLDOWN_SECONDS
            logger.warning(
                "Rate-limit threshold (%d calls/min) reached – "
                "mock LLM active for %d s",
                _MAX_CALLS_PER_MINUTE,
                _COOLDOWN_SECONDS,
            )


def _mock_text(text: str) -> LlmResponse:
    return LlmResponse(
        content=genai_types.Content(
            role="model",
            parts=[genai_types.Part(text=text)],
        )
    )


def _mock_fn_call(name: str, args: dict) -> LlmResponse:
    return LlmResponse(
        content=genai_types.Content(
            role="model",
            parts=[
                genai_types.Part(
                    function_call=genai_types.FunctionCall(
                        name=name, args=args
                    ),
                )
            ],
        )
    )


def _last_user_text(llm_request: LlmRequest) -> str:
    try:
        for c in reversed(llm_request.contents or []):
            if c.role == "user":
                for p in (c.parts or []):
                    if hasattr(p, "text") and p.text:
                        return p.text.lower()
    except Exception:
        pass
    return ""


def _has_tool_result(llm_request: LlmRequest) -> bool:
    try:
        if llm_request.contents:
            last = llm_request.contents[-1]
            for p in (last.parts or []):
                if hasattr(p, "function_response") and p.function_response:
                    return True
    except Exception:
        pass
    return False


# ── keyword sets for intent detection ───────────────────────────
_TASK_WORDS = (
    "task", "todo", "to-do", "priority", "work item",
    "add task", "update task", "mark done", "complete task",
    "my tasks", "pending", "backlog",
)
_SCHEDULE_WORDS = (
    "calendar", "event", "meeting", "schedule", "appointment",
    "add event", "reschedule", "cancel event", "delete event",
    "book", "block time", "free slot",
)
_PLANNER_WORDS = (
    "plan my day", "plan my week", "day plan", "optimise",
    "optimize", "time block", "daily plan", "weekly plan",
    "what should i do", "how should i spend",
)


def _detect_intent(txt: str):
    """Return agent name if a clear intent is found, else None."""
    if any(w in txt for w in _TASK_WORDS):
        return "TaskAgent"
    if any(w in txt for w in _SCHEDULE_WORDS):
        return "ScheduleAgent"
    if any(w in txt for w in _PLANNER_WORDS):
        return "PlannerAgent"
    return None


# ── per-agent before_model callbacks ────────────────────────────
def root_before_model(callback_context, llm_request):
    if not _should_use_mock():
        _track_real_call()
        return None
    logger.info("[MockLLM] root → mock fallback")
    txt = _last_user_text(llm_request)
    agent = _detect_intent(txt)
    if agent:
        return _mock_fn_call("transfer_to_agent", {"agent_name": agent})
    return _mock_text(
        "Hello! I'm ProWork AI, your productivity assistant. "
        "I can help you with:\n"
        "- **Tasks** – view, add, or update your tasks\n"
        "- **Calendar** – view, add, reschedule, or cancel events\n"
        "- **Day Planning** – create an optimised time-blocked schedule\n\n"
        "What would you like to do?"
    )


def task_before_model(callback_context, llm_request):
    if not _should_use_mock():
        _track_real_call()
        return None
    logger.info("[MockLLM] TaskAgent → mock fallback")
    txt = _last_user_text(llm_request)
    if _has_tool_result(llm_request):
        return _mock_text(
            "Here are your tasks from AlloyDB, ordered by priority score "
            "(highest first). Focus on the top-priority item to maximise "
            "your productivity today."
        )
    if any(w in txt for w in ("add", "create", "new task")):
        return _mock_text(
            "I'd be happy to add a task for you. Could you tell me the "
            "task title, priority (1-10), and an optional due date?"
        )
    if any(w in txt for w in ("update", "change", "modify", "edit", "mark done", "complete")):
        return _mock_fn_call("get_user_tasks", {"user_id": 1})
    return _mock_fn_call("get_user_tasks", {"user_id": 1})


def schedule_before_model(callback_context, llm_request):
    if not _should_use_mock():
        _track_real_call()
        return None
    logger.info("[MockLLM] ScheduleAgent → mock fallback")
    txt = _last_user_text(llm_request)
    if _has_tool_result(llm_request):
        return _mock_text(
            "Here are your upcoming calendar events. Review the times "
            "above to plan your availability for the day."
        )
    if any(w in txt for w in ("add", "create", "new", "book", "block")):
        return _mock_text(
            "I'd be happy to add an event. Could you provide the event "
            "title, start time, and end time?"
        )
    if any(w in txt for w in ("delete", "cancel", "remove")):
        return _mock_fn_call("get_user_calendar", {"user_id": 1})
    return _mock_fn_call("get_user_calendar", {"user_id": 1})


def planner_before_model(callback_context, llm_request):
    if not _should_use_mock():
        _track_real_call()
        return None
    logger.info("[MockLLM] PlannerAgent → mock fallback")
    if _has_tool_result(llm_request):
        return _mock_text(
            "Your optimised day plan is ready. Follow the time-blocked "
            "schedule and tackle the highest-priority task first. "
            "Protect focus time and avoid context switching."
        )
    return _mock_fn_call(
        "plan_day_schedule", {"user_id": 1, "goal": "Plan my day"}
    )
