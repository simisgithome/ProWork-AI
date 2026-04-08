# ProWork AI

Multi-agent AI system for task, schedule, and workflow automation using **Google ADK**, **Gemini**, **MCP Toolbox**, **AlloyDB**, and **FastAPI**.

---

## Architecture

```
User ─▸ FastAPI (app.py)
            │
            ▼
     ProWorkOrchestrator  (root LlmAgent)
         ├── TaskManager        sub-agent  ← toolbox: list_tasks, create_task, update_task_status
         ├── ScheduleManager    sub-agent  ← toolbox: list_schedule, create_schedule_event
         └── KnowledgeAgent     sub-agent  ← toolbox: search_knowledge
                    │
                    ▼
            MCP Toolbox server  (tools.yaml)
                    │
                    ▼
               AlloyDB / PostgreSQL
```

---

## Project Layout

```
ProWork-AI/
├── prowork_agents/          # Google ADK agent package
│   ├── __init__.py
│   ├── agent.py             # root_agent  (ADK entry‑point)
│   ├── task_agent.py        # TaskManager sub-agent
│   ├── schedule_agent.py    # ScheduleManager sub-agent
│   ├── knowledge_agent.py   # KnowledgeAgent sub-agent
│   ├── tools.py             # MCP Toolbox loader
│   └── prompts.py           # Agent instructions
├── app.py                   # FastAPI application
├── run_app.py               # Async uvicorn launcher
├── tools.yaml               # MCP Toolbox config (AlloyDB sources & SQL tools)
├── scripts/
│   ├── init_db.py           # DB schema creation
│   └── deploy.sh            # Cloud Run deploy script
├── requirements.txt
├── Dockerfile
├── .env.example
└── .gitignore
```

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Runtime |
| Google Cloud SDK (`gcloud`) | Auth, deployment |
| AlloyDB (or PostgreSQL) instance | Data store |
| MCP Toolbox binary | Tool middleware |
| Gemini API key _or_ Vertex AI | LLM backend |

---

## Commands – Step by Step

### 1. Clone & set up environment

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

```bash
cp .env.example .env
# Edit .env with your values:
#   GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT, ALLOYDB_* credentials, TOOLBOX_URL
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 4. Set up AlloyDB

```bash
# Create cluster (one-time)
gcloud alloydb clusters create prowork-cluster \
  --password=YOUR_PASSWORD \
  --network=default \
  --region=us-central1

# Create primary instance
gcloud alloydb instances create prowork-primary \
  --instance-type=PRIMARY \
  --cpu-count=2 \
  --region=us-central1 \
  --cluster=prowork-cluster
```

Or use a local PostgreSQL for development:
```bash
docker run -d --name prowork-pg \
  -e POSTGRES_DB=prowork \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:15
```

### 5. Initialise database tables

```bash
python scripts/init_db.py
```

### 6. Download & run MCP Toolbox

```bash
# Download the binary (Linux example)
export VERSION=0.8.0
curl -O https://storage.googleapis.com/genai-toolbox/v${VERSION}/linux/amd64/toolbox
chmod +x toolbox

# Start Toolbox (reads tools.yaml)
./toolbox --tools_file tools.yaml
```

### 7. Run locally

```bash
# Option A – FastAPI dev server
python app.py

# Option B – ADK CLI (interactive agent REPL)
adk run prowork_agents

# Option C – ADK web UI
adk web prowork_agents
```

API docs: http://localhost:8080/docs

### 8. Deploy to Cloud Run

```bash
# Set required env vars
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_API_KEY=your-key
export TOOLBOX_URL=https://your-toolbox-cloudrun-url

# Deploy
bash scripts/deploy.sh
```

The script will print the Cloud Run service URL at the end:
```
✅  Deployment complete.
▸ Service URL:
https://prowork-ai-xxxxxxxxxx-uc.a.run.app
```

### 9. Verify the deployment

```bash
# Health check
curl https://prowork-ai-xxxxxxxxxx-uc.a.run.app/health

# Chat
curl -X POST https://prowork-ai-xxxxxxxxxx-uc.a.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List my tasks"}'
```

---

## Deploy MCP Toolbox to Cloud Run (optional)

If you want the Toolbox server itself on Cloud Run:

```bash
gcloud run deploy prowork-toolbox \
  --source=. \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}"
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
