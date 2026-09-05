---
name: forgeops
description: >
  ForgeOps is the NexusLayer infrastructure automation platform. Use this skill when
  the user says "list nodes", "run playbook", "run forge", "check drift", "ssh node",
  "infrastructure", "forgeops", or any request to manage servers, run playbooks, detect
  configuration drift, or access the encrypted secrets vault on ForgeOps.
---

# ForgeOps Skill

Interact with the ForgeOps infrastructure automation platform — SSH node registry, reusable playbooks, drift detection, encrypted vault, and audit trail.

**Frontend:** https://forgeops.nexuslayer.eu  
**API base:** https://forgeops.nexuslayer.eu/api/v1  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## Nodes (SSH Servers)

### List All Nodes
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/nodes | python3 -m json.tool
```

### Register a Node
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-01",
    "hostname": "10.0.0.10",
    "port": 22,
    "osType": "LINUX",
    "connectionType": "SSH_KEY",
    "description": "Production web server"
  }' \
  https://forgeops.nexuslayer.eu/api/v1/nodes | python3 -m json.tool
```

### Ping / Test Connection
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/nodes/NODE_ID/ping | python3 -m json.tool
```

---

## Forges (Playbooks)

### List All Forges
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/forges | python3 -m json.tool
```

### Run a Forge
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"targetNodeIds": ["NODE_UUID_1", "NODE_UUID_2"]}' \
  https://forgeops.nexuslayer.eu/api/v1/forges/FORGE_ID/runs | python3 -m json.tool
```

---

## Runs

### List Runs (for one forge)
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/forges/FORGE_ID/runs | python3 -m json.tool
```

### Get Run Output
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/runs/RUN_ID | python3 -m json.tool
```

---

## Drift Detection

### List Drift Reports
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/forges/FORGE_ID/drift | python3 -m json.tool
```

---

## Vault (Secrets)

### List Secret Names
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/vault/secrets | python3 -m json.tool
```

---

## Audit Log

```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/audit/events | python3 -m json.tool
```

---

## Dashboard SSO Link
```
https://forgeops.nexuslayer.eu?sso_token={{NEXUSLAYER_TOKEN}}
```

---

## Endpoint reference (verified against production)

| Method | Path |
|---|---|
| GET | `/api/v1/health` |
| GET/POST | `/api/v1/nodes` · `/api/v1/nodes/{id}` · `POST /api/v1/nodes/{id}/ping` |
| GET/POST | `/api/v1/groups` · `/api/v1/groups/{id}/members` · `/api/v1/groups/{id}/variables` |
| GET/POST | `/api/v1/forges` · `/api/v1/forges/{id}` · `/api/v1/forges/{id}/versions` |
| POST | `/api/v1/forges/{id}/validate` · `/api/v1/forges/{id}/bindings` |
| GET/POST | `/api/v1/forges/{forgeId}/runs` — list and start runs for a forge |
| GET | `/api/v1/runs/{runId}` · `/api/v1/runs/{runId}/tasks` · `/api/v1/runs/{runId}/logs` |
| POST | `/api/v1/runs/{runId}/cancel` |
| GET | `/api/v1/forges/{forgeId}/drift` · `POST /api/v1/forges/{forgeId}/drift/check` |
| GET/POST | `/api/v1/vault/secrets` · `GET /api/v1/vault/secrets/{id}/reveal` |
| GET | `/api/v1/audit/events` — ADMIN or OPERATOR role only |

There is **no** top-level `/api/v1/runs` or `/api/v1/drift`; both are nested under a
forge. `/api/v1/users` and `/api/v1/audit/events` require an elevated role and return
403 for a standard account.

**Problems?** Email admin@nexuslayer.eu.
