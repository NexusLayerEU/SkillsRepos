"""
NexusLayer Platform — MCP Server
================================
Exposes all NexusLayer products as MCP tools consumable by any
MCP-compatible agent: Claude Code CLI, Claude Desktop, custom agents.

Setup:
    pip install fastmcp httpx
    export NEXUSLAYER_TOKEN="eyJhbG..."   # from https://identity.nexuslayer.eu

Claude Code wiring (.mcp.json in project root):
    {
      "mcpServers": {
        "nexuslayer": {
          "command": "python3",
          "args": ["/path/to/nexuslayer_mcp.py"],
          "env": { "NEXUSLAYER_TOKEN": "eyJhbG..." }
        }
      }
    }

Or source ~/.nexuslayer.env before starting Claude Code.
"""

import os
import json
import httpx
from fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────

TOKEN = os.environ.get("NEXUSLAYER_TOKEN", "")

SERVICES = {
    "agentbrain": os.environ.get("AGENTBRAIN_URL",  "https://cortex.nexuslayer.eu"),
    "agentvault": os.environ.get("AGENTVAULT_URL",  "https://vault.nexuslayer.eu"),
    "brainvault":  os.environ.get("BRAINVAULT_URL",  "https://notes.nexuslayer.eu"),
    "flowmesh":    os.environ.get("FLOWMESH_URL",    "https://flowmesh.nexuslayer.eu"),
    "watchgrid":   os.environ.get("WATCHGRID_URL",   "https://watchgrid.nexuslayer.eu"),
    "graphvault":  os.environ.get("GRAPHVAULT_URL",  "https://graph.nexuslayer.eu"),
    "taskrelay":   os.environ.get("TASKRELAY_URL",   "https://tasks.nexuslayer.eu"),
    "forgeops":    os.environ.get("FORGEOPS_URL",    "https://forgeops.nexuslayer.eu"),
    "myapify":     os.environ.get("MYAPIFY_URL",     "https://myapify.nexuslayer.eu"),
    "modelrouter": os.environ.get("MODELROUTER_URL", "https://router.nexuslayer.eu"),
}

mcp = FastMCP(
    "NexusLayer Platform",
    instructions="""
You have access to all NexusLayer products via these tools. Use them proactively.

Products:
- agentbrain_*    → Persistent AI memory (episodes, lessons, working memory)
- agentvault_*    → Zero-trust secret store
- brainvault_*    → Personal knowledge base (notes, semantic search)
- flowmesh_*      → Visual pipeline orchestration
- watchgrid_*     → AI agent observability (runs, costs, errors)
- graphvault_*    → Knowledge graph store
- taskrelay_*     → Autonomous task queue
- forgeops_*      → Infrastructure automation (SSH nodes, playbooks, drift)
- myapify_*       → Self-hosted web scraper (actors, datasets, schedules)
- modelrouter_*   → LLM gateway (unified chat across providers)
""",
)

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def _get(url: str) -> dict:
    r = httpx.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(url: str, payload: dict) -> dict:
    r = httpx.post(url, json=payload, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


# ── AgentBrain ────────────────────────────────────────────────────────────────

@mcp.tool()
def agentbrain_get_context(keywords: str, limit: int = 5) -> dict:
    """Load memory context (episodes + lessons) matching keywords."""
    base = SERVICES["agentbrain"]
    return _get(f"{base}/api/v1/context?keywords={keywords}&limit={limit}")


@mcp.tool()
def agentbrain_add_episode(content: str, tags: list[str] = None, source: str = "mcp") -> dict:
    """Save a permanent episode to episodic memory."""
    base = SERVICES["agentbrain"]
    return _post(f"{base}/api/v1/episodes", {"content": content, "tags": tags or [], "source": source})


@mcp.tool()
def agentbrain_add_working(content: str, tags: list[str] = None, ttl_hours: int = 24) -> dict:
    """Save a short-lived working memory entry (auto-expires)."""
    base = SERVICES["agentbrain"]
    return _post(f"{base}/api/v1/working", {"content": content, "tags": tags or [], "ttlHours": ttl_hours})


@mcp.tool()
def agentbrain_get_lessons() -> dict:
    """List all accepted and staged lessons."""
    return _get(f"{SERVICES['agentbrain']}/api/v1/lessons")


# ── AgentVault ────────────────────────────────────────────────────────────────

@mcp.tool()
def agentvault_list_secrets() -> dict:
    """List all secrets in AgentVault (names and types only, no values)."""
    return _get(f"{SERVICES['agentvault']}/api/v1/secrets")


@mcp.tool()
def agentvault_create_secret(name: str, secret_type: str, value: str, description: str = "") -> dict:
    """Create a new encrypted secret. Types: API_KEY, USERNAME_PASSWORD, SSH_KEY, JSON, CONNECTION_STRING."""
    return _post(f"{SERVICES['agentvault']}/api/v1/secrets", {
        "name": name, "type": secret_type, "value": value, "description": description
    })


# ── BrainVault ────────────────────────────────────────────────────────────────

@mcp.tool()
def brainvault_create_note(title: str, content: str, tags: list[str] = None) -> dict:
    """Save a note to the personal knowledge base. Always include 'AINotes' in tags."""
    all_tags = list(set(["AINotes"] + (tags or [])))
    return _post(f"{SERVICES['brainvault']}/v1/notes", {"title": title, "content": content, "tags": all_tags})


@mcp.tool()
def brainvault_search(query: str, limit: int = 10) -> dict:
    """Search notes by keyword."""
    return _get(f"{SERVICES['brainvault']}/v1/notes?search={query}&limit={limit}")


# ── FlowMesh ──────────────────────────────────────────────────────────────────

@mcp.tool()
def flowmesh_list_pipelines() -> dict:
    """List all FlowMesh pipelines."""
    return _get(f"{SERVICES['flowmesh']}/api/v1/pipelines")


@mcp.tool()
def flowmesh_trigger_pipeline(pipeline_id: str, payload: dict = None) -> dict:
    """Execute a FlowMesh pipeline with optional input payload."""
    return _post(f"{SERVICES['flowmesh']}/api/v1/pipelines/{pipeline_id}/execute", {"payload": payload or {}})


@mcp.tool()
def flowmesh_execution_status(execution_id: str) -> dict:
    """Get the current status of a pipeline execution."""
    return _get(f"{SERVICES['flowmesh']}/api/v1/executions/{execution_id}")


# ── WatchGrid ─────────────────────────────────────────────────────────────────

@mcp.tool()
def watchgrid_list_runs(limit: int = 20) -> dict:
    """List recent WatchGrid agent runs."""
    return _get(f"{SERVICES['watchgrid']}/api/v1/runs?limit={limit}")


@mcp.tool()
def watchgrid_get_run(run_id: str) -> dict:
    """Get full details of a WatchGrid run including events and cost."""
    return _get(f"{SERVICES['watchgrid']}/api/v1/runs/{run_id}")


# ── GraphVault ────────────────────────────────────────────────────────────────

@mcp.tool()
def graphvault_list_graphs() -> dict:
    """List all stored knowledge graphs in GraphVault."""
    return _get(f"{SERVICES['graphvault']}/api/v1/graphs")


@mcp.tool()
def graphvault_query(project: str, question: str, limit: int = 5) -> dict:
    """Semantic query against a stored knowledge graph."""
    return _post(f"{SERVICES['graphvault']}/api/v1/graphs/{project}/query", {"question": question, "limit": limit})


# ── TaskRelay ─────────────────────────────────────────────────────────────────

@mcp.tool()
def taskrelay_get_next_task(priority: str = None) -> dict:
    """Get the next open task from the TaskRelay queue."""
    base = SERVICES["taskrelay"]
    url = f"{base}/api/v1/tickets/next?status=OPEN"
    if priority:
        url += f"&priority={priority}"
    return _get(url)


@mcp.tool()
def taskrelay_update_task(ticket_id: str, status: str, completion_notes: str = "") -> dict:
    """Update a TaskRelay ticket status. Status: IN_PROGRESS, DONE, PAUSED, FAILED."""
    base = SERVICES["taskrelay"]
    payload = {"status": status}
    if completion_notes:
        payload["completionNotes"] = completion_notes
    r = httpx.patch(f"{base}/api/v1/tickets/{ticket_id}", json=payload, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


# ── ForgeOps ──────────────────────────────────────────────────────────────────

@mcp.tool()
def forgeops_list_nodes() -> dict:
    """List all SSH nodes registered in ForgeOps."""
    return _get(f"{SERVICES['forgeops']}/api/v1/nodes")


@mcp.tool()
def forgeops_list_forges() -> dict:
    """List all ForgeOps playbooks (forges)."""
    return _get(f"{SERVICES['forgeops']}/api/v1/forges")


@mcp.tool()
def forgeops_run_forge(forge_id: str, node_ids: list[str]) -> dict:
    """Execute a ForgeOps playbook against the specified node IDs."""
    return _post(f"{SERVICES['forgeops']}/api/v1/forges/{forge_id}/run", {"targetNodeIds": node_ids})


@mcp.tool()
def forgeops_list_runs() -> dict:
    """List recent ForgeOps execution runs."""
    return _get(f"{SERVICES['forgeops']}/api/v1/runs")


# ── MyApify ───────────────────────────────────────────────────────────────────

@mcp.tool()
def myapify_list_actors() -> dict:
    """List all MyApify actors."""
    return _get(f"{SERVICES['myapify']}/api/actors")


@mcp.tool()
def myapify_run_actor(actor_id: str, input_data: dict = None) -> dict:
    """Run a MyApify actor with optional input."""
    return _post(f"{SERVICES['myapify']}/api/actors/{actor_id}/runs", {"input": input_data or {}})


@mcp.tool()
def myapify_list_runs() -> dict:
    """List recent MyApify actor runs."""
    return _get(f"{SERVICES['myapify']}/api/runs")


@mcp.tool()
def myapify_get_dataset(dataset_id: str, limit: int = 100) -> dict:
    """Get items from a MyApify dataset."""
    return _get(f"{SERVICES['myapify']}/api/datasets/{dataset_id}/items?limit={limit}")


# ── ModelRouter ───────────────────────────────────────────────────────────────

@mcp.tool()
def modelrouter_chat(model: str, messages: list[dict], max_tokens: int = 1024) -> dict:
    """Send a chat request through the NexusLayer ModelRouter (supports Claude, Gemini, Ollama)."""
    return _post(f"{SERVICES['modelrouter']}/api/v1/chat", {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("Warning: NEXUSLAYER_TOKEN not set. Set it in ~/.nexuslayer.env or as an env var.")
        print("  source ~/.nexuslayer.env")
        print("  export NEXUSLAYER_TOKEN=eyJhbG...")
    mcp.run()
