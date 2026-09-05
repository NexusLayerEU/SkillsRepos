---
name: agentbrain
description: >
  AgentBrain is the NexusLayer persistent memory system for AI agents.
  Use this skill when the user says "remember", "save to memory", "load my context",
  "what did we work on", "push memory", "add episode", "brain push", "brain context",
  or any request to store or recall information across sessions.
---

# AgentBrain — Persistent AI Memory

AgentBrain is a three-layer memory system: working memory (24h TTL), episodic memory (permanent events), and lessons (hard-won rules promoted to permanent guidance).

**Dashboard:** https://cortex.nexuslayer.eu  
**API base:** https://api.agentbrain.nexuslayer.eu/api  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Quick Commands (use `brain` CLI)

```bash
# Load context for current task
brain context "project keywords"

# Save an episode (finding, decision, work done)
brain push "SESSION: what was done — details" "project,topic"

# Save short-lived working memory (24h TTL)
brain working "reminder note" "reminder"

# List recent episodes
brain memories

# List all lessons
brain lessons
```

---

## Direct API

The API base is `/api` — there is no `/api/v1`.

> **`tags` is a comma-separated string, not an array.** The write endpoints bind the
> body as a string-to-string map, so `"tags": ["a","b"]` is rejected. Send
> `"tags": "a,b"`.

### Load context (episodes + lessons)
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://api.agentbrain.nexuslayer.eu/api/context?q=PROJECT_NAME"
```

### Save an episode
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"content":"What happened this session","tags":"project,session"}' \
  https://api.agentbrain.nexuslayer.eu/api/memory/episodic
```

### Save working memory (24h TTL)
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"content":"Short reminder","tags":"reminder"}' \
  https://api.agentbrain.nexuslayer.eu/api/memory/working
```

### List recent episodes
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://api.agentbrain.nexuslayer.eu/api/memory/episodic?page=0&size=10"
```

### List lessons
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://api.agentbrain.nexuslayer.eu/api/lessons?status=ACCEPTED"
```

A lesson's text is in `claim`, with the rule to apply in `rationale`.

### Other endpoints
`/api/stats`, `/api/memory/search`, `/api/dream`, `/api/claude`, `/api/backup`.

---

## Session Protocol

**Session start:** `brain context "project task-keywords"` — read episodes and lessons.  
**During session:** `brain push "finding or decision" "project,topic"` after significant work.  
**Session end:** `brain push "SESSION: summary — next: what's next" "project,session-summary"`

---

**Problems?** Email admin@nexuslayer.eu.
