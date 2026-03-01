"""
Evaluation Agent — Scores simulation outcomes and produces final recommendations.

Takes simulation results + research findings, computes business metrics,
and uses LLM reasoning to generate an executive summary.
"""

from __future__ import annotations

import json
from typing import Any

import modal
from config import app, sim_image


EVAL_SYSTEM_PROMPT = """"You are an expert Hyper-Local Real Estate Analyst for __REGION__.
.

Given:
- Monte Carlo simulation statistics (profit distribution, risk metrics, ROI)
- Research data (demographics, foot traffic, competitive landscape)

Produce a JSON response with this schema:
{
  "executive_summary": "<2-3 paragraph summary of findings and recommendation>",
  "recommendation": "strong_go | cautious_go | conditional | do_not_proceed",
  "confidence_level": "<high | medium | low>",
  "key_findings": [
    "<finding 1>",
    "<finding 2>",
    "<finding 3>"
  ],
  "pricing_strategy": {
    "recommended_avg_price": <float>,
    "reasoning": "<why this price point>"
  },
  "location_recommendation": {
    "best_area": "<area description>",
    "reasoning": "<why>"
  },
  "risk_mitigation": [
    "<risk 1 and how to mitigate>",
    "<risk 2 and how to mitigate>"
  ],
  "break_even_estimate_months": <int>,
  "three_year_outlook": "<description of 3-year scenario>"
}

Be specific with numbers. Reference the simulation data directly. Do not be vague."""


@app.function(image=sim_image, timeout=600)
def evaluate(session_id: str) -> dict[str, Any]:
    """
    Evaluate simulation results and produce a final strategic recommendation.

    Args:
        session_id: Session identifier. Reads simulation + research from memory.

    Returns:
        Complete evaluation with metrics, LLM analysis, and recommendation.
    """
    from memory.store import load, save, emit_event, set_status
    from llm.client import call_llm_json

    set_status(session_id, "evaluating", 0.0, "Analyzing simulation results...")

    # Load prior results from shared memory
    sim_results = load(session_id, "simulation", {})
    demographics = load(session_id, "research:demographics", {})
    foot_traffic = load(session_id, "research:foot_traffic", {})
    competitors = load(session_id, "research:competitor_analysis", {})

    emit_event(session_id, {
        "event": "evaluation_started",
        "inputs": ["simulation", "demographics", "foot_traffic", "competitors"],
    })

    # ---- Compute quantitative metrics ----
    profit = sim_results.get("profit", {})
    risk = sim_results.get("risk", {})
    revenue = sim_results.get("revenue", {})
    cost = sim_results.get("cost", {})
    roi = sim_results.get("roi", {})

    initial_investment = sim_results.get("parameters_used", {}).get("initial_investment", 150000)

    # Break-even analysis
    monthly_profit = profit.get("mean", 0) / 12
    break_even_months = (
        round(initial_investment / monthly_profit) if monthly_profit > 0 else 999
    )

    # Sharpe-like ratio (risk-adjusted return)
    profit_std = profit.get("std", 1)
    sharpe = round(profit.get("mean", 0) / profit_std, 3) if profit_std > 0 else 0

    # Probability of achieving target ROI (>20%)
    target_profit = initial_investment * 0.20
    # Approximate using normal distribution
    from math import erf, sqrt
    z = (target_profit - profit.get("mean", 0)) / (profit_std if profit_std > 0 else 1)
    prob_target_roi = round((1 - 0.5 * (1 + erf(z / sqrt(2)))) * 100, 2)

    quantitative_metrics = {
        "expected_annual_profit": profit.get("mean", 0),
        "median_annual_profit": profit.get("median", 0),
        "profit_std": profit_std,
        "p10_profit_worst_case": profit.get("p10", 0),
        "p90_profit_best_case": profit.get("p90", 0),
        "expected_annual_revenue": revenue.get("mean", 0),
        "expected_annual_cost": cost.get("mean", 0),
        "mean_roi_pct": roi.get("mean_pct", 0),
        "probability_of_loss_pct": risk.get("prob_loss", 0),
        "value_at_risk_p10": risk.get("var_10", 0),
        "break_even_months": break_even_months,
        "sharpe_ratio": sharpe,
        "prob_20pct_roi": prob_target_roi,
        "initial_investment": initial_investment,
    }

    set_status(session_id, "evaluating", 0.5, "Generating strategic analysis...")

    # ---- LLM strategic analysis ----
    analysis_prompt = f"""Analyze the following business simulation results and produce a strategic recommendation.

## Simulation Results ({sim_results.get('total_scenarios', 0)} Monte Carlo scenarios)
- Expected Annual Profit: ${profit.get('mean', 0):,.0f}
- Profit Std Dev: ${profit_std:,.0f}
- 10th Percentile (worst case): ${profit.get('p10', 0):,.0f}
- 90th Percentile (best case): ${profit.get('p90', 0):,.0f}
- Probability of Loss: {risk.get('prob_loss', 0):.1f}%
- Mean ROI: {roi.get('mean_pct', 0):.1f}%
- Break-even Estimate: {break_even_months} months
- Initial Investment: ${initial_investment:,.0f}

## Revenue & Cost
- Expected Annual Revenue: ${revenue.get('mean', 0):,.0f}
- Expected Annual Cost: ${cost.get('mean', 0):,.0f}

## Market Research
- Target Market: {demographics.get('target_demographic', 'general')}
- Total Population in Area: {demographics.get('total_population', 'N/A')}
- Median Income: ${demographics.get('median_income', 0):,}
- Student Population %: {demographics.get('avg_student_pct', 0):.1%}
- Best Location: {foot_traffic.get('best_location', 'N/A')}
- Daily Foot Traffic: {foot_traffic.get('estimated_daily_foot_traffic_mean', 'N/A')}
- Competitors Nearby: {competitors.get('nearby_competitors', 'N/A')}
- Market Saturation: {competitors.get('market_saturation', 'N/A')}
- Avg Competitor Rating: {competitors.get('avg_competitor_rating', 'N/A')}"""

    llm_analysis = call_llm_json(
        prompt=analysis_prompt,
        system_prompt=EVAL_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=2048,
    )

    # ---- Combine everything ----
    evaluation = {
        "session_id": session_id,
        "quantitative_metrics": quantitative_metrics,
        "llm_analysis": llm_analysis,
        "simulation_summary": {
            "total_scenarios": sim_results.get("total_scenarios", 0),
            "elapsed_seconds": sim_results.get("elapsed_seconds", 0),
            "num_containers": sim_results.get("num_containers", 0),
        },
        "histogram": sim_results.get("histogram", {}),
    }

    # Persist
    save(session_id, "evaluation", evaluation)
    save(session_id, "final", evaluation)

    emit_event(session_id, {
        "event": "evaluation_complete",
        "recommendation": llm_analysis.get("recommendation", "unknown"),
        "expected_profit": profit.get("mean", 0),
        "roi_pct": roi.get("mean_pct", 0),
        "prob_loss": risk.get("prob_loss", 0),
    })
    set_status(session_id, "complete", 1.0, "Analysis complete")

    return evaluation
