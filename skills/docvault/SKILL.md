---
name: docvault
description: >
  DocVault is the NexusLayer document data room — projects, folders, uploaded
  documents (PDF/DOCX/XLSX/images) and shareable links. Use this skill when the
  user mentions DocVault, a document vault or data room, project documents, or
  wants to upload, find, download or share a file on nexuslayer.eu.
---

# DocVault — Document Data Room

**Dashboard:** https://docs.nexuslayer.eu
**API base:** https://docs.nexuslayer.eu/api
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Projects

Listing projects is also the cheapest way to confirm your token works — an invalid
token returns an error rather than an array.

```bash
# list
curl https://docs.nexuslayer.eu/api/projects \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# create
curl -X POST https://docs.nexuslayer.eu/api/projects \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme due diligence"}'

# get / update / delete
curl https://docs.nexuslayer.eu/api/projects/{id}      -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
curl -X PATCH  https://docs.nexuslayer.eu/api/projects/{id} -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" -H "Content-Type: application/json" -d '{"name":"..."}'
curl -X DELETE https://docs.nexuslayer.eu/api/projects/{id} -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## Folders (inside a project)

```bash
curl -X POST   https://docs.nexuslayer.eu/api/projects/{id}/folders -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" -H "Content-Type: application/json" -d '{"name":"Contracts"}'
curl -X PATCH  https://docs.nexuslayer.eu/api/projects/{id}/folders/{folderId} -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" -H "Content-Type: application/json" -d '{"name":"..."}'
curl -X DELETE https://docs.nexuslayer.eu/api/projects/{id}/folders/{folderId} -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
```

## Documents

```bash
# upload (multipart)
curl -X POST https://docs.nexuslayer.eu/api/projects/{projectId}/documents \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -F "file=@./contract.pdf"

# metadata / rename-move / delete
curl https://docs.nexuslayer.eu/api/documents/{id}          -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"
curl -X PATCH  https://docs.nexuslayer.eu/api/documents/{id} -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" -H "Content-Type: application/json" -d '{"name":"..."}'
curl -X DELETE https://docs.nexuslayer.eu/api/documents/{id} -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}"

# download the file itself
curl https://docs.nexuslayer.eu/api/documents/{id}/download \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" -OJ
```

---

## Notes

- Uploads are multipart — do not JSON-encode a file body.
- DocVault holds **binary documents**; MarkVault holds authored markdown; BrainVault
  holds RAG-queryable notes. Pick the right one before writing.

**Problems?** Email admin@nexuslayer.eu.
