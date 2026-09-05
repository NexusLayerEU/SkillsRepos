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
    "hostname": "192.168.1.100",
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
  https://forgeops.nexuslayer.eu/api/v1/forges/FORGE_ID/run | python3 -m json.tool
```

---

## Runs

### List Runs
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://forgeops.nexuslayer.eu/api/v1/runs | python3 -m json.tool
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
  https://forgeops.nexuslayer.eu/api/v1/drift | python3 -m json.tool
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
