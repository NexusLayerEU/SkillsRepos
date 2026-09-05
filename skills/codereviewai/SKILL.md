---
name: codereviewai
description: >
  CodeReviewAI (AgentReview) is the NexusLayer autonomous code review product — it
  analyses a repository or pull request and reports bugs, security issues and code
  smells with severity levels and fix suggestions. Use this skill when the user asks
  for an AI code review, mentions CodeReviewAI or AgentReview, wants to scan a
  project, or wants to poll for review tasks queued from the web UI.
---

# CodeReviewAI — Autonomous Code Review

**Dashboard:** https://review.nexuslayer.eu
**API base:** https://review.nexuslayer.eu/api/v1
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Submit a project for review

```bash
curl -X POST https://review.nexuslayer.eu/api/v1/reviews \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-service","branch":"main"}'
```

The response carries a review id. The human-readable report is at
`https://review.nexuslayer.eu/app/review/<review-id>`.

## Check review status

```bash
curl https://review.nexuslayer.eu/api/v1/reviews/{id} \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## List reviews

```bash
curl https://review.nexuslayer.eu/api/v1/reviews \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## Findings

Findings carry a severity of `CRITICAL`, `HIGH`, `MEDIUM` or `LOW`, the file and line
they anchor to, an explanation, and a suggested fix. Work `CRITICAL` and `HIGH` first;
treat `LOW` as optional cleanup.

Supported languages include Python, Java, TypeScript, JavaScript, Go, C#, PHP and SQL.

## Response shape

`GET /api/v1/reviews` returns a Spring page:

```json
{"content": [ ... ], "pageable": {"pageNumber":0,"pageSize":20}, "totalElements": 0}
```

Read `content` for the reviews themselves; page with `?page=N&size=M`.

## API keys

Generate a project API key at https://review.nexuslayer.eu/app/settings. Store it in an
environment variable (`AR_API_KEY`) — never commit it to the repository being reviewed.

---

## Notes

- A review runs against a snapshot. Re-run it after pushing fixes rather than assuming
  the old report still applies.
- Findings are advisory. Confirm a finding against the actual code before acting on it.

**Problems?** Email admin@nexuslayer.eu.
