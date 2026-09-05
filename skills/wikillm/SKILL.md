---
name: wikillm
description: >
  WikiLLM turns a folder of documents into a structured, cross-linked wiki with
  semantic search and a RAG query API. Use this skill when the user mentions WikiLLM
  or WikiForge, wants to turn PDFs/DOCX/XLSX/Markdown into a knowledge base, or wants
  to query a generated wiki.
---

# WikiLLM — Documents to a Living Knowledge Base

**Dashboard:** https://wikillm.nexuslayer.eu
**API base:** https://api.wikillm.nexuslayer.eu/api/v1
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

WikiLLM ingests PDF, DOCX, XLSX, CSV and Markdown, runs them through a multi-stage LLM
pipeline, and publishes a searchable wiki that updates when the source files change.

---

## Projects

```bash
# list
curl https://api.wikillm.nexuslayer.eu/api/v1/projects \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# create
curl -X POST https://api.wikillm.nexuslayer.eu/api/v1/projects \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"name":"platform-docs"}'

# force a full rebuild
curl -X POST https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/rebuild \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## Files

```bash
# upload source documents
curl -X POST https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/files \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -F "file=@./spec.pdf"

# processing status per file
curl "https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/files?status=pending" \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## Wiki content and search

```bash
# generated pages
curl https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/pages \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# one page — format=md|html|json
curl "https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/pages/{pageId}?format=md" \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# semantic search across the wiki
curl -X POST https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/search \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"query":"how does failover work"}'
```

## RAG query (the agent entry point)

```bash
curl -X POST https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/rag \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"question":"what is the retention policy?"}'
# -> {"answer": "...", "sources": [{"filename":..., "wiki_page":..., "relevance":...}]}
```

Prefer the RAG endpoint over reading pages one at a time — it returns an answer with the
source pages cited, which is what you want to ground a response on.

## Pipeline status

```bash
curl https://api.wikillm.nexuslayer.eu/api/v1/projects/{id}/pipeline \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
# files_by_status, progress_pct, active_jobs, eta_seconds
```

---

## Notes

- Ingestion is asynchronous. Poll the pipeline endpoint rather than assuming a freshly
  uploaded file is already searchable.
- A rebuild regenerates pages from source; local edits to generated pages do not survive.

**Problems?** Email admin@nexuslayer.eu.
