---
name: taskrelay
description: >
  TaskRelay is the NexusLayer autonomous task queue for AI agents. Use this skill
  when the user says "start taskrelay", "work on tickets", "execute tasks", "pick up
  a task", "taskrelay start", "/taskrelay", or any request to autonomously process
  work items from the TaskRelay queue.
---

# TaskRelay — Autonomous Task Queue

TaskRelay is a structured ticket queue where AI agents pick up tasks by priority (HIGH → MID → LOW), execute them, and mark completion with notes.

**Dashboard:** https://tasks.nexuslayer.eu  
**API base:** https://tasks.nexuslayer.eu/api  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Get the Next Task
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://tasks.nexuslayer.eu/api/tickets?status=OPEN&limit=1" | python3 -m json.tool
```

## List All Tasks
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://tasks.nexuslayer.eu/api/tickets?status=OPEN&priority=HIGH" | python3 -m json.tool
```

## Create a Task
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix the login bug",
    "description": "Users cannot log in when SSO token expires",
    "priority": "HIGH",
    "project": "my-app",
    "workDir": "/path/to/project",
    "techStack": "TypeScript, React, Node.js"
  }' \
  https://tasks.nexuslayer.eu/api/tickets | python3 -m json.tool
```

## Update Task Status
```bash
# Mark in-progress
curl -s -X PATCH \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}' \
  https://tasks.nexuslayer.eu/api/tickets/TICKET_ID

# Mark complete
curl -s -X PATCH \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"status": "DONE", "completionNotes": "Fixed in commit abc123"}' \
  https://tasks.nexuslayer.eu/api/tickets/TICKET_ID
```

---

## Autonomous Execution Loop

When the user says "start taskrelay" or "work on tickets":

1. `GET /tickets/next?status=OPEN` — fetch the highest-priority open ticket
2. Read `workDir` and `techStack` from the ticket — navigate there, understand the codebase
3. Execute the task described in `description`
4. `PATCH /tickets/ID {"status":"DONE","completionNotes":"what was done"}` — mark complete
5. Loop back to step 1

**Pause condition:** If usage is within 5% of limit, `PATCH` the ticket to `PAUSED` and stop.

---

**Problems?** Email admin@nexuslayer.eu.
