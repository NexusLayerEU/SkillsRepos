---
name: agentshop
description: >
  AgentShop is the NexusLayer coding-agent platform — pick a specialist agent
  (Python, Java, DevOps, React, SQL and more), deploy it over SSH to a machine you
  registered, and manage its work from a Kanban board with live output streaming.
  Use this skill when the user mentions AgentShop, wants to dispatch a coding task
  to an agent, or wants to register a machine to run agents on.
---

# AgentShop — Coding Agent Platform

**Dashboard:** https://agentshop.nexuslayer.eu
**API base:** https://agentshop.nexuslayer.eu/api
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Agents

```bash
# what specialists are available
curl https://agentshop.nexuslayer.eu/api/agents \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

Each agent carries a system prompt tuned to its speciality — a Python agent reviews and
writes Python idiomatically, a DevOps agent reasons about infrastructure, and so on.

## Machines

Agents run on machines **you** register, over SSH. Nothing executes on NexusLayer
infrastructure.

```bash
curl https://agentshop.nexuslayer.eu/api/machines \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

curl -X POST https://agentshop.nexuslayer.eu/api/machines \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"name":"build-01","host":"10.0.0.9","user":"deploy"}'
```

## Tasks

```bash
# dispatch work to an agent on a machine
curl -X POST https://agentshop.nexuslayer.eu/api/tasks \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "<agent-id>",
    "machineId": "<machine-id>",
    "title": "Add rate limiting to the login endpoint",
    "description": "429 after 5 attempts per minute per IP."
  }'

# poll status
curl https://agentshop.nexuslayer.eu/api/tasks/{id} \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

Task output streams to the Kanban board over WebSocket while the agent works.

## GitHub integration

With GitHub configured under Settings, each task gets its own branch, commits and a pull
request automatically — you review the PR rather than the raw diff.

```bash
curl https://agentshop.nexuslayer.eu/api/settings/github \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

---

## Notes

- Agents act on real machines and real repositories. Scope a task narrowly and review
  the resulting PR before merging.
- Register a machine with a dedicated, least-privilege SSH user — not root.

**Problems?** Email admin@nexuslayer.eu.
