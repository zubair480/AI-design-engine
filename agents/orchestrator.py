"""
Orchestrator — Map-Reduce pipeline linking the three agent tiers.

Stage 1  →  Planner (single LLM call → JSON with target regions)
             ↓
        Python fetches live market data from Zillow / Redfin for each region
             ↓
Stage 2  →  Parallel Analysts (N Modal containers, one per region)
             ↓
Stage 3  →  Conclusion (single LLM call synthesises all analyst reports)
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import modal
from config import app, sim_image


# ═══════════════════════════════════════════════════════════════════════════
# Main pipeline  (Planner → Data Fetch → Analysts → Conclusion)
# ═══════════════════════════════════════════════════════════════════════════

@app.function(image=sim_image, timeout=900)
def run_pipeline(user_prompt: str, session_id: str | None = None) -> dict[str, Any]:
    """
    Execute the full 3-tier Map-Reduce investment analysis pipeline.

    1. PLAN   — Planner agent decomposes the prompt into target regions.
    2. FETCH  — Python downloads live Zillow/Redfin data for every region.
    3. ANALYSE — Parallel Analyst agents deep-dive each region (the "Map" step).
    4. CONCLUDE — Conclusion agent synthesises all reports (the "Reduce" step).

    Args:
        user_prompt: Free-text investment objective.
        session_id:  Optional session ID (generated if None).

    Returns:
        Complete pipeline output dict.
    """
    from memory.store import save, emit_event, set_status
    from agents.planner import plan
    from agents.analyst import analyze_region
    from agents.conclusion import conclude
    from data.market_data import fetch_all_market_data

    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    pipeline_start = time.time()

    save(session_id, "user_prompt", user_prompt)
    emit_event(session_id, {
        "event": "pipeline_started",
        "session_id": session_id,
        "prompt": user_prompt,
    })

    # ──────────────────────────────────────────────────────────────────
    # STAGE 1: PLANNER  (The Architect)
    # ──────────────────────────────────────────────────────────────────
    print("\n🏗️  STAGE 1 / 4 — Planner: decomposing investment request...")
    plan_result = plan.remote(user_prompt, session_id)

    target_regions = plan_result["target_regions"]
    budget = plan_result["client_budget"]
    goals = plan_result["investment_goals"]
    instructions = plan_result["analyst_instructions"]

    print(f"   ✅ Planner identified {len(target_regions)} regions: {target_regions}")
    print(f"   Budget: {budget}  |  Goals: {', '.join(goals)}")

    # ──────────────────────────────────────────────────────────────────
    # STAGE 2: DATA FETCH  (Python downloads real market data)
    # ──────────────────────────────────────────────────────────────────
    print("\n📊  STAGE 2 / 4 — Fetching live market data from Zillow & Redfin...")
    set_status(session_id, "fetching_data", 0.0,
               f"Downloading market data for {len(target_regions)} regions...")

    market_data = fetch_all_market_data(target_regions)

    for region, data in market_data.items():
        has_value = "median_home_value" in data.get("zillow", {})
        has_rent = "median_rent" in data.get("zillow", {})
        print(f"   📍 {region}: home_value={'✅' if has_value else '❌'}  rent={'✅' if has_rent else '❌'}")

    save(session_id, "market_data", market_data)
    set_status(session_id, "fetching_data", 1.0, "Market data ready")

    # ──────────────────────────────────────────────────────────────────
    # STAGE 3: PARALLEL ANALYSTS  (The Swarm — one container per region)
    # ──────────────────────────────────────────────────────────────────
    print(f"\n🔬  STAGE 3 / 4 — Launching {len(target_regions)} Analyst agents in parallel...")
    set_status(session_id, "analysing", 0.0,
               f"Running {len(target_regions)} parallel analyst agents...")

    # Build starmap inputs: each analyst gets its region + data
    analyst_inputs = []
    for region in target_regions:
        region_data = market_data.get(region, {})
        summary = region_data.get("summary", "No market data available for this region.")
        analyst_inputs.append((
            region,                     # region
            budget,                     # budget
            summary,                    # market_data_summary
            instructions,               # analyst_instructions
            session_id,                 # session_id
            goals,                      # investment_goals
        ))

    # 🔥 PARALLEL DISPATCH — all analyst agents run concurrently on Modal
    analyst_reports: list[dict] = list(analyze_region.starmap(analyst_inputs))

    # Sort by total score descending
    analyst_reports.sort(
        key=lambda r: r.get("investment_score", {}).get("total", 0),
        reverse=True,
    )

    for report in analyst_reports:
        region = report.get("region", "?")
        score = report.get("investment_score", {}).get("total", "?")
        print(f"   ✅ {region}: Investment Score = {score}/100")

    save(session_id, "analyst_reports", analyst_reports)
    set_status(session_id, "analysing", 1.0, "All analyst reports complete")

    # ──────────────────────────────────────────────────────────────────
    # STAGE 4: CONCLUSION  (The Senior Wealth Advisor)
    # ──────────────────────────────────────────────────────────────────
    print("\n📝  STAGE 4 / 4 — Conclusion agent synthesising final recommendation...")
    conclusion = conclude.remote(
        user_prompt=user_prompt,
        analyst_reports=analyst_reports,
        plan_context=plan_result,
        session_id=session_id,
    )

    pipeline_elapsed = round(time.time() - pipeline_start, 2)

    # ──────────────────────────────────────────────────────────────────
    # FINAL OUTPUT
    # ──────────────────────────────────────────────────────────────────
    final_output = {
        "session_id": session_id,
        "user_prompt": user_prompt,
        "pipeline_elapsed_seconds": pipeline_elapsed,
        "plan": plan_result,
        "market_data_regions": list(market_data.keys()),
        "analyst_reports": analyst_reports,
        "conclusion": conclusion,
    }

    save(session_id, "final_output", final_output)
    emit_event(session_id, {
        "event": "pipeline_complete",
        "session_id": session_id,
        "elapsed_seconds": pipeline_elapsed,
        "recommendation": conclusion.get("recommendation", "unknown"),
        "recommended_region": conclusion.get("recommended_region", "unknown"),
    })

    return final_output


# ═══════════════════════════════════════════════════════════════════════════
# Follow-up handler (re-analyse with modified parameters)
# ═══════════════════════════════════════════════════════════════════════════

@app.function(image=sim_image, timeout=600)
def run_followup(
    session_id: str,
    followup_prompt: str,
    override_regions: list[str] | None = None,
) -> dict[str, Any]:
    """
    Handle a follow-up question that builds on a prior analysis.

    Examples:
      "What about Decatur instead of Marion?"
      "Re-run with a $300k budget."

    Args:
        session_id:        Existing session to build upon.
        followup_prompt:   The follow-up question.
        override_regions:  Explicit new regions to analyse (optional).

    Returns:
        Updated pipeline output.
    """
    from memory.store import load, save, emit_event, set_status
    from llm.client import call_llm_json
    from agents.analyst import analyze_region
    from agents.conclusion import conclude
    from data.market_data import fetch_all_market_data

    set_status(session_id, "followup", 0.0,
               f"Processing follow-up: {followup_prompt[:80]}...")

    emit_event(session_id, {
        "event": "followup_started",
        "prompt": followup_prompt,
    })

    # Load prior context
    prior_plan = load(session_id, "plan", {})
    user_prompt = prior_plan.get("user_prompt", "")
    budget = prior_plan.get("client_budget", "Not specified")
    goals = prior_plan.get("investment_goals", [])
    instructions = prior_plan.get("analyst_instructions", "")

    # Determine which regions to analyse
    if override_regions:
        target_regions = override_regions
    else:
        # Optionally enrich the LLM prompt with relevant prior findings from supermemory
        extra_context = ""
        try:
            from memory.store import query_similar

            # Query for up to 5 similar past research items using the followup text
            sims = query_similar(session_id, query_text=followup_prompt, k=5)
            if sims:
                lines = [f"- {s.get('text') or s.get('id')} (score={s.get('score',0):.3f})" for s in sims]
                extra_context = "\nRelevant prior findings:\n" + "\n".join(lines)
        except Exception:
            # If supermemory isn't available, continue without it
            extra_context = ""

        # Ask LLM to interpret the follow-up
        interpretation = call_llm_json(
            prompt=f"""Prior analysis targeted these regions: {prior_plan.get('target_regions', [])}
{extra_context}
The user asks: "{followup_prompt}"

Return JSON: {{"target_regions": ["City, ST", ...], "updated_budget": "<budget or null>", "updated_instructions": "<instructions or null>"}}
Only include regions the user wants analysed. If they want to keep the same regions, return the same list.""",
            system_prompt="You interpret follow-up investment queries. Output strict JSON only.",
            temperature=0.1,
        )
        target_regions = interpretation.get("target_regions", prior_plan.get("target_regions", []))
        if interpretation.get("updated_budget"):
            budget = interpretation["updated_budget"]
        if interpretation.get("updated_instructions"):
            instructions = interpretation["updated_instructions"]

    # Fetch data + run analysts + conclude (same flow as main pipeline)
    market_data = fetch_all_market_data(target_regions)
    save(session_id, "market_data_followup", market_data)

    analyst_inputs = []
    for region in target_regions:
        region_data = market_data.get(region, {})
        summary = region_data.get("summary", "No market data available.")
        analyst_inputs.append((region, budget, summary, instructions, session_id, goals))

    analyst_reports = list(analyze_region.starmap(analyst_inputs))
    analyst_reports.sort(
        key=lambda r: r.get("investment_score", {}).get("total", 0),
        reverse=True,
    )

    conclusion = conclude.remote(
        user_prompt=f"{user_prompt}\n\nFollow-up: {followup_prompt}",
        analyst_reports=analyst_reports,
        plan_context={**prior_plan, "client_budget": budget},
        session_id=session_id,
    )

    followup_output = {
        "session_id": session_id,
        "followup_prompt": followup_prompt,
        "target_regions": target_regions,
        "analyst_reports": analyst_reports,
        "conclusion": conclusion,
    }

    save(session_id, "followup_result", followup_output)
    emit_event(session_id, {
        "event": "followup_complete",
        "session_id": session_id,
    })

    return followup_output
