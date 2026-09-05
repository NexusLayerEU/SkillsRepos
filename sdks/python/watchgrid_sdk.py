"""
WatchGrid Python SDK
====================
Production-quality SDK for ingesting agent observability events into WatchGrid.

Supports:
- Sync and async usage
- Context manager: `with wg.run("id") as run:`
- Decorator: `@wg.track`
- Manual event logging
- Auto-batching (flush every 1 second or 50 events)
- Thread-safe buffer
"""

from __future__ import annotations

import asyncio
import functools
import json
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _post(url: str, headers: dict, payload: dict, timeout: int = 10) -> int:
    """HTTP POST using stdlib only. Returns HTTP status code."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status
    except HTTPError as exc:
        return exc.code
    except URLError:
        return 0


# ---------------------------------------------------------------------------
# Run context (returned by `with wg.run(...)`)
# ---------------------------------------------------------------------------

class RunContext:
    """
    Bound to a specific run_id. Provides convenience methods so callers
    don't have to pass run_id on every call.
    """

    def __init__(self, client: "WatchGridClient", run_id: str) -> None:
        self._client = client
        self.run_id = run_id

    def log_llm_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: int,
    ) -> None:
        self._client.log_llm_call(
            self.run_id, model, input_tokens, output_tokens, cost_usd, latency_ms
        )

    def log_tool_call(self, tool_name: str, duration_ms: int) -> None:
        self._client.log_tool_call(self.run_id, tool_name, duration_ms)

    def log_error(self, message: str) -> None:
        self._client.log_error(self.run_id, message)


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------

class WatchGridClient:
    """
    WatchGrid observability client.

    Args:
        base_url: WatchGrid API base URL, e.g. "https://watchgrid.nexuslayer.eu"
        sdk_key:  Agent SDK key starting with "wg_sdk_"
        batch_size: Flush buffer after this many events (default 50)
        flush_interval: Auto-flush interval in seconds (default 1.0)
        timeout: HTTP request timeout in seconds (default 10)
    """

    def __init__(
        self,
        base_url: str,
        sdk_key: str,
        *,
        batch_size: int = 50,
        flush_interval: float = 1.0,
        timeout: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._sdk_key = sdk_key
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._timeout = timeout

        self._buffer: list[dict] = []
        self._lock = threading.Lock()

        self._headers = {
            "X-SDK-Key": sdk_key,
            "Content-Type": "application/json",
        }

        self._flush_thread = threading.Thread(
            target=self._auto_flush_loop, daemon=True
        )
        self._flush_thread.start()

    # ------------------------------------------------------------------
    # Event builders
    # ------------------------------------------------------------------

    def start_run(self, run_id: Optional[str] = None) -> str:
        """
        Enqueue a RUN_START event.

        Args:
            run_id: Optional run ID. If omitted, a UUID4 is generated.

        Returns:
            The run_id used.
        """
        run_id = run_id or str(uuid.uuid4())
        self._enqueue({"type": "RUN_START", "runId": run_id, "timestamp": _utcnow()})
        return run_id

    def end_run(
        self,
        run_id: str,
        status: str = "SUCCESS",
        error: Optional[str] = None,
    ) -> None:
        """
        Enqueue a RUN_END event.

        Args:
            run_id: The run to close.
            status: "SUCCESS", "FAILURE", or "TIMEOUT"
            error:  Optional error message (also logs an ERROR event if provided)
        """
        if error:
            self.log_error(run_id, error)
            status = "FAILURE"
        self._enqueue(
            {"type": "RUN_END", "runId": run_id, "status": status, "timestamp": _utcnow()}
        )

    def log_llm_call(
        self,
        run_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: int,
    ) -> None:
        """Record a single LLM API call."""
        self._enqueue(
            {
                "type": "LLM_CALL",
                "runId": run_id,
                "model": model,
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "costUsd": round(cost_usd, 8),
                "latencyMs": latency_ms,
                "timestamp": _utcnow(),
            }
        )

    def log_tool_call(self, run_id: str, tool_name: str, duration_ms: int) -> None:
        """Record a tool/function invocation."""
        self._enqueue(
            {
                "type": "TOOL_CALL",
                "runId": run_id,
                "toolName": tool_name,
                "durationMs": duration_ms,
                "timestamp": _utcnow(),
            }
        )

    def log_error(self, run_id: str, message: str) -> None:
        """Record an error or exception."""
        self._enqueue(
            {"type": "ERROR", "runId": run_id, "message": message, "timestamp": _utcnow()}
        )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    @contextmanager
    def run(self, run_id: Optional[str] = None):
        """
        Context manager that wraps a block of code as a WatchGrid run.

        Usage::

            with wg.run("my-run-id") as run:
                run.log_llm_call("gpt-4o", 400, 100, 0.003, 1200)
        """
        run_id = run_id or str(uuid.uuid4())
        self.start_run(run_id)
        ctx = RunContext(self, run_id)
        try:
            yield ctx
            self.end_run(run_id, status="SUCCESS")
        except Exception as exc:
            self.end_run(run_id, status="FAILURE", error=str(exc))
            raise
        finally:
            self.flush()

    # ------------------------------------------------------------------
    # Decorator
    # ------------------------------------------------------------------

    def track(self, func: Callable) -> Callable:
        """
        Decorator that automatically creates a WatchGrid run for each
        function invocation.

        Usage::

            @wg.track
            def my_agent(prompt: str) -> str:
                ...
        """
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                run_id = str(uuid.uuid4())
                self.start_run(run_id)
                try:
                    result = await func(*args, **kwargs)
                    self.end_run(run_id, status="SUCCESS")
                    return result
                except Exception as exc:
                    self.end_run(run_id, status="FAILURE", error=str(exc))
                    raise
                finally:
                    self.flush()
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                run_id = str(uuid.uuid4())
                self.start_run(run_id)
                try:
                    result = func(*args, **kwargs)
                    self.end_run(run_id, status="SUCCESS")
                    return result
                except Exception as exc:
                    self.end_run(run_id, status="FAILURE", error=str(exc))
                    raise
                finally:
                    self.flush()
            return sync_wrapper

    # ------------------------------------------------------------------
    # Async variants
    # ------------------------------------------------------------------

    async def async_start_run(self, run_id: Optional[str] = None) -> str:
        """Async variant of start_run."""
        return self.start_run(run_id)

    async def async_end_run(
        self,
        run_id: str,
        status: str = "SUCCESS",
        error: Optional[str] = None,
    ) -> None:
        """Async variant of end_run."""
        self.end_run(run_id, status=status, error=error)

    async def async_log_llm_call(
        self,
        run_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: int,
    ) -> None:
        """Async variant of log_llm_call."""
        self.log_llm_call(run_id, model, input_tokens, output_tokens, cost_usd, latency_ms)

    async def async_log_tool_call(
        self, run_id: str, tool_name: str, duration_ms: int
    ) -> None:
        """Async variant of log_tool_call."""
        self.log_tool_call(run_id, tool_name, duration_ms)

    async def async_log_error(self, run_id: str, message: str) -> None:
        """Async variant of log_error."""
        self.log_error(run_id, message)

    async def async_flush(self) -> None:
        """Async variant of flush — runs flush in a thread executor."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.flush)

    # ------------------------------------------------------------------
    # Buffer management
    # ------------------------------------------------------------------

    def _enqueue(self, event: dict) -> None:
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= self._batch_size:
                self._send_and_clear()

    def flush(self) -> None:
        """Flush all buffered events to WatchGrid immediately."""
        with self._lock:
            self._send_and_clear()

    def _send_and_clear(self) -> None:
        """Must be called with self._lock held."""
        if not self._buffer:
            return
        batch = list(self._buffer)
        self._buffer.clear()
        # Release lock before doing I/O
        self._lock.release()
        try:
            status = _post(
                f"{self._base_url}/ingest/events",
                headers=self._headers,
                payload={"events": batch},
                timeout=self._timeout,
            )
            if status not in (200, 202):
                # Re-enqueue events on transient failure (best-effort)
                with self._lock:
                    self._buffer[:0] = batch
                return
        finally:
            self._lock.acquire()

    def _auto_flush_loop(self) -> None:
        while True:
            time.sleep(self._flush_interval)
            with self._lock:
                self._send_and_clear()

    def __repr__(self) -> str:
        return f"WatchGridClient(base_url={self._base_url!r})"


# ---------------------------------------------------------------------------
# Usage example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import random

    WATCHGRID_URL = "https://watchgrid.nexuslayer.eu"
    SDK_KEY = "wg_sdk_YOUR_KEY_HERE"

    wg = WatchGridClient(WATCHGRID_URL, SDK_KEY)

    # ---- Example 1: Context manager ----
    print("Running context manager example...")
    with wg.run() as run:
        print(f"  Run ID: {run.run_id}")
        # Simulate LLM call
        time.sleep(0.05)
        run.log_llm_call(
            model="gpt-4o",
            input_tokens=412,
            output_tokens=95,
            cost_usd=0.0031,
            latency_ms=1130,
        )
        # Simulate tool call
        run.log_tool_call("web_search", duration_ms=320)
        # Simulate second LLM call
        run.log_llm_call(
            model="gpt-4o",
            input_tokens=580,
            output_tokens=210,
            cost_usd=0.0072,
            latency_ms=1840,
        )
    print("  Done.")

    # ---- Example 2: Decorator ----
    @wg.track
    def my_agent(prompt: str) -> str:
        """Simple agent that gets auto-tracked."""
        time.sleep(0.02)
        return f"Processed: {prompt}"

    print("\nRunning decorator example...")
    result = my_agent("Summarise the quarterly report")
    print(f"  Result: {result}")

    # ---- Example 3: Manual tracking ----
    print("\nRunning manual example...")
    run_id = wg.start_run()
    print(f"  Run ID: {run_id}")
    try:
        wg.log_llm_call(run_id, "claude-3-5-sonnet", 300, 80, 0.0025, 950)
        wg.log_tool_call(run_id, "database_query", 45)
        wg.end_run(run_id, status="SUCCESS")
    except Exception as exc:
        wg.end_run(run_id, status="FAILURE", error=str(exc))

    wg.flush()
    print("  Flushed. Check your WatchGrid dashboard at https://watchgrid.nexuslayer.eu")

    # ---- Example 4: Async usage ----
    async def async_example():
        print("\nRunning async example...")
        run_id = await wg.async_start_run()
        await asyncio.sleep(0.02)
        await wg.async_log_llm_call(run_id, "gpt-4o-mini", 200, 60, 0.0008, 430)
        await wg.async_end_run(run_id, status="SUCCESS")
        await wg.async_flush()
        print(f"  Async run {run_id} complete.")

    asyncio.run(async_example())
