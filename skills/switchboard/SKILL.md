---
name: switchboard
description: >
  SwitchBoard is the NexusLayer OpenAI-compatible LLM router — one endpoint and one
  key in front of Claude, Gemini, GPT, NVIDIA and local models, selected by a
  provider-prefixed model ID. Use this skill whenever a project needs an LLM
  endpoint or model ID, when the user mentions SwitchBoard, or when choosing or
  changing which model an application calls.
---

# SwitchBoard — OpenAI-Compatible LLM Router

**Dashboard:** https://switchboard.nexuslayer.eu
**API base:** https://switchboard.nexuslayer.eu/v1
**Auth:** `Authorization: Bearer <SWITCHBOARD_API_KEY>`

Any OpenAI SDK works unmodified — change the base URL and the model ID, nothing else.

> **SwitchBoard uses its own API keys, not your NexusLayer SSO token.** Keys look like
> `sk-...` and are generated in the SwitchBoard dashboard. The NexusLayer JWT signs you
> into the dashboard but is rejected by the API with
> `{"error":"API key required for remote API access"}`.
>
> Sign in at https://switchboard.nexuslayer.eu with your NexusLayer account, create a
> key, and put it in `SWITCHBOARD_API_KEY`. Keep it out of source control.

---

## Model IDs are provider-prefixed

The prefix selects the upstream route:

| Prefix | Upstream | Use for |
|---|---|---|
| `cc/` | Claude | Default. Best reasoning and coding quality. |
| `ag/` | Gemini | Fast, cheap, long context. |
| `gh/` | GPT | Alternate frontier route. |
| `nvidia/` | NVIDIA Build | Open-weight models. Higher latency — avoid when latency matters. |
| `local/` | Ollama / vLLM | On-prem and offline work. |

List exactly what is available right now rather than guessing:

```bash
curl -s https://switchboard.nexuslayer.eu/v1/models \
  -H "Authorization: Bearer $SWITCHBOARD_API_KEY" | jq '.data[].id'
```

## Chat completions

```bash
curl -s https://switchboard.nexuslayer.eu/v1/chat/completions \
  -H "Authorization: Bearer $SWITCHBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cc/claude-opus-4-8",
    "messages": [{"role": "user", "content": "Say hi"}]
  }'
```

## Python (OpenAI SDK)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://switchboard.nexuslayer.eu/v1",
    api_key=os.environ["SWITCHBOARD_API_KEY"],
)
resp = client.chat.completions.create(
    model="cc/claude-opus-4-8",
    messages=[{"role": "user", "content": "Say hi"}],
)
print(resp.choices[0].message.content)
```

## Wiring an application

```bash
LLM_BASE_URL=https://switchboard.nexuslayer.eu/v1
LLM_API_KEY=<your SwitchBoard sk-... key>
LLM_MODEL=cc/claude-opus-4-8
```

Changing provider then means editing `LLM_MODEL`, not editing code.

## Embeddings

Embeddings go through the same endpoint and the same key. Asymmetric embedding models
distinguish query text from document text — pass the correct input type when the model
requires it, or retrieval quality silently degrades.

---

## Notes

- Always pin an explicit model ID. Never rely on an implicit default.
- Call `/v1/models` before hardcoding an ID; the catalogue changes.
- SwitchBoard and ModelRouter are both gateways: SwitchBoard is OpenAI-compatible,
  ModelRouter is Anthropic-compatible. Pick the one that matches your SDK.

**Problems?** Email admin@nexuslayer.eu.
