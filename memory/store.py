"""
Memory store helpers for inter-agent communication and persistent storage.

Uses modal.Dict for fast KV access and modal.Volume for large artifacts.
"""

from __future__ import annotations

import json
import time
from typing import Any


def _get_dict():
    from config import memory_dict
    return memory_dict


def _get_vol():
    from config import results_vol
    return results_vol


def _get_queue():
    from config import event_queue
    return event_queue


# ---------------------------------------------------------------------------
# Key-Value memory (modal.Dict)
# ---------------------------------------------------------------------------

def save(session_id: str, key: str, value: Any) -> None:
    """Store a value in shared agent memory."""
    d = _get_dict()
    d[f"{session_id}:{key}"] = value


def load(session_id: str, key: str, default: Any = None) -> Any:
    """Load a value from shared agent memory."""
    d = _get_dict()
    try:
        return d[f"{session_id}:{key}"]
    except KeyError:
        return default


def save_many(session_id: str, data: dict[str, Any]) -> None:
    """Store multiple key-value pairs at once."""
    d = _get_dict()
    for k, v in data.items():
        d[f"{session_id}:{k}"] = v


def list_keys(session_id: str) -> list[str]:
    """List all keys for a given session (expensive — use sparingly)."""
    d = _get_dict()
    prefix = f"{session_id}:"
    return [k for k in d.keys() if k.startswith(prefix)]


# ---------------------------------------------------------------------------
# Volume-based artifact storage (large files)
# ---------------------------------------------------------------------------

def save_artifact(session_id: str, filename: str, data: Any) -> None:
    """Write a JSON-serializable object to the results volume."""
    vol = _get_vol()
    import os
    dir_path = f"/results/{session_id}"
    os.makedirs(dir_path, exist_ok=True)
    with open(f"{dir_path}/{filename}", "w") as f:
        json.dump(data, f)
    vol.commit()


def load_artifact(session_id: str, filename: str) -> Any:
    """Read a JSON artifact from the results volume."""
    vol = _get_vol()
    vol.reload()
    with open(f"/results/{session_id}/{filename}", "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Event queue (real-time UI updates)
# ---------------------------------------------------------------------------

def emit_event(session_id: str, event: dict) -> None:
    """Push a UI event onto the session-partitioned queue."""
    q = _get_queue()
    event["timestamp"] = time.time()
    q.put(event, partition=session_id)


def poll_events(session_id: str, timeout: float = 5.0) -> list[dict]:
    """Pull all available events for a session (non-blocking after timeout)."""
    q = _get_queue()
    events = []
    try:
        batch = q.get_many(100, timeout=timeout, partition=session_id)
        events.extend(batch)
    except Exception:
        pass
    return events


# ---------------------------------------------------------------------------
# Session context builder (for follow-up queries)
# ---------------------------------------------------------------------------

def get_session_context(session_id: str) -> dict[str, Any]:
    """
    Reconstruct all stored data for a session.
    Used by the orchestrator to support follow-up queries without re-running
    everything from scratch.
    """
    d = _get_dict()
    prefix = f"{session_id}:"
    context = {}
    for k in d.keys():
        if k.startswith(prefix):
            short_key = k[len(prefix):]
            context[short_key] = d[k]
    return context


def get_status(session_id: str) -> dict[str, Any]:
    """Get the current pipeline status for a session."""
    return load(session_id, "status", default={
        "phase": "idle",
        "progress": 0,
        "message": "Not started",
    })


def set_status(session_id: str, phase: str, progress: float, message: str) -> None:
    """Update the pipeline status and emit a UI event."""
    status = {"phase": phase, "progress": progress, "message": message}
    save(session_id, "status", status)
    emit_event(session_id, {"event": "status_update", **status})
