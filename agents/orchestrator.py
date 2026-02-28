"""
Orchestrator — Executes the full agent pipeline from user prompt to final output.

Manages the DAG execution: plans tasks, fans out research in parallel,
runs simulations, and produces the final evaluation.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import modal
from config import app, sim_image


@app.function(image=sim_image, timeout=900)
def run_pipeline(user_prompt: str, session_id: str | None = None) -> dict[str, Any]:
    """
    Execute the full decision engine pipeline.

    Steps:
        1. Planner: decompose objective → task DAG
        2. Research: parallel execution of all research tasks
        3. Simulation: Monte Carlo fan-out across 100 containers
        4. Evaluation: scoring + LLM strategic analysis

    Args:
        user_prompt: Free-text business objective.
        session_id: Optional session ID (generated if None).

    Returns:
        Final evaluation results.
    """
    from memory.store import save, emit_event, set_status
    from agents.planner import plan
    from agents.research import research
    from agents.simulation import run_full_simulation
    from agents.evaluation import evaluate

    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    pipeline_start = time.time()

    save(session_id, "user_prompt", user_prompt)
    emit_event(session_id, {
        "event": "pipeline_started",
        "session_id": session_id,
        "prompt": user_prompt,
    })

    # ---- PHASE 1: PLANNING ----
    plan_result = plan.remote(user_prompt, session_id)
    subtasks = plan_result["subtasks"]
    waves = plan_result["execution_waves"]

    # ---- PHASE 2: RESEARCH (parallel) ----
    # Collect all research-type tasks from wave 0
    research_tasks = [t for t in subtasks if t["type"] == "research"]

    # Map research subtask IDs for parallel execution
    research_inputs = [
        (t["id"], session_id, t.get("params", {}))
        for t in research_tasks
    ]

    research_results = {}
    if research_inputs:
        set_status(session_id, "researching", 0.0, f"Running {len(research_inputs)} research tasks in parallel...")

        # 🔥 PARALLEL RESEARCH — all research tasks run concurrently
        results = list(research.starmap(research_inputs))
        for r in results:
            subtask_id = r.get("_subtask_id", "unknown")
            research_results[subtask_id] = r

    # ---- PHASE 3: SIMULATION (massively parallel) ----
    # First, ask the LLM to generate business-specific simulation parameters
    # based on the prompt, location, and research findings
    llm_business_params = _generate_business_params(
        user_prompt,
        plan_result.get("business_type", "unknown"),
        plan_result.get("location", "unknown"),
        research_results,
    )
    research_results["_llm_business_params"] = llm_business_params

    # Check for simulation tasks
    sim_tasks = [t for t in subtasks if t["type"] == "simulation"]
    sim_result = None

    if sim_tasks:
        sim_result = run_full_simulation.remote(
            session_id=session_id,
            research_data=research_results,
        )

    # ---- PHASE 4: EVALUATION ----
    eval_result = evaluate.remote(session_id)

    pipeline_elapsed = round(time.time() - pipeline_start, 2)

    # ---- FINAL OUTPUT ----
    final_output = {
        "session_id": session_id,
        "user_prompt": user_prompt,
        "pipeline_elapsed_seconds": pipeline_elapsed,
        "plan": plan_result,
        "research": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in research_results.items()},
        "simulation": sim_result,
        "evaluation": eval_result,
    }

    save(session_id, "final_output", final_output)
    emit_event(session_id, {
        "event": "pipeline_complete",
        "session_id": session_id,
        "elapsed_seconds": pipeline_elapsed,
        "recommendation": eval_result.get("llm_analysis", {}).get("recommendation", "unknown"),
    })

    return final_output


@app.function(image=sim_image, timeout=600)
def run_followup(
    session_id: str,
    followup_prompt: str,
    override_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Handle a follow-up query that reuses prior research and re-runs simulation.

    Example: "What if rent increases 20%?"

    Args:
        session_id: Existing session to build upon.
        followup_prompt: The follow-up question.
        override_params: Explicit parameter overrides for simulation.

    Returns:
        Updated evaluation results.
    """
    from memory.store import load, save, emit_event, set_status
    from llm.client import call_llm_json
    from agents.simulation import run_full_simulation
    from agents.evaluation import evaluate

    set_status(session_id, "followup", 0.0, f"Processing follow-up: {followup_prompt[:80]}...")

    emit_event(session_id, {
        "event": "followup_started",
        "prompt": followup_prompt,
    })

    # If no explicit overrides, use LLM to interpret the follow-up
    if override_params is None:
        prior_params = load(session_id, "simulation", {}).get("parameters_used", {})
        override_params = call_llm_json(
            prompt=f"""Given these current simulation parameters:
{prior_params}

The user asks: "{followup_prompt}"

Return a JSON object with ONLY the parameters that should change.
For example, if rent increases 20%, return: {{"monthly_rent": {prior_params.get('monthly_rent', 3500) * 1.2}}}
Only include changed parameters.""",
            system_prompt="You are a parameter adjustment assistant. Output only a JSON object of changed parameters.",
            temperature=0.1,
        )

    # Re-run simulation with modified parameters (reuses research data)
    research_data = {}
    for key_suffix in ["demographics", "foot_traffic", "competitor_analysis"]:
        data = load(session_id, f"research:{key_suffix}")
        if data:
            research_data[key_suffix] = data

    sim_result = run_full_simulation.remote(
        session_id=session_id,
        research_data=research_data,
        override_params=override_params,
    )

    # Re-run evaluation
    eval_result = evaluate.remote(session_id)

    followup_output = {
        "session_id": session_id,
        "followup_prompt": followup_prompt,
        "parameter_changes": override_params,
        "simulation": sim_result,
        "evaluation": eval_result,
    }

    save(session_id, "followup_result", followup_output)
    emit_event(session_id, {
        "event": "followup_complete",
        "session_id": session_id,
    })

    return followup_output


# ---------------------------------------------------------------------------
# LLM-based business parameter generator
# ---------------------------------------------------------------------------

_PARAM_SYSTEM_PROMPT = """You are a business financial modeling expert. Given a business idea, location, and research data, estimate realistic simulation parameters.

You MUST output valid JSON with these exact keys:
{
  "foot_traffic_mean": <int, average daily foot traffic/customers near the business>,
  "foot_traffic_std": <int, standard deviation of daily traffic>,
  "conversion_rate_alpha": <float, Beta distribution alpha for purchase rate>,
  "conversion_rate_beta": <float, Beta distribution beta for purchase rate>,
  "avg_order_value_mean": <float, log-space mean of average order value (exp(x) = dollar amount)>,
  "avg_order_value_std": <float, log-space std dev>,
  "monthly_rent": <int, monthly rent in dollars>,
  "rent_variance": <float, 0-0.2, how much rent fluctuates>,
  "monthly_labor": <int, total monthly staff costs>,
  "monthly_cogs_pct": <float, 0.15-0.60, cost of goods as fraction of revenue>,
  "monthly_utilities": <int, monthly utility costs>,
  "initial_investment": <int, total startup capital needed>,
  "seasonal_amplitude": <float, 0-0.4, seasonal variation strength>
}

Guidelines for different business types:
- Coffee shop: foot_traffic 150-400, AOV exp(1.3-1.8)=$3.50-$6, COGS 25-35%, investment $80K-250K
- Food truck: foot_traffic 80-250, AOV exp(2.0-2.5)=$7-$12, COGS 30-40%, investment $50K-150K, low rent
- Warehouse: foot_traffic 10-50, AOV exp(5.5-7.5)=$250-$1800, COGS 60-80%, investment $500K-2M, high rent
- Co-working: foot_traffic 20-100, AOV exp(3.5-4.2)=$33-$67/day, COGS 10-20%, investment $200K-800K
- Restaurant: foot_traffic 100-350, AOV exp(2.5-3.5)=$12-$33, COGS 28-35%, investment $150K-500K

Adjust for location:
- Downtown/urban: higher rent, higher foot traffic
- Suburban: lower rent, lower foot traffic
- College town: seasonal (high Aug-May, low Jun-Jul), younger demographic
- Expensive cities (SF, NYC): 2-3x rent, higher wages

Be specific and realistic. Different businesses must produce VERY different numbers."""


def _generate_business_params(
    user_prompt: str,
    business_type: str,
    location: str,
    research_data: dict,
) -> dict:
    """Ask the LLM to generate business-specific simulation parameters."""
    from llm.client import call_llm_json

    research_summary = ""
    demo = research_data.get("demographics", {})
    ft = research_data.get("foot_traffic", {})
    comp = research_data.get("competitor_analysis", {})

    if demo:
        research_summary += f"Demographics: median income ${demo.get('median_income', 'N/A')}, student pct {demo.get('avg_student_pct', 'N/A')}, population {demo.get('total_population', 'N/A')}. "
    if ft:
        research_summary += f"Foot traffic: avg {ft.get('overall_avg_traffic', 'N/A')}/day. "
    if comp:
        research_summary += f"Competitors: {comp.get('total_competitors', 'N/A')} nearby, saturation {comp.get('market_saturation', 'N/A')}. "

    try:
        params = call_llm_json(
            prompt=f"""Business idea: {user_prompt}
Business type: {business_type}
Location: {location}
Research findings: {research_summary if research_summary else 'No local data available.'}

Generate realistic Monte Carlo simulation parameters for this specific business.""",
            system_prompt=_PARAM_SYSTEM_PROMPT,
            temperature=0.3,
        )
        # Validate keys and types
        validated = {}
        expected_ints = ["foot_traffic_mean", "foot_traffic_std", "monthly_rent", "monthly_labor", "monthly_utilities", "initial_investment"]
        expected_floats = ["conversion_rate_alpha", "conversion_rate_beta", "avg_order_value_mean", "avg_order_value_std", "rent_variance", "monthly_cogs_pct", "seasonal_amplitude"]

        for k in expected_ints:
            if k in params:
                try:
                    validated[k] = int(float(params[k]))
                except (ValueError, TypeError):
                    pass
        for k in expected_floats:
            if k in params:
                try:
                    validated[k] = float(params[k])
                except (ValueError, TypeError):
                    pass
        return validated
    except Exception as e:
        print(f"Warning: LLM param generation failed ({e}), using defaults")
        return {}
