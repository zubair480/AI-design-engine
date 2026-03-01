"""
Conclusion Agent — The Senior Wealth Advisor.

Receives all Analyst reports, ranks the regions by Investment Score,
and synthesises a final, client-facing recommendation.

Input:  Original user prompt + list of Analyst report dicts
Output: Polished advisory memo with ranked regions and clear recommendation
"""

from __future__ import annotations

import json
from typing import Any

import modal
from config import app, sim_image


# ═══════════════════════════════════════════════════════════════════════════
# System prompt — {user_prompt} and {analyst_reports} injected at runtime
# ═══════════════════════════════════════════════════════════════════════════

CONCLUSION_SYSTEM_PROMPT = """You are a Senior Wealth Advisor at a premier real estate investment firm. A client asked:

"__USER_PROMPT__"

Your team of local analysts has provided the following deep-dive reports and scores for various sub-regions:

__ANALYST_REPORTS__

Your job is to synthesize this data into a final, highly readable recommendation for the client.

You must:
1. Rank the regions by their total Investment Score (highest first).
2. Explain why the winning region is the best place to deploy the client's capital — reference the specific numbers.
3. For the runner-up region(s), briefly explain what makes them attractive or why they fell short.
4. Highlight the top 3 risks the client should be aware of across ALL regions.
5. Provide a concrete "Next Steps" action plan (e.g., "Visit the market", "Engage a local agent", "Run deeper due diligence on X").

Style rules:
- Speak directly to the client in a professional, confident, and advisory tone.
- Do NOT mention that you are an AI or that you are reading "analyst reports". Present this as your firm's comprehensive findings.
- Use dollar amounts and percentages — be specific, not vague.
- Keep the total response between 400-700 words.

Output strict JSON with this schema:
{
  "executive_summary": "<3-4 sentence high-level summary>",
  "ranked_regions": [
    {
      "rank": 1,
      "region": "<region name>",
      "score": <total score out of 100>,
      "score_breakdown": {"risk": <int>, "roi_potential": <int>, "feasibility": <int>},
      "headline": "<one-sentence why this region wins or loses>",
      "monthly_cash_flow_est": <int or null>,
      "five_year_return_est_pct": <float or null>
    }
  ],
  "recommendation": "<strong_buy | buy | hold | avoid>",
  "recommended_region": "<name of the #1 region>",
  "recommended_strategy": "<2-3 sentences: what to buy, at what price, expected returns>",
  "top_risks": [
    "<risk 1 with mitigation>",
    "<risk 2 with mitigation>",
    "<risk 3 with mitigation>"
  ],
  "next_steps": [
    "<step 1>",
    "<step 2>",
    "<step 3>"
  ],
  "full_advisory_memo": "<The complete 400-700 word advisory memo, written in first-person plural advisory voice (Our team..., We recommend...). Use line breaks for readability. it's statement not an email>"
}"""


@app.function(image=sim_image, timeout=600)
def conclude(
    user_prompt: str,
    analyst_reports: list[dict[str, Any]],
    plan_context: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    """
    Synthesise all Analyst reports into a final client recommendation.

    Args:
        user_prompt:     The original client request.
        analyst_reports: List of Analyst output dicts (one per region).
        plan_context:    The Planner output (budget, goals, etc.).
        session_id:      Session identifier.

    Returns:
        Final advisory dict with ranked regions, recommendation, and memo.
    """
    from llm.client import call_llm_json
    from memory.store import save, emit_event, set_status

    set_status(session_id, "concluding", 0.0, "Synthesising analyst findings...")

    emit_event(session_id, {
        "event": "conclusion_started",
        "num_reports": len(analyst_reports),
    })

    # ── Build the analyst reports text block ────────────────────────────
    reports_text = _format_analyst_reports(analyst_reports)

    system_prompt = (
        CONCLUSION_SYSTEM_PROMPT
        .replace("__USER_PROMPT__", user_prompt)
        .replace("__ANALYST_REPORTS__", reports_text)
    )

    # Brief reinforcement prompt
    budget = plan_context.get("client_budget", "Not specified")
    goals = ", ".join(plan_context.get("investment_goals", []))
    conclusion_prompt = (
        f"The client's budget is {budget} and their goals are: {goals}.\n"
        f"Please provide your final ranked recommendation across all {len(analyst_reports)} regions."
    )

    result = call_llm_json(
        prompt=conclusion_prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=4096,
    )

    # Ensure ranked_regions is sorted by score descending
    ranked = result.get("ranked_regions", [])
    if ranked:
        ranked = sorted(ranked, key=lambda r: r.get("score", 0), reverse=True)
        for i, r in enumerate(ranked):
            r["rank"] = i + 1
        result["ranked_regions"] = ranked

    # Persist
    save(session_id, "conclusion", result)
    emit_event(session_id, {
        "event": "conclusion_complete",
        "session_id": session_id,
        "recommendation": result.get("recommendation", "unknown"),
        "recommended_region": result.get("recommended_region", "unknown"),
    })
    set_status(session_id, "complete", 1.0, "Analysis complete")

    return result


def _format_analyst_reports(reports: list[dict[str, Any]]) -> str:
    """
    Convert the list of analyst dicts into a readable text block
    that gets injected into the Conclusion agent's system prompt.
    """
    sections = []

    for i, report in enumerate(reports, 1):
        region = report.get("region", f"Region {i}")
        score = report.get("investment_score", {})
        roi = report.get("projected_roi", {})
        risk = report.get("investment_risk", {})
        feasibility = report.get("market_feasibility", {})

        lines = [
            f"--- ANALYST REPORT #{i}: {region} ---",
            f"Investment Score: {score.get('total', 'N/A')}/100 "
            f"(Risk: {score.get('risk', '?')}/20, "
            f"ROI: {score.get('roi_potential', '?')}/50, "
            f"Feasibility: {score.get('feasibility', '?')}/30)",
            "",
        ]

        # Market feasibility
        if feasibility:
            lines.append(f"Market Assessment: {feasibility.get('summary', 'N/A')}")
            lines.append(f"  Price Level: {feasibility.get('median_price_assessment', 'N/A')}")
            lines.append(f"  Trend: {feasibility.get('market_trend', 'N/A')}")
            lines.append(f"  Best Property: {feasibility.get('best_property_type', 'N/A')}")
            lines.append(f"  Budget Range: {feasibility.get('price_range_for_budget', 'N/A')}")
            lines.append("")

        # ROI projections
        if roi:
            lines.append(f"Projected ROI: {roi.get('summary', 'N/A')}")
            lines.append(f"  Monthly Rent: ${roi.get('estimated_monthly_rent', 'N/A')}")
            lines.append(f"  Monthly Expenses: ${roi.get('estimated_monthly_expenses', 'N/A')}")
            lines.append(f"  Monthly Cash Flow: ${roi.get('estimated_monthly_cash_flow', 'N/A')}")
            lines.append(f"  Cash-on-Cash Return: {roi.get('annual_cash_on_cash_return_pct', 'N/A')}%")
            lines.append(f"  5-Year Appreciation: {roi.get('projected_5yr_appreciation_pct', 'N/A')}%")
            lines.append(f"  5-Year Total Return: {roi.get('projected_5yr_total_return_pct', 'N/A')}%")
            lines.append("")

        # Risk
        if risk:
            lines.append(f"Risk Assessment: {risk.get('summary', 'N/A')}")
            drivers = risk.get("economic_drivers", [])
            if drivers:
                lines.append(f"  Economic Drivers: {', '.join(drivers)}")
            key_risks = risk.get("key_risks", [])
            if key_risks:
                lines.append(f"  Key Risks: {', '.join(key_risks)}")
            lines.append(f"  Vacancy Risk: {risk.get('vacancy_risk', 'N/A')}")
            lines.append("")

        # Advantages / disadvantages
        advs = report.get("local_advantages", [])
        disadvs = report.get("local_disadvantages", [])
        if advs:
            lines.append(f"Advantages: {'; '.join(advs)}")
        if disadvs:
            lines.append(f"Disadvantages: {'; '.join(disadvs)}")

        verdict = report.get("one_line_verdict", "")
        if verdict:
            lines.append(f"Analyst Verdict: {verdict}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)
