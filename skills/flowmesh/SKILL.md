---
name: flowmesh
description: >
  FlowMesh is the NexusLayer visual pipeline builder and execution engine.
  Use this skill when the user says "run pipeline", "trigger flow", "execute pipeline",
  "list pipelines", "create pipeline", "pipeline status", "flowmesh", or any request
  to manage or execute multi-agent workflows.
---

# FlowMesh — Visual Pipeline Orchestration

FlowMesh builds and runs multi-step AI agent pipelines. Define workflows visually or via API, then trigger them on demand, schedule, or webhook.

**Dashboard:** https://flowmesh.nexuslayer.eu  
**API base:** https://api.flowmesh.nexuslayer.eu/api/v1  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## List Pipelines
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.flowmesh.nexuslayer.eu/api/v1/pipelines | python3 -m json.tool
```

## Get Pipeline Details
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.flowmesh.nexuslayer.eu/api/v1/pipelines/PIPELINE_ID | python3 -m json.tool
```

## Trigger a Pipeline
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"payload": {"input": "your data here"}}' \
  https://api.flowmesh.nexuslayer.eu/api/v1/pipelines/PIPELINE_ID/execute | python3 -m json.tool
```

## Check Execution Status
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.flowmesh.nexuslayer.eu/api/v1/executions/EXECUTION_ID | python3 -m json.tool
```

## List Recent Executions
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.flowmesh.nexuslayer.eu/api/v1/executions | python3 -m json.tool
```

## Create a Pipeline (API)
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Pipeline",
    "description": "Optional description",
    "nodes": [],
    "edges": []
  }' \
  https://api.flowmesh.nexuslayer.eu/api/v1/pipelines | python3 -m json.tool
```

---

## Node Types

| Type | Purpose |
|------|---------|
| `AGENT` | Run an AI agent with a prompt |
| `LLM` | Direct LLM call (model + prompt) |
| `CONDITION` | Branch on a boolean expression |
| `TRANSFORM` | Transform data with a script |
| `WEBHOOK` | Call an external HTTP endpoint |
| `MERGE` | Merge parallel branches |
| `NOTIFY` | Send email/Slack notification |
| `DELAY` | Wait N seconds |
