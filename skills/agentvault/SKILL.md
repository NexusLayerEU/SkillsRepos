---
name: agentvault
description: >
  AgentVault is the NexusLayer zero-trust secret store for AI agents.
  Use this skill IMMEDIATELY when the user says "save secret", "store secret",
  "add secret to vault", "load secret", "fetch secret", "get secret from vault",
  "list secrets", "save to AgentVault", or any variation of storing or retrieving
  credentials, API keys, passwords, or tokens.
---

# AgentVault — Zero-Trust Secret Store

AgentVault stores encrypted secrets. Agents authenticate with short-lived vault tokens, request only the secrets they need, and every access is logged.

**Dashboard:** https://vault.nexuslayer.eu  
**API base:** https://api.agentvault.nexuslayer.eu  
**Auth:** NexusLayer SSO JWT `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## List Secrets
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://api.agentvault.nexuslayer.eu/api/v1/secrets | python3 -m json.tool
```

## Create a Secret
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MY_API_KEY",
    "type": "API_KEY",
    "value": "sk-the-actual-value",
    "description": "Optional description"
  }' \
  https://api.agentvault.nexuslayer.eu/api/v1/secrets
```

Secret types: `API_KEY`, `USERNAME_PASSWORD`, `SSH_KEY`, `CERTIFICATE`, `JSON`, `CONNECTION_STRING`

## Fetch a Secret Value (agent flow)

```python
import urllib.request, json

# Step 1: get a short-lived vault token
token_req = urllib.request.Request(
    "https://api.agentvault.nexuslayer.eu/vault/token",
    data=json.dumps({
        "agentId": "YOUR_AGENT_UUID",
        "agentSecret": "av_ag_YOUR_AGENT_SECRET"
    }).encode(),
    headers={"Content-Type": "application/json"}
)
vault_token = json.loads(urllib.request.urlopen(token_req).read())["token"]

# Step 2: fetch the secret
secret_req = urllib.request.Request(
    "https://api.agentvault.nexuslayer.eu/vault/secrets/MY_API_KEY",
    headers={"X-Vault-Token": vault_token}
)
value = json.loads(urllib.request.urlopen(secret_req).read())["value"]
print(value)
```

## Register an Agent (admin)
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "description": "My automation agent"}' \
  https://api.agentvault.nexuslayer.eu/api/v1/agents
```
Save the `agentSecret` from the response — it is shown **once only**.

## Grant Agent Access to a Secret
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"agentIdentityId": "AGENT_UUID", "secretId": "SECRET_UUID"}' \
  https://api.agentvault.nexuslayer.eu/api/v1/policies
```

## Python SDK
```python
# Install: copy sdks/python/agentvault_sdk.py to your project
from agentvault_sdk import AgentVaultClient

with AgentVaultClient("https://vault.nexuslayer.eu", AGENT_ID, AGENT_SECRET) as vault:
    api_key = vault.fetch_secret("OPENAI_API_KEY", run_id="run-001")
```
