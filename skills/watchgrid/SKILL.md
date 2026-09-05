---
name: watchgrid
description: >
  WatchGrid is the NexusLayer observability platform for AI agents.
  Use this skill when the user says "start tracking", "log this run", "watch my agent",
  "track LLM costs", "watchgrid", "list runs", "agent observability", or any request
  to monitor or record AI agent activity, costs, or errors.
---

# WatchGrid — AI Agent Observability

WatchGrid tracks every agent session: LLM calls, tool invocations, costs, errors, and run outcomes — in real time.

**Dashboard:** https://watchgrid.nexuslayer.eu  
**API base:** https://api.watchgrid.nexuslayer.eu/api/v1  
**Ingest endpoint:** https://watchgrid.nexuslayer.eu/ingest/events  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## List Runs
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.watchgrid.nexuslayer.eu/api/v1/runs | python3 -m json.tool
```

## Get Run Details
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.watchgrid.nexuslayer.eu/api/v1/runs/RUN_ID | python3 -m json.tool
```

## Ingest Events (SDK key required)

Get your SDK key from: https://watchgrid.nexuslayer.eu → Settings → SDK Keys

```bash
SDK_KEY="wg_sdk_YOUR_KEY_HERE"

# Start a run
curl -s -X POST \
  -H "X-SDK-Key: $SDK_KEY" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"type":"RUN_START","runId":"run-001","timestamp":"2026-01-01T00:00:00Z"}]}' \
  https://watchgrid.nexuslayer.eu/ingest/events

# Log an LLM call
curl -s -X POST \
  -H "X-SDK-Key: $SDK_KEY" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"type":"LLM_CALL","runId":"run-001","model":"claude-sonnet-4-6","inputTokens":400,"outputTokens":100,"costUsd":0.003,"latencyMs":1200,"timestamp":"2026-01-01T00:00:01Z"}]}' \
  https://watchgrid.nexuslayer.eu/ingest/events

# End a run
curl -s -X POST \
  -H "X-SDK-Key: $SDK_KEY" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"type":"RUN_END","runId":"run-001","status":"SUCCESS","timestamp":"2026-01-01T00:00:10Z"}]}' \
  https://watchgrid.nexuslayer.eu/ingest/events
```

## Python SDK
```python
# Install: copy sdks/python/watchgrid_sdk.py to your project
from watchgrid_sdk import WatchGridClient

wg = WatchGridClient("https://watchgrid.nexuslayer.eu", "wg_sdk_YOUR_KEY")

with wg.run("my-run") as run:
    run.log_llm_call("claude-sonnet-4-6", 400, 100, 0.003, 1200)
    run.log_tool_call("web_search", 320)
```

## Event Types

| Event | Required fields |
|-------|----------------|
| `RUN_START` | `runId`, `timestamp` |
| `RUN_END` | `runId`, `status` (`SUCCESS`/`FAILURE`/`TIMEOUT`), `timestamp` |
| `LLM_CALL` | `runId`, `model`, `inputTokens`, `outputTokens`, `costUsd`, `latencyMs`, `timestamp` |
| `TOOL_CALL` | `runId`, `toolName`, `durationMs`, `timestamp` |
| `ERROR` | `runId`, `message`, `timestamp` |
