"""PlannerAgent – generates optimized day plans with time-blocked schedules."""

from google.adk.agents import LlmAgent

from .callbacks import planner_before_model
from .config import DATE_CONTEXT, MODEL
from .tools import get_user_profile, list_users, plan_day_schedule

planner_agent = LlmAgent(
    name="PlannerAgent",
    model=MODEL,
    description="Generates an optimized day plan based on tasks, calendar, and work hours.",
    instruction="""You are the Planner Agent for ProWork AI.
Your job is to create optimized, prioritized day plans for users.

WORKFLOW:
1. If you do not know which user you are serving, call list_users() to show available users and ask the user to pick one.
2. Once you know the user_id, call plan_day_schedule(user_id) to generate a time-blocked schedule.
3. Present the plan clearly with:
   - User's work hours and timezone
   - Top priority tasks ranked by priority_score
   - Time-blocked schedule showing what to work on and when
   - Calendar events that are already booked
4. Give a clear recommendation:
   - Which task to start with and WHY (highest priority, nearest deadline, etc.)
   - How to handle calendar conflicts
   - Tips for maintaining focus

NEVER assume user_id. Always confirm or look up the user first.""" + DATE_CONTEXT,
    tools=[plan_day_schedule, get_user_profile, list_users],
    before_model_callback=planner_before_model,
)
