# ProWork AI – Troubleshooting Guide

## 1. ADK: `root_agent is None`

**Error:**
```
root_agent is None
```

**Cause:** ADK loads `agent.py` inside its own uvicorn event loop. If `root_agent` is built with `async` code (e.g., `asyncio.run()`), it detects a running loop and returns `None`.

**Fix:** Build `root_agent` synchronously at module level — no async calls during module load.

---

## 2. ADK: `No agents found`

**Error:**
```
No agents found in prowork_agents
```

**Cause:** Running `adk web prowork_agents` makes ADK scan *inside* the package for sub-folders. It doesn't find any agent packages.

**Fix:** Run `adk web .` from the parent directory so ADK discovers `prowork_agents/` as an agent package.

---

## 3. Gemini: `429 RESOURCE_EXHAUSTED`

**Error:**
```
429 RESOURCE_EXHAUSTED: GenerateContent API rate limit exceeded for model gemini-2.0-flash
```

**Cause:** Free-tier quota for `gemini-2.0-flash` was exhausted.

**Fix:** Switch all agents to `gemini-2.5-flash` model.

---

## 4. ToolboxTool: `'ToolboxTool' object has no attribute 'name'`

**Error:**
```
AttributeError: 'ToolboxTool' object has no attribute 'name'
    task_tools = [t for t in tools if t.name in task_tool_names]
```

**Cause:** In `toolbox-core`, the tool name is stored as `__name__` (Python callable convention), not `.name`.

**Fix:** Use `getattr(t, "__name__", "")` instead of `t.name`:
```python
task_tools = [t for t in tools if getattr(t, "__name__", "") in task_tool_names]
```

---

## 5. Cloud Run: `--clear-base-image` required

**Error:**
```
ERROR: Missing required argument [--clear-base-image]: Base image is not supported for services built from Dockerfile.
```

**Cause:** Earlier deployment used a buildpack-based base image. Switching to Dockerfile requires clearing it.

**Fix:** Add `--clear-base-image` flag to `gcloud run deploy`.

---

## 6. Cloud Run: Container failed to start (port mismatch)

**Error:**
```
The user-provided container failed to start and listen on the port defined by PORT=8080
```

**Cause (case 1):** `adk web` defaults to `host=127.0.0.1` (localhost only). Cloud Run requires `0.0.0.0`.

**Fix:** Set `--host 0.0.0.0` in the Dockerfile CMD:
```dockerfile
CMD ["sh", "-c", "exec adk web --host 0.0.0.0 --port ${PORT:-8080} ."]
```

**Cause (case 2):** App crashed during startup (e.g., import error, DB connection timeout).

**Fix:** Check logs with:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=prowork-ai" \
  --limit 20 --format="value(textPayload)" --freshness=10m
```

---

## 7. Toolbox: YAML parse error (boolean default)

**Error:**
```
unable to parse tool "log_action": cannot unmarshal string into Go struct field Config.Parameters of type bool
> default: "true"
```

**Cause:** In `tools.yaml`, a boolean parameter had `default: "true"` (string). Toolbox expects native YAML boolean.

**Fix:** Use unquoted boolean:
```yaml
- name: success
  type: boolean
  default: true       # NOT "true"
```

---

## 8. Toolbox Cloud Run: VPC egress misconfiguration

**Error:**
```
Deployment failed – container timeout (AlloyDB API calls failing)
```

**Cause:** Using `--vpc-egress all-traffic` routed ALL traffic through VPC, including Google API calls needed by Toolbox internally.

**Fix:** Use `--vpc-egress private-ranges-only` so only private IP traffic (AlloyDB `10.x.x.x`) goes through VPC:
```bash
gcloud run deploy toolbox ... --vpc-egress private-ranges-only
```

---

## 9. Cloud Run: New-style URL DNS resolution failure

**Error:**
```
Could not resolve host: prowork-ai-49987200036.us-central1.run.app
```

**Cause:** New-format Cloud Run URLs (`SERVICE-PROJECT_NUMBER.REGION.run.app`) only have IPv6 AAAA DNS records. Corporate DNS servers that don't support IPv6 resolution fail to resolve them.

**Fix (Option A):** Use the old-format URL which has IPv4 A records:
```
https://prowork-ai-avjm7ayixq-uc.a.run.app
```
Both URLs point to the same service. Find it with:
```bash
gcloud run services describe prowork-ai --region us-central1 \
  --format="value(metadata.annotations['run.googleapis.com/urls'])"
```

**Fix (Option B):** Add to Windows hosts file (requires admin):
```
2600:1900:4240:200::  prowork-ai-49987200036.us-central1.run.app
```

---

## 10. AlloyDB: Table/column not found errors

**Error:**
```
column "priority" does not exist / relation "schedule" does not exist
```

**Cause:** `tools.yaml` SQL queries referenced tables/columns that don't match the actual AlloyDB schema.

**Fix:** Query the actual schema via Toolbox and update `tools.yaml` to match:

| tools.yaml (wrong)       | AlloyDB (actual)            |
|--------------------------|-----------------------------|
| `tasks.priority`         | `tasks.priority_score`      |
| `tasks.due_date`         | `tasks.due_at`              |
| `schedule` table         | `calendar_events` table     |
| `schedule.location`      | `calendar_events.source`    |
| `knowledge_base` table   | `notes_memory` table        |

After updating `tools.yaml`, redeploy Toolbox:
```bash
gcloud secrets versions add tools --data-file=tools.yaml
gcloud run services update toolbox --region=us-central1 --update-secrets="/app/tools.yaml=tools:latest"
```

---

## Quick Reference: Useful Commands

```bash
# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" \
  --limit 20 --format="value(textPayload)" --freshness=10m

# Get service URLs
gcloud run services describe SERVICE_NAME --region us-central1 \
  --format="value(status.url)"

# List revisions
gcloud run revisions list --service SERVICE_NAME --region us-central1 --limit 3

# Update Toolbox secret
gcloud secrets versions add tools --data-file=tools.yaml
gcloud run services update toolbox --region=us-central1 --update-secrets="/app/tools.yaml=tools:latest"

# Set gcloud PATH (Windows PowerShell)
$env:PATH = "C:\Users\simanjali.jena\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin;" + $env:PATH
```
