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


# ---------------------------------------------------------------------------
# Lightweight Vector "Supermemory" Helpers
# - Optional: uses sentence-transformers when available
# - Persists vectors per-session to the results volume as `vectors.json`
# - Provides: save_embedding, query_similar, clear_vectors
# ---------------------------------------------------------------------------


def _ensure_vectors_artifact(session_id: str) -> list[dict]:
    """Load or initialize the vectors artifact for a session."""
    try:
        return load_artifact(session_id, "vectors.json") or []
    except Exception:
        # File may not exist yet
        return []


def _persist_vectors(session_id: str, vectors: list[dict]) -> None:
    """Persist the vectors list to the results volume."""
    save_artifact(session_id, "vectors.json", vectors)


def _compute_embedding(text: str) -> list[float]:
    """Compute an embedding for `text` using sentence-transformers if installed.

    Raises a clear error if no embedding backend is available.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError(
            "No embedding backend found. Install 'sentence-transformers' or configure an external vector DB."
        ) from e

    # Cache the model on the function to avoid reloading repeatedly
    if not hasattr(_compute_embedding, "_model"):
        _compute_embedding._model = SentenceTransformer("all-MiniLM-L6-v2")
    emb = _compute_embedding._model.encode(text)
    return emb.tolist()


def save_embedding(session_id: str, key: str, text: str, metadata: dict | None = None, embedding: list[float] | None = None) -> dict:
    """Save a text + embedding into the session's vector store.

    Returns the stored vector record.
    """
    vectors = _ensure_vectors_artifact(session_id)
    if embedding is None:
        embedding = _compute_embedding(text)

    record = {
        "id": f"{key}-{int(time.time()*1000)}",
        "key": key,
        "text": text,
        "embedding": embedding,
        "metadata": metadata or {},
        "timestamp": time.time(),
    }
    vectors.append(record)
    _persist_vectors(session_id, vectors)
    return record


def _cosine_sim(a: list[float], b: list[float]) -> float:
    # Pure-Python cosine similarity (safe fallback, avoids numpy requirement)
    sa = 0.0
    sb = 0.0
    dot = 0.0
    for x, y in zip(a, b):
        dot += x * y
        sa += x * x
        sb += y * y
    if sa == 0 or sb == 0:
        return 0.0
    return dot / ((sa ** 0.5) * (sb ** 0.5))


def query_similar(session_id: str, query_text: str | None = None, k: int = 5, query_embedding: list[float] | None = None) -> list[dict]:
    """Return top-k similar vector records for a session.

    Either provide `query_text` (will be embedded) or `query_embedding` directly.
    Each returned dict contains `id`, `key`, `text`, `metadata`, and `score` (cosine).
    """
    vectors = _ensure_vectors_artifact(session_id)
    if not vectors:
        return []

    if query_embedding is None:
        if not query_text:
            raise ValueError("Either query_text or query_embedding must be provided")
        query_embedding = _compute_embedding(query_text)

    # Score all vectors
    scored = []
    for rec in vectors:
        emb = rec.get("embedding")
        if not emb:
            continue
        score = _cosine_sim(query_embedding, emb)
        scored.append({**rec, "score": score})

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:k]


def clear_vectors(session_id: str) -> None:
    """Remove all stored vectors for a session."""
    _persist_vectors(session_id, [])
