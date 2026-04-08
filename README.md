# ProWork AI

Multi-agent AI system for task, schedule, and day-planning automation using **Google ADK**, **Gemini (Vertex AI)**, **AlloyDB**, and **Cloud Run**.

---

## Architecture

```
User ─▸ ADK Web UI (Cloud Run)
            │
            ▼
     ProWorkOrchestrator  (root LlmAgent)
         ├── TaskAgent       sub-agent  ← tasks: view, add, update
         ├── ScheduleAgent   sub-agent  ← calendar: view, add, update, delete
         └── PlannerAgent    sub-agent  ← generates optimized day plans
                    │
                    ▼
            SQLAlchemy ─▸ AlloyDB (PostgreSQL)
```

---

## Project Structure

```
ProWork-AI/
├── prowork_agents/          # Google ADK agent package
│   ├── __init__.py
│   ├── agent.py             # root_agent (ADK entry-point, orchestrator)
│   ├── task_agent.py        # TaskAgent sub-agent
│   ├── schedule_agent.py    # ScheduleAgent sub-agent
│   ├── planner_agent.py     # PlannerAgent sub-agent
│   ├── tools.py             # AlloyDB tool functions (list_users, tasks, calendar, etc.)
│   ├── callbacks.py         # before_model callbacks & mock LLM fallback
│   ├── config.py            # MODEL, DATE_CONTEXT, logger
│   ├── db.py                # SQLAlchemy engine & serialize helper
│   └── .env                 # Environment variables (not committed)
├── requirements.txt
├── Dockerfile
├── .gitignore
└── .dockerignore
```

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Runtime |
| Google Cloud SDK (`gcloud`) | Auth, deployment |
| AlloyDB instance | Data store |
| Vertex AI enabled | LLM backend (Gemini) |

---

## Setup

### 1. Clone & install dependencies

```bash
git clone <your-repo-url> && cd ProWork-AI

python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Configure environment variables

Create `prowork_agents/.env`:

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your-password
ALLOYDB_HOST=your-alloydb-ip
ALLOYDB_PORT=5432
ALLOYDB_DB=postgres
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 4. Run locally

```bash
# ADK web UI
adk web prowork_agents

# ADK CLI (interactive REPL)
adk run prowork_agents
```

### 5. Deploy to Cloud Run

```bash
gcloud run deploy prowork-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=us-central1,ALLOYDB_USER=postgres,ALLOYDB_PASSWORD=your-password,ALLOYDB_HOST=your-alloydb-ip,ALLOYDB_PORT=5432,ALLOYDB_DB=postgres" \
  --memory 1Gi --cpu 1 --max-instances 3 --timeout 300 \
  --network default --subnet default --vpc-egress private-ranges-only
```

Then update `TOOLBOX_URL` to the resulting Cloud Run URL before deploying the app.

---

## Tech Stack

- **Google ADK** – agent framework (`LlmAgent`, `sub_agents`, delegation)
- **Gemini** – LLM backend (via API key or Vertex AI)
- **MCP Toolbox** – middleware exposing AlloyDB as callable tools
- **AlloyDB / PostgreSQL** – structured data & vector search
- **FastAPI** – HTTP API layer
- **Cloud Run** – serverless deployment

---

## License

MIT
