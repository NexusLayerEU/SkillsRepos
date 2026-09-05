"""MyApify Actor SDK — Python"""
import os, json, urllib.request

_API_URL    = os.environ.get('MYAPIFY_API_URL', 'http://localhost:4280')
_RUN_ID     = os.environ.get('MYAPIFY_RUN_ID', '')
_DATASET_ID = os.environ.get('MYAPIFY_DATASET_ID', '')
_API_KEY    = os.environ.get('MYAPIFY_API_KEY', '')
_INPUT      = json.loads(os.environ.get('ACTOR_INPUT', '{}'))

def get_input():
    """Return the actor input as a dict."""
    return _INPUT

def push_data(items):
    """Push one item or a list of items to the output dataset."""
    if not isinstance(items, list):
        items = [items]
    data = json.dumps(items).encode()
    req  = urllib.request.Request(
        f"{_API_URL}/api/datasets/{_DATASET_ID}/items",
        data=data,
        headers={"Content-Type": "application/json", "x-api-key": _API_KEY},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def log(message, level="INFO"):
    """Print a log message (captured by the run engine)."""
    print(f"[{level}] {message}", flush=True)
