# NexusLayer SDK & Skills Kit

One-command onboarding for Claude Code. Installs all NexusLayer skills, SDKs, and the MCP server — fully configured with your API key.

**Get your API key:** https://identity.nexuslayer.eu → Profile → API Key

---

## Quick Install

```bash
git clone https://github.com/Thomasdimakopoulos/NextLayer.git
cd NextLayer/SDKSKILLSREPO
bash install.sh
```

The installer will ask for your NexusLayer API key, validate it, and set everything up.

---

## What Gets Installed

| Component | Location | Description |
|-----------|----------|-------------|
| **16 Skills** | `~/.claude/skills/` | Claude Code natively understands every NexusLayer product |
| **Python SDKs** | `~/.nexuslayer/sdks/python/` | AgentVault, WatchGrid, MyApify clients |
| **Node.js SDKs** | `~/.nexuslayer/sdks/node/` | AgentVault, WatchGrid, MyApify clients |
| **`brain` CLI** | `~/.local/bin/brain` | AgentBrain memory management from terminal |
| **Env file** | `~/.nexuslayer.env` | All service URLs + your token |

---

## Install with Claude Code (Recommended)

```bash
git clone https://github.com/Thomasdimakopoulos/NextLayer.git
cd NextLayer/SDKSKILLSREPO
claude
```

Claude Code reads `CLAUDE.md` automatically and walks you through the full setup interactively — including optional MCP server configuration.

---

## Manual Install (no Claude Code)

```bash
bash install.sh "YOUR_TOKEN_HERE"
```

---

## MCP Server

The MCP server wires all NexusLayer products as live tools into Claude Code or Claude Desktop.

**Setup:**
```bash
pip install fastmcp httpx
```

Add to your project's `.mcp.json`:
```json
{
  "mcpServers": {
    "nexuslayer": {
      "command": "python3",
      "args": ["/path/to/SDKSKILLSREPO/mcp/nexuslayer_mcp.py"],
      "env": {
        "NEXUSLAYER_TOKEN": "YOUR_TOKEN_HERE"
      }
    }
  }
}
```

---

## Skills Reference

After install, these skills are active in every Claude Code session:

| Skill | Say to trigger |
|-------|---------------|
| `agentbrain` | "remember this", "load my context", "brain push" |
| `agentvault` | "save secret", "get secret X", "list secrets" |
| `brainvault` | "save a note", "search my notes", "find in knowledge base" |
| `flowmesh` | "trigger pipeline", "run flow", "list pipelines" |
| `watchgrid` | "start tracking", "log this run", "list runs" |
| `graphvault` | "push graph", "query graph", "list graphs" |
| `taskrelay` | "start taskrelay", "work on tickets", "next task" |
| `forgeops` | "list nodes", "run playbook", "check drift" |
| `myapify` | "list actors", "run actor", "get dataset" |
| `markvault` | "save a doc", "list docs", "search markvault" |
| `docvault` | "upload a document", "search documents", "share a file" |
| `modelrouter` | "route this to Claude", "which provider is active" |
| `switchboard` | "which model should I use", "list models", "call GPT" |
| `codereviewai` | "review this repo", "check my PR", "find bugs" |
| `wikillm` | "build a wiki", "ask the wiki", "search the knowledge base" |
| `agentshop` | "deploy an agent", "dispatch a coding task", "list machines" |

---

## Python SDK Usage

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.nexuslayer/sdks/python"))

# AgentVault
from agentvault_sdk import AgentVaultClient
with AgentVaultClient("https://vault.nexuslayer.eu", AGENT_ID, AGENT_SECRET) as vault:
    api_key = vault.fetch_secret("OPENAI_API_KEY")

# WatchGrid
from watchgrid_sdk import WatchGridClient
wg = WatchGridClient("https://watchgrid.nexuslayer.eu", "wg_sdk_YOUR_KEY")
with wg.run() as run:
    run.log_llm_call("claude-sonnet-4-6", 400, 100, 0.003, 1200)
```

---

## Node.js SDK Usage

```javascript
const { AgentVaultClient } = require("~/.nexuslayer/sdks/node/agentvault");
const vault = new AgentVaultClient("https://vault.nexuslayer.eu", agentId, agentSecret);
const apiKey = await vault.fetchSecret("OPENAI_API_KEY");
```

---

## Products

| Product | URL | Description |
|---------|-----|-------------|
| Identity / SSO | https://identity.nexuslayer.eu | Sign in, get API key, manage profile |
| AgentBrain | https://cortex.nexuslayer.eu | Persistent AI memory |
| AgentVault | https://vault.nexuslayer.eu | Zero-trust secret store |
| BrainVault | https://notes.nexuslayer.eu | Personal knowledge base with RAG |
| FlowMesh | https://flowmesh.nexuslayer.eu | Visual pipeline orchestration |
| WatchGrid | https://watchgrid.nexuslayer.eu | AI agent observability |
| GraphVault | https://graph.nexuslayer.eu | Knowledge graph store |
| TaskRelay | https://tasks.nexuslayer.eu | Autonomous task queue |
| ForgeOps | https://forgeops.nexuslayer.eu | Infrastructure automation |
| MyApify | https://myapify.nexuslayer.eu | Self-hosted web scraper |
| ModelRouter | https://router.nexuslayer.eu | Anthropic-compatible LLM gateway |
| SwitchBoard | https://switchboard.nexuslayer.eu | OpenAI-compatible LLM router |
| MarkVault | https://mark.nexuslayer.eu | Markdown document store |
| DocVault | https://docs.nexuslayer.eu | Document data room |
| CodeReviewAI | https://review.nexuslayer.eu | Autonomous code review |
| WikiLLM | https://wikillm.nexuslayer.eu | Documents to a searchable wiki |
| AgentShop | https://agentshop.nexuslayer.eu | Deploy coding agents to your machines |
| WatermarkRemover | https://nexuslayer.eu/watermark/ | Remove watermarks from images |

---

## Support

Something not working? Email **admin@nexuslayer.eu** with the product name and the
exact error you saw. Installation problems, API errors, billing and trial questions,
and bug reports all go to the same address.
