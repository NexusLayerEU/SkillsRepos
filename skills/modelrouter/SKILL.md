---
name: modelrouter
description: >
  ModelRouter is the NexusLayer Anthropic-compatible LLM gateway — it routes
  /v1/messages calls to Claude, Gemini, Ollama or NVIDIA behind one endpoint, with
  unified cost and token tracking. Use this skill when the user mentions ModelRouter,
  wants an Anthropic-SDK-compatible endpoint, or wants to switch LLM providers
  without changing code.
---

# ModelRouter — Anthropic-Compatible LLM Gateway

**Dashboard:** https://router.nexuslayer.eu (also https://gateway.nexuslayer.eu)
**API base:** https://api.router.nexuslayer.eu
**Auth:** `x-api-key: {{NEXUSLAYER_TOKEN}}`

> ModelRouter mirrors the **Anthropic** wire format, so it authenticates with an
> `x-api-key` header — **not** `Authorization: Bearer`. Sending a Bearer token
> returns 403.

---

## Health

```bash
curl -s https://api.router.nexuslayer.eu/v1/health
# {"status":"ok","service":"ModelRouter"}
```

No auth required — use it to tell "gateway down" apart from "my key is wrong".

## Messages

```bash
curl -s https://api.router.nexuslayer.eu/v1/messages \
  -H "x-api-key: {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-opus-4-8",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Say hi"}]
  }'
```

## Python (Anthropic SDK)

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://api.router.nexuslayer.eu",
    api_key=NEXUSLAYER_TOKEN,   # sent as x-api-key by the SDK
)
msg = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Say hi"}],
)
print(msg.content[0].text)
```

## Choosing the provider

Which upstream serves a request is configured in the dashboard at
https://router.nexuslayer.eu, not per request. Switching provider is a dashboard
change rather than a code change. Provider API keys live in the router config and are
never forwarded upstream from your request.

---

## Troubleshooting

| Response | Meaning |
|---|---|
| `403` | You sent `Authorization: Bearer`. Use `x-api-key` instead. |
| `502` with `"Provider error: ... HTTP 4xx"` | The gateway is up but the **configured upstream provider** rejected the call — expired provider key or a retired model. Fix it in the dashboard under Providers. |
| `000` / timeout | Wrong host. The API lives on `api.router.nexuslayer.eu`; `router.nexuslayer.eu` serves the dashboard. |

Only `/v1/messages` and `/v1/health` exist. There is no `/v1/models` and no
`/v1/provider` endpoint.

ModelRouter has **no embeddings endpoint** — use SwitchBoard for embeddings.

**Problems?** Email admin@nexuslayer.eu.
