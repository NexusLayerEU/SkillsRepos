---
name: brainvault
description: >
  VaultBrain (BrainVault) is the NexusLayer personal knowledge base — a notes and
  document store with semantic search. Use this skill when the user says "save a note",
  "add to knowledge base", "search my notes", "find in brainvault", "store this finding",
  "save to brainvault", "recall", or any variation of saving or searching personal notes.
---

# VaultBrain — Personal Knowledge Base

VaultBrain stores notes, findings, and documents with semantic search. Tag everything with `AINotes` for agent accessibility.

**Dashboard:** https://notes.nexuslayer.eu  
**API base:** https://api.brainvault.nexuslayer.eu/v1  
**Auth:** NexusLayer SSO JWT (see below)

---

## Authentication

VaultBrain uses a short-lived HMAC-SHA256 token generated from your email and the shared SSO secret. Use this Python snippet:

```python
import urllib.request, json, hmac, hashlib, base64, time, os

SECRET  = b'nexuslayer-shared-sso-secret-change-in-production-64chars!!'
EMAIL   = "YOUR_EMAIL@example.com"  # replace with your NexusLayer account email

header  = base64.urlsafe_b64encode(json.dumps({'alg':'HS256','typ':'JWT'}).encode()).rstrip(b'=').decode()
payload = base64.urlsafe_b64encode(json.dumps({
    'sub': EMAIL, 'email': EMAIL, 'name': EMAIL,
    'iat': int(time.time()), 'exp': int(time.time()) + 3600
}).encode()).rstrip(b'=').decode()
sig     = base64.urlsafe_b64encode(
    hmac.new(SECRET, f'{header}.{payload}'.encode(), hashlib.sha256).digest()
).rstrip(b'=').decode()
TOKEN   = f'{header}.{payload}.{sig}'
```

Or simply use your NexusLayer SSO token: `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Save a Note
```python
body = json.dumps({
    "title": "Note title",
    "content": "Markdown content here",
    "tags": ["AINotes", "project-name", "topic"]
}).encode()
req = urllib.request.Request(
    "https://api.brainvault.nexuslayer.eu/v1/notes",
    data=body,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    d = json.loads(resp.read())
    print(f"Saved — ID: {d['id']} | {d['title']}")
```

**Always tag with `"AINotes"`** plus project/topic tags.

## Search Notes
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://api.brainvault.nexuslayer.eu/v1/notes?search=keyword&tag=AINotes" | python3 -m json.tool
```

## List All Notes
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.brainvault.nexuslayer.eu/v1/notes | python3 -m json.tool
```

## Get a Note by ID
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.brainvault.nexuslayer.eu/v1/notes/NOTE_ID | python3 -m json.tool
```
