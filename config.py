"""
Shared Modal configuration: App, Images, Volumes, Secrets, Dicts, Queues.
All agents and services import from here.
"""

import modal

# ---------------------------------------------------------------------------
# Modal App
# ---------------------------------------------------------------------------
app = modal.App("ai-decision-engine")

# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------
hf_secret = modal.Secret.from_name("huggingface-secret")

# ---------------------------------------------------------------------------
# Persistent storage
# ---------------------------------------------------------------------------
results_vol = modal.Volume.from_name("decision-engine-results", create_if_missing=True)
model_vol = modal.Volume.from_name("decision-engine-models", create_if_missing=True)

# ---------------------------------------------------------------------------
# Distributed KV store (inter-agent memory, TTL 7 days)
# ---------------------------------------------------------------------------
memory_dict = modal.Dict.from_name("agent-memory", create_if_missing=True)

# ---------------------------------------------------------------------------
# Real-time event queue (session-partitioned) for UI updates
# ---------------------------------------------------------------------------
event_queue = modal.Queue.from_name("ui-events", create_if_missing=True)

# ---------------------------------------------------------------------------
# Container images
# ---------------------------------------------------------------------------

# Helper: common local source mounts for all images
def _add_local_sources(image):
    """Add all local Python source directories to a Modal image."""
    return (
        image
        .add_local_python_source("config")
        .add_local_python_source("agents")
        .add_local_python_source("memory")
        .add_local_python_source("sandbox")
        .add_local_python_source("llm")
        .add_local_python_source("web")
        .add_local_python_source("data")
        .add_local_dir("data", remote_path="/data")
    )

# Base image shared by simulation, research, evaluation agents
sim_image = _add_local_sources(
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "numpy>=1.26",
        "scipy>=1.12",
        "pandas>=2.2",
        "pydantic>=2.6",
        "httpx>=0.27",
    )
)

# Image for the vLLM inference server
# (vllm_image is defined in llm/server.py)
# (vllm_image is defined in llm/server.py instead)
llm_image = None  # not used anymore - vLLM image defined in llm.server

# Image for FastAPI web backend
web_image = _add_local_sources(
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi[standard]>=0.115",
        "uvicorn>=0.30",
        "pydantic>=2.6",
    )
).add_local_dir("web/frontend/dist", remote_path="/assets/frontend/dist")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LLM_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
LLM_MAX_TOKENS = 4096
LLM_TEMPERATURE = 0.3

# Simulation defaults
SIM_NUM_SCENARIOS = 5000
SIM_BATCH_SIZE = 50  # scenarios per container
SIM_NUM_BATCHES = SIM_NUM_SCENARIOS // SIM_BATCH_SIZE  # 100 containers

# Memory key prefixes
KEY_PLAN = "plan"
KEY_RESEARCH = "research"
KEY_SIMULATION = "simulation"
KEY_EVALUATION = "evaluation"
KEY_FINAL = "final"
KEY_STATUS = "status"
