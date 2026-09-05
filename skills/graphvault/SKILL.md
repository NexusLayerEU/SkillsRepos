---
name: graphvault
description: >
  GraphVault is the NexusLayer knowledge graph store. Use this skill when the user
  mentions graphvault, wants to push or store a graph, query a stored graph, visualize
  code knowledge, or access project graphs on graph.nexuslayer.eu.
---

# GraphVault — Knowledge Graph Store

GraphVault stores code knowledge graphs (nodes, relationships) and exposes them via REST and an interactive visual explorer.

**Dashboard:** https://graph.nexuslayer.eu  
**API base:** https://graph.nexuslayer.eu/api/v1  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## CLI Setup
```bash
# Install graphvault CLI (requires Node.js 18+)
npm install -g @nexuslayer/graphvault-cli

# Configure
graphvault config set --server https://graph.nexuslayer.eu --token {{NEXUSLAYER_TOKEN}}
```

## Push a Graph
```bash
graphvault push graphify-out/graph.json \
  --project my-project \
  --html graphify-out/graph.html \
  --report graphify-out/GRAPH_REPORT.md
```

## List Graphs
```bash
graphvault ls
```

## Query a Graph
```bash
graphvault query my-project "what connects auth to the database?"
```

---

## REST API

### List Projects
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://graph.nexuslayer.eu/api/v1/graphs | python3 -m json.tool
```

### Get Graph Nodes
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  "https://graph.nexuslayer.eu/api/v1/graphs/PROJECT_NAME/nodes?type=FILE" | python3 -m json.tool
```

### Semantic Query
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"question": "how does authentication work?", "limit": 5}' \
  https://graph.nexuslayer.eu/api/v1/graphs/PROJECT_NAME/query | python3 -m json.tool
```

---

## Tier Limits

| Plan | Nodes | Projects |
|------|-------|---------|
| FREE | 10,000 | 3 |
| PRO | 500,000 | 25 |
| MAX | Unlimited | Unlimited |
