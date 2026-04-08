"""Shared configuration for ProWork AI agents."""

import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash"

# Current date context for LLM (so it can resolve "today", "tomorrow", etc.)
_TODAY = datetime.utcnow().strftime("%Y-%m-%d")
_TOMORROW = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
DATE_CONTEXT = (
    f"\nIMPORTANT: Today's date is {_TODAY}. Tomorrow is {_TOMORROW}. "
    "When the user says 'today', 'tomorrow', 'next Monday', etc., "
    "automatically resolve these to actual ISO dates (YYYY-MM-DDTHH:MM:SS). "
    "Never ask the user to specify the exact date when the relative date is clear."
)

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prowork_agents")
