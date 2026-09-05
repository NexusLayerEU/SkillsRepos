---
name: markvault
description: >
  MarkVault is the NexusLayer markdown document store — tag-organised docs with
  title search, Mermaid diagrams and PDF/DOCX export. Use this skill when the user
  mentions MarkVault, wants to push, list, search, update or delete a markdown
  document, or asks where a runbook or spec lives on nexuslayer.eu.
---

# MarkVault — Markdown Document Store

**Dashboard:** https://mark.nexuslayer.eu (also https://markvault.nexuslayer.eu — same backend)
**API base:** https://mark.nexuslayer.eu/v1
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Current user

```bash
curl https://mark.nexuslayer.eu/v1/user/me \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## List documents

```bash
# all docs (metadata only, no content)
curl "https://mark.nexuslayer.eu/v1/docs" \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# q filters on TITLE only, case-insensitive substring — it is not full-text
curl "https://mark.nexuslayer.eu/v1/docs?q=deployment" \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# tags is comma-separated and matches docs overlapping ANY listed tag
curl "https://mark.nexuslayer.eu/v1/docs?tags=infra,runbook" \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## Get one document (includes content)

```bash
curl https://mark.nexuslayer.eu/v1/docs/{id} \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## List all tags in use

```bash
curl https://mark.nexuslayer.eu/v1/docs/tags \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
# -> ["infra", "runbook", ...] distinct, alphabetical
```

## Create a document

```bash
curl -X POST https://mark.nexuslayer.eu/v1/docs \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Deploy runbook","content":"# Deploy\n\n1. ...","tags":["infra","runbook"]}'
```

`title` and `content` are required (400 if missing). Returns 201 with the full row.
`pushed_by` is set server-side from the JWT — do not send it.

## Update a document (partial)

```bash
curl -X PUT https://mark.nexuslayer.eu/v1/docs/{id} \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"content":"# Deploy (revised)\n..."}'
```

Only `title`, `content` and `tags` are updatable; omitted fields keep their existing
value. `updated_at` is bumped automatically. 404 if the id does not exist.

## Delete a document

```bash
curl -X DELETE https://mark.nexuslayer.eu/v1/docs/{id} \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

---

## Notes

- Fence a block as ```mermaid and it renders as a diagram in the UI and in exports.
- MarkVault is **not** BrainVault. MarkVault stores authored markdown documents;
  BrainVault stores vector-indexed notes you query with RAG. Different products.

**Problems?** Email admin@nexuslayer.eu.
