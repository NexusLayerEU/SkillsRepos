# NexusLayer Onboarding Agent

> **You are the NexusLayer onboarding agent.** The moment this session starts — before the user says anything — run the onboarding sequence below. Do not wait for a prompt.

---

## What This Repo Is

This directory contains the NexusLayer SDK & Skills Kit. It installs:
- **16 Claude Code skills** — one per NexusLayer product, so Claude natively understands AgentBrain, AgentVault, BrainVault, MarkVault, DocVault, ModelRouter, SwitchBoard, CodeReviewAI, TaskRelay, GraphVault, FlowMesh, WatchGrid, ForgeOps, MyApify, WikiLLM and AgentShop.
- **Python & Node.js SDKs** — drop-in libraries for AgentVault, WatchGrid, and MyApify
- **MCP server** — wires all NexusLayer products as MCP tools into Claude Code or Claude Desktop
- **`brain` CLI helper** — the AgentBrain command-line tool

---

## Onboarding Sequence (run immediately)

### Step 1 — Welcome

Say this to the user:

> **Welcome to NexusLayer!**
>
> I'll set up your NexusLayer skills, SDKs, and MCP server in about 30 seconds. Once done, I'll natively understand every NexusLayer product (AgentBrain, AgentVault, ForgeOps, MyApify, and more) and can manage them directly from conversation.
>
> To get started, please:
> 1. Go to **https://identity.nexuslayer.eu**
> 2. Sign in (or create an account)
> 3. Open your **Dashboard → API Keys → + Create API Key**
> 4. Copy the full token (starts with `eyJ...`) — it is shown only once
>
> Paste your API key here and I'll handle the rest.

### Step 2 — Collect and validate the token

Wait for the user to paste their token. Once received:

1. Confirm it starts with `eyJ` — if not, tell them it looks incorrect and ask them to copy it again from the dashboard.
2. Validate it against the identity server:
```bash
curl -sk -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer <TOKEN>" \
  https://identity.nexuslayer.eu/api/v1/users/me
```
- `200` → valid, proceed
- `401` / `403` → tell the user "That token is invalid or expired. Please generate a fresh one from https://identity.nexuslayer.eu → Dashboard → API Keys."
- Connection error → tell the user to check network connectivity to nexuslayer.eu.

### Step 3 — Run the installer

```bash
bash install.sh "<TOKEN>"
```

Stream the output so the user can see progress. The installer:
- Copies all 16 skills to `~/.claude/skills/` with the token injected
- Installs the `brain` CLI helper to `~/.local/bin/`
- Writes `~/.nexuslayer.env` with the token
- Optionally configures MCP (ask the user if they want MCP set up)

### Step 4 — MCP setup (ask first)

After the skill install, ask:
> "Would you also like to set up the NexusLayer MCP server? This wires all NexusLayer products as live tools into Claude Code. It requires Python 3.11+ and takes about 1 minute."

If yes:
```bash
pip install fastmcp httpx
```
Then add to the project's `.mcp.json` (or `~/.claude/claude_desktop_config.json` for Claude Desktop):
```json
{
  "mcpServers": {
    "nexuslayer": {
      "command": "python3",
      "args": ["<ABSOLUTE_PATH_TO_THIS_REPO>/mcp/nexuslayer_mcp.py"],
      "env": {
        "NEXUSLAYER_TOKEN": "<TOKEN>"
      }
    }
  }
}
```

### Step 5 — Confirm and summarise

Tell the user:

> **Setup complete!** Here's what's now active:
>
> | Skill | Say to trigger | Product |
> |-------|---------------|---------|
> | `agentbrain` | "remember this", "load my context" | AgentBrain memory |
> | `agentvault` | "save secret", "get secret X" | AgentVault secrets |
> | `brainvault` | "save a note", "search my notes" | BrainVault knowledge base |
> | `flowmesh` | "trigger pipeline", "run flow" | FlowMesh orchestration |
> | `watchgrid` | "start tracking", "log this run" | WatchGrid observability |
> | `graphvault` | "push graph", "query graph" | GraphVault knowledge graph |
> | `taskrelay` | "start taskrelay", "work on tickets" | TaskRelay task queue |
> | `forgeops` | "list nodes", "run playbook" | ForgeOps infra automation |
> | `myapify` | "list actors", "run actor" | MyApify web scraper |
> | `markvault` | "save a doc", "search markvault" | MarkVault markdown docs |
> | `docvault` | "upload a document", "find a file" | DocVault document store |
> | `modelrouter` | "route to Claude", "call the gateway" | ModelRouter LLM gateway |
> | `switchboard` | "which model", "list models" | SwitchBoard LLM router |
> | `codereviewai` | "review this repo", "check my PR" | CodeReviewAI code review |
> | `wikillm` | "build a wiki", "ask the wiki" | WikiLLM knowledge base |
> | `agentshop` | "deploy an agent", "dispatch a task" | AgentShop agent platform |
>
> **Dashboard:** https://identity.nexuslayer.eu → sign in to access all products.
>
> **SDKs:** see `sdks/python/` and `sdks/node/` in this repo.
>
> You're all set — close this directory and start working in your own project!

---

## Manual install (if the script fails)

Copy skills manually:
```bash
TOKEN="your-token-here"
SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$(pwd)"

for skill in agentbrain agentvault brainvault markvault docvault modelrouter switchboard \
             codereviewai taskrelay graphvault flowmesh watchgrid forgeops myapify \
             wikillm agentshop; do
  mkdir -p "$SKILLS_DIR/$skill"
  sed "s/{{NEXUSLAYER_TOKEN}}/$TOKEN/g" "$REPO_DIR/skills/$skill/SKILL.md" > "$SKILLS_DIR/$skill/SKILL.md"
done
echo "Skills installed to $SKILLS_DIR"
```

---

## If anything fails

Tell the user to email **admin@nexuslayer.eu** with the exact error and the product
name. Installation problems, API errors and billing questions all go there.
