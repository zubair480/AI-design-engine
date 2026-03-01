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

# 3-Tier Agent Pipeline (Map-Reduce architecture)
from agents.planner import plan  # noqa: F401        # Tier 1: The Architect
from agents.analyst import analyze_region  # noqa: F401  # Tier 2: The Swarm
from agents.conclusion import conclude  # noqa: F401     # Tier 3: The Advisor
from agents.orchestrator import run_pipeline, run_followup  # noqa: F401

# Legacy agents (kept for backward compatibility)
from agents.research import research  # noqa: F401
from agents.simulation import run_single_batch, run_full_simulation  # noqa: F401
from agents.evaluation import evaluate  # noqa: F401

# Sandbox executor
from sandbox.executor import execute_code, execute_analysis  # noqa: F401

# Web API
from web.api import web  # noqa: F401


# ---------------------------------------------------------------------------
# CLI entrypoint for quick testing
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(
    prompt: str = "Where should I invest $500k in real estate in Southern Illinois?",
    session_id: str = "",
):
    """
    Run the full 3-tier Map-Reduce investment analysis pipeline.

    Usage:
      modal run app.py
      modal run app.py --prompt "Best rental properties under $300k in Texas"
      modal run app.py --prompt "Where should I invest $500k in Southern Illinois?"
    """
    import uuid
    import json
    import time

    if not session_id:
        session_id = uuid.uuid4().hex[:12]

    print(f"\n{'='*70}")
    print(f"  AI Real Estate Investment Engine  (Map-Reduce Multi-Agent)")
    print(f"  Session : {session_id}")
    print(f"  Prompt  : {prompt}")
    print(f"{'='*70}\n")

    # Run the full pipeline (vLLM server cold-starts automatically)
    result = run_pipeline.remote(prompt, session_id)

    # ── Extract results ──
    plan = result.get("plan", {})
    reports = result.get("analyst_reports", [])
    conclusion = result.get("conclusion", {})

    # ── Print Planner output ──
    print(f"\n{'='*70}")
    print(f"  PLANNER OUTPUT")
    print(f"{'='*70}")
    print(f"  Budget       : {plan.get('client_budget', 'N/A')}")
    print(f"  Goals        : {', '.join(plan.get('investment_goals', []))}")
    print(f"  Time Horizon : {plan.get('time_horizon', 'N/A')}")
    print(f"  Risk Profile : {plan.get('risk_tolerance', 'N/A')}")
    print(f"  Regions      : {', '.join(plan.get('target_regions', []))}")

    # ── Print Analyst scoreboard ──
    print(f"\n{'='*70}")
    print(f"  ANALYST SCOREBOARD")
    print(f"  {'Region':<25} {'Risk':>6} {'ROI':>6} {'Feas.':>6} {'TOTAL':>7}")
    print(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*6} {'-'*7}")
    for rpt in reports:
        sc = rpt.get("investment_score", {})
        print(
            f"  {rpt.get('region', '?'):<25} "
            f"{sc.get('risk', '?'):>5}/20 "
            f"{sc.get('roi_potential', '?'):>4}/50 "
            f"{sc.get('feasibility', '?'):>4}/30 "
            f"{sc.get('total', '?'):>5}/100"
        )

    # ── Print Conclusion ──
    print(f"\n{'='*70}")
    print(f"  FINAL RECOMMENDATION")
    print(f"{'='*70}")
    print(f"  Verdict    : {conclusion.get('recommendation', 'N/A').upper()}")
    print(f"  Top Region : {conclusion.get('recommended_region', 'N/A')}")
    if conclusion.get("recommended_strategy"):
        print(f"  Strategy   : {conclusion['recommended_strategy']}")
    print(f"")
    print(f"  Pipeline time: {result.get('pipeline_elapsed_seconds', 0):.1f}s")

    # ── Print the full advisory memo ──
    memo = conclusion.get("full_advisory_memo", conclusion.get("executive_summary", ""))
    if memo:
        print(f"\n{'='*70}")
        print(f"  ADVISORY MEMO")
        print(f"  {'-'*66}")
        for line in memo.split("\n"):
            print(f"  {line}")

    # ── Top risks ──
    risks = conclusion.get("top_risks", [])
    if risks:
        print(f"\n  TOP RISKS")
        print(f"  {'-'*66}")
        for i, risk in enumerate(risks, 1):
            print(f"  {i}. {risk}")

    # ── Next steps ──
    steps = conclusion.get("next_steps", [])
    if steps:
        print(f"\n  NEXT STEPS")
        print(f"  {'-'*66}")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")

    print(f"\n  Full results saved to Modal Dict: session {session_id}")
    print()

    return result
