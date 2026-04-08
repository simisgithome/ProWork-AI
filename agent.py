"""
ProWork AI – ADK root agent (orchestrator).

Exposes `root_agent` at module level for ADK CLI discovery.
Sub-agents are imported from their own modules.
"""

from google.adk.agents import LlmAgent

from .callbacks import root_before_model
from .config import DATE_CONTEXT, MODEL
from .planner_agent import planner_agent
from .schedule_agent import schedule_agent
from .task_agent import task_agent
from .tools import list_users

# =========================================================
# ROOT AGENT (ADK convention: root_agent at module level)
# =========================================================
root_agent = LlmAgent(
    name="ProWorkOrchestrator",
    model=MODEL,
    description="ProWork AI root orchestrator that delegates to sub-agents.",
    instruction="""You are ProWork AI, a smart productivity assistant.
You coordinate a team of specialised sub-agents:
 - TaskAgent – fetches, adds, and updates tasks in AlloyDB
 - ScheduleAgent – fetches, adds, updates, and deletes calendar events in AlloyDB
 - PlannerAgent – generates optimized day plans with time-blocked schedules

WORKFLOW:
1. When the user first says hello or starts a conversation, greet them warmly and explain what you can do:
   - View, add, or prioritize tasks
   - View, add, or manage calendar events
   - Generate an optimized day plan
2. Ask which user they are (use list_users to show available users if needed).
3. Once you know the user and their intent, route to the correct sub-agent.

ROUTING RULES:
- Plan day/week, optimize schedule → PlannerAgent
- Tasks (view, add, update, mark done, prioritize) → TaskAgent
- Calendar/events (view, add, reschedule, cancel) → ScheduleAgent

IMPORTANT:
- NEVER assume user_id. Always ask or look up the user first.
- For greetings like 'hi', 'hello', introduce yourself and ask how you can help.
- Be conversational, helpful, and confirm actions taken.""" + DATE_CONTEXT,
    sub_agents=[task_agent, schedule_agent, planner_agent],
    tools=[list_users],
    before_model_callback=root_before_model,
)
