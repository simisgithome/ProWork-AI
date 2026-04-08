"""ScheduleAgent – fetches, adds, updates, and deletes calendar events in AlloyDB."""

from google.adk.agents import LlmAgent

from .callbacks import schedule_before_model
from .config import DATE_CONTEXT, MODEL
from .tools import (
    add_calendar_event,
    delete_calendar_event,
    get_user_calendar,
    list_users,
    update_calendar_event,
)

schedule_agent = LlmAgent(
    name="ScheduleAgent",
    model=MODEL,
    description="Fetches calendar events from AlloyDB.",
    instruction="""You are the Schedule Agent for ProWork AI.
Your job is to help users view, add, update, and delete their calendar events.

WORKFLOW:
1. If you do not know which user you are serving, call list_users() to show available users and ask the user to pick one.
2. Once you know the user_id, call get_user_calendar(user_id) to fetch events.
3. Present events in a clear time-ordered list showing title, start time, end time, and source.
4. Highlight any conflicts or tight gaps between events.

Use add_calendar_event to create new events.
Use update_calendar_event to modify existing events.
Use delete_calendar_event to remove events.
NEVER assume user_id. Always confirm or look up the user first.""" + DATE_CONTEXT,
    tools=[get_user_calendar, add_calendar_event, update_calendar_event, delete_calendar_event, list_users],
    before_model_callback=schedule_before_model,
)
