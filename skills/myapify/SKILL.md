---
name: myapify
description: >
  MyApify is the NexusLayer self-hosted actor runner for web scraping and automation.
  Use this skill when the user says "list actors", "run actor", "create actor", "scrape",
  "myapify", "list runs", "get dataset", "schedule actor", or any request to manage
  or execute web scraping actors on the MyApify platform.
---

# MyApify Skill

Interact with the self-hosted MyApify actor runner — upload actors, run them on demand or schedule, store datasets, manage key-value state.

**Frontend:** https://myapify.nexuslayer.eu  
**API base:** https://myapify.nexuslayer.eu/api  
**Auth:** `Authorization: Bearer {{NEXUSLAYER_TOKEN}}`

---

## My Profile / API Key
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/auth/me | python3 -m json.tool
```

## Stats / Overview
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/stats | python3 -m json.tool
```

---

## Actors

### List Actors
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/actors | python3 -m json.tool
```

### Create an Actor
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-scraper",
    "description": "Scrapes product prices",
    "code": "const { Actor } = require(\"apify\");\nActor.main(async () => { /* your code */ });"
  }' \
  https://myapify.nexuslayer.eu/api/actors | python3 -m json.tool
```

### Run an Actor
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"input": {"url": "https://example.com"}}' \
  https://myapify.nexuslayer.eu/api/actors/ACTOR_ID/runs | python3 -m json.tool
```

---

## Runs

### List All Runs
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/runs | python3 -m json.tool
```

### Get Run Status
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/runs/RUN_ID | python3 -m json.tool
```

---

## Datasets

### Get Dataset Items
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/datasets/DATASET_ID/items | python3 -m json.tool
```

---

## Schedules

### List Schedules
```bash
curl -s -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  https://myapify.nexuslayer.eu/api/schedules | python3 -m json.tool
```

### Create a Schedule
```bash
curl -s -X POST \
  -H "Authorization: Bearer {{NEXUSLAYER_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{
    "actorId": "ACTOR_ID",
    "cronExpression": "0 9 * * *",
    "input": {"url": "https://example.com"},
    "isEnabled": true
  }' \
  https://myapify.nexuslayer.eu/api/schedules | python3 -m json.tool
```

---

## Actor SDK (Python)

For actors running inside MyApify, use the built-in SDK:

```python
# Available inside actor runtime as environment variables
import os, json, urllib.request

DATASET_ID = os.environ.get('MYAPIFY_DATASET_ID')
API_KEY    = os.environ.get('MYAPIFY_API_KEY')
API_URL    = os.environ.get('MYAPIFY_API_URL', 'https://myapify.nexuslayer.eu')

def push_data(items):
    if not isinstance(items, list): items = [items]
    req = urllib.request.Request(
        f"{API_URL}/api/datasets/{DATASET_ID}/items",
        data=json.dumps(items).encode(),
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())
```

---

## Dashboard SSO Link
```
https://myapify.nexuslayer.eu?sso_token={{NEXUSLAYER_TOKEN}}
```
