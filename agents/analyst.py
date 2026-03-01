"""
Analyst Agent — The Swarm.

Each instance is a Hyper-Local Real Estate Analyst for one specific region.
The orchestrator spins up N of these in parallel (one per target region).

Input:  Region name, client budget, live market data (injected by Python),
        and analyst instructions from the Planner.
Output: Structured analysis with a standardised Investment Score out of 100,
        broken into Risk (0-20), ROI Potential (0-50), Feasibility (0-30).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import modal
from config import app, sim_image


# ═══════════════════════════════════════════════════════════════════════════
# System prompt template — {region}, {budget}, {market_data}, {instructions}
# are filled dynamically by the orchestrator before each call.
# ═══════════════════════════════════════════════════════════════════════════

ANALYST_SYSTEM_PROMPT = """You are an expert Hyper-Local Real Estate Analyst for __REGION__.

You have been handed an investment budget of __BUDGET__ and the following live market data for your region:

__MARKET_DATA__

Your job is to analyze this specific region based on the data provided and the instructions below.

Analyst Instructions from Lead Strategist:
__INSTRUCTIONS__

You must evaluate:

1. **Market Feasibility & Current Pricing**: Are property prices reasonable? Is the market trending up or down? What type of property best fits the budget?

2. **Investment Risk**: What are the economic drivers? Is the area dependent on one employer or industry? What is the vacancy risk? Are there regulatory red flags?

3. **Projected 5-Year ROI**: Based on the pricing and rental data, project both cash-flow returns (monthly rental income minus expenses) and appreciation returns. Be specific with numbers.

4. **Local Advantages & Disadvantages**: What makes this region uniquely attractive or risky compared to other markets?

CRITICAL: You must conclude your analysis with a standardised "Investment Score" out of 100 points, broken down as follows:
- **Risk Score** (0 to 20): Higher = LESS risky. 20 = extremely safe, 0 = extremely risky.
- **ROI Potential** (0 to 50): Higher = better return potential. 50 = exceptional ROI, 0 = no ROI.
- **Feasibility** (0 to 30): Higher = more feasible given the budget and goals. 30 = perfect fit, 0 = impossible.

Be RUTHLESS. If the numbers don't make sense for this budget and these goals, score it low. Do not inflate scores to be polite.

Output your response as strict JSON with this schema:
{
  "region": "<region name>",
  "market_feasibility": {
    "summary": "<2-3 sentence overview>",
    "median_price_assessment": "<cheap | fair | overpriced>",
    "market_trend": "<appreciating | stable | declining>",
    "best_property_type": "<e.g. single-family, duplex, condo>",
    "price_range_for_budget": "<realistic price range this budget can target>"
  },
  "investment_risk": {
    "summary": "<2-3 sentence overview>",
    "economic_drivers": ["<driver 1>", "<driver 2>"],
    "key_risks": ["<risk 1>", "<risk 2>"],
    "vacancy_risk": "<low | moderate | high>",
    "overall_risk_level": "<low | moderate | high>"
  },
  "projected_roi": {
    "summary": "<2-3 sentence overview>",
    "estimated_monthly_rent": <int>,
    "estimated_monthly_expenses": <int>,
    "estimated_monthly_cash_flow": <int>,
    "annual_cash_on_cash_return_pct": <float>,
    "projected_5yr_appreciation_pct": <float>,
    "projected_5yr_total_return_pct": <float>
  },
  "local_advantages": ["<advantage 1>", "<advantage 2>"],
  "local_disadvantages": ["<disadvantage 1>", "<disadvantage 2>"],
  "investment_score": {
    "risk": <int 0-20>,
    "roi_potential": <int 0-50>,
    "feasibility": <int 0-30>,
    "total": <int 0-100>
  },
  "one_line_verdict": "<Single sentence: should the client invest here or not?>"
}"""


@app.function(image=sim_image, timeout=600)
def analyze_region(
    region: str,
    budget: str,
    market_data_summary: str,
    analyst_instructions: str,
    session_id: str,
    investment_goals: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run deep-dive analysis on a single region.

    Called in parallel by the orchestrator — one container per region.

    Args:
        region:              e.g. "Carbondale, IL"
        budget:              e.g. "$500,000"
        market_data_summary: Human-readable market data block from data/market_data.py
        analyst_instructions: Instructions from the Planner agent
        session_id:          Session identifier
        investment_goals:    e.g. ["cash flow", "appreciation"]

    Returns:
        Analyst report dict with Investment Score.
    """
    from llm.client import call_llm_json
    from memory.store import save, emit_event

    emit_event(session_id, {
        "event": "analyst_started",
        "region": region,
    })

    # Build the system prompt with injected context (use replace to avoid
    # collisions with JSON curly braces in the template)
    system_prompt = (
        ANALYST_SYSTEM_PROMPT
        .replace("__REGION__", region)
        .replace("__BUDGET__", budget)
        .replace("__MARKET_DATA__", market_data_summary)
        .replace("__INSTRUCTIONS__", analyst_instructions)
    )

    # The user-facing prompt reinforces what we want
    goals_str = ", ".join(investment_goals) if investment_goals else "cash flow and appreciation"
    user_prompt = (
        f"Analyze {region} as a real estate investment opportunity.\n"
        f"Client budget: {budget}\n"
        f"Investment goals: {goals_str}\n"
        f"Provide your analysis and Investment Score."
    )

    result = call_llm_json(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=4096,
    )

    # Validate investment score structure
    score = result.get("investment_score", {})
    if not isinstance(score, dict):
        score = {}

    risk = _clamp(score.get("risk", 10), 0, 20)
    roi = _clamp(score.get("roi_potential", 25), 0, 50)
    feasibility = _clamp(score.get("feasibility", 15), 0, 30)
    total = risk + roi + feasibility

    result["investment_score"] = {
        "risk": risk,
        "roi_potential": roi,
        "feasibility": feasibility,
        "total": total,
    }
    result["region"] = region

    # Persist per-region analysis
    save(session_id, f"analyst:{region}", result)
    emit_event(session_id, {
        "event": "analyst_complete",
        "region": region,
        "score": total,
        "risk": risk,
        "roi_potential": roi,
        "feasibility": feasibility,
    })

    return result


def _clamp(value, lo, hi):
    """Clamp a numeric value to [lo, hi], handling non-numeric inputs."""
    try:
        v = int(float(value))
    except (ValueError, TypeError):
        v = (lo + hi) // 2  # midpoint fallback
    return max(lo, min(hi, v))
