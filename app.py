"""
AI Decision Engine — Main Modal Application

This is the entry point for the entire system.
Imports all agents, services, and web endpoints to register them with Modal.

Usage:
  modal serve app.py     # Development with live reload
  modal deploy app.py    # Production deployment
  modal run app.py       # Run CLI entrypoint (test pipeline)
"""

# Import the Modal App instance (this also sets up images, volumes, etc.)
from config import app

# Import all Modal functions/classes to register them with the app
# Each import triggers @app.function/@app.cls decorators

# LLM server (Qwen 2.5 via Modal RPC)
from llm.server import LlmServer  # noqa: F401

# Agents
from agents.planner import plan  # noqa: F401
from agents.research import research  # noqa: F401
from agents.simulation import run_single_batch, run_full_simulation  # noqa: F401
from agents.evaluation import evaluate  # noqa: F401
from agents.orchestrator import run_pipeline, run_followup  # noqa: F401

# Sandbox executor
from sandbox.executor import execute_code, execute_analysis  # noqa: F401

# Web API
from web.api import web  # noqa: F401


# ---------------------------------------------------------------------------
# CLI entrypoint for quick testing
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(
    prompt: str = "Design a profitable coffee shop in Urbana, IL",
    session_id: str = "",
):
    """
    Run the full pipeline from the command line.

    Usage:
      modal run app.py
      modal run app.py --prompt "Should I open a food truck in Austin?"
    """
    import uuid
    import json
    import time

    if not session_id:
        session_id = uuid.uuid4().hex[:12]

    print(f"\n{'='*60}")
    print(f"  AI Decision Engine")
    print(f"  Session: {session_id}")
    print(f"  Prompt: {prompt}")
    print(f"{'='*60}\n")

    # Run the full pipeline
    # (vLLM server starts automatically with LlmServer.startup())
    result = run_pipeline.remote(prompt, session_id)

    # Print summary
    evaluation = result.get("evaluation", {})
    metrics = evaluation.get("quantitative_metrics", {})
    analysis = evaluation.get("llm_analysis", {})
    sim_summary = evaluation.get("simulation_summary", {})

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Total pipeline time: {result.get('pipeline_elapsed_seconds', 0):.1f}s")
    print(f"  Simulations: {sim_summary.get('total_scenarios', 0):,} in {sim_summary.get('elapsed_seconds', 0):.1f}s")
    print(f"  Containers used: {sim_summary.get('num_containers', 0)}")
    print(f"")
    print(f"  Expected Annual Profit: ${metrics.get('expected_annual_profit', 0):,.0f}")
    print(f"  Mean ROI: {metrics.get('mean_roi_pct', 0):.1f}%")
    print(f"  Probability of Loss: {metrics.get('probability_of_loss_pct', 0):.1f}%")
    print(f"  Break-even: {metrics.get('break_even_months', 'N/A')} months")
    print(f"  Value at Risk (P10): ${metrics.get('value_at_risk_p10', 0):,.0f}")
    print(f"")
    print(f"  Recommendation: {analysis.get('recommendation', 'N/A')}")
    print(f"  Confidence: {analysis.get('confidence_level', 'N/A')}")
    print(f"{'='*60}")

    if analysis.get("executive_summary"):
        print(f"\n  EXECUTIVE SUMMARY")
        print(f"  {'-'*56}")
        for line in analysis["executive_summary"].split("\n"):
            print(f"  {line}")

    print(f"\n  Full results saved to Modal Volume: decision-engine-results/{session_id}/")
    print()

    return result
