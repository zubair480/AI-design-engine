"""
Planner Agent — The Architect.

Analyzes a client's investment request, extracts budget and goals,
and breaks the geography into 3-5 specific target regions for parallel
Analyst agents to investigate.

Input:  Free-text investment objective
Output: Structured JSON with budget, goals, target_regions, analyst_instructions
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import modal
from config import app, sim_image


# ═══════════════════════════════════════════════════════════════════════════
# System Prompt — forces strict JSON output with geographic targets
# ═══════════════════════════════════════════════════════════════════════════

PLANNER_SYSTEM_PROMPT = """You are the Lead Strategist for a real estate investment firm. Your job is to analyze a client's investment request and break it down into 10-20 smaller geographic regions for your local analysts to investigate.

You must output your response in strict JSON format. Do not include introductory text.

Required JSON structure:
{
  "client_budget": "<Extracted budget as a string, e.g. '$500,000'. If not stated, write 'Not specified'>",
  "investment_goals": ["<goal 1, e.g. 'cash flow'>", "<goal 2, e.g. 'appreciation'>"],
  "property_types": ["<type 1, e.g. 'single-family rental'>", "<type 2, e.g. 'multi-family'>"],
  "target_regions": [
    "<City 1, ST>",
    "<City 2, ST>",
    "<City 3, ST>"
  ],
  "analyst_instructions": "<Specific metrics and questions the local analysts must evaluate, tailored to this particular request. Be detailed.>",
  "time_horizon": "<short-term (1-3 yr) | medium-term (3-7 yr) | long-term (7+ yr)>",
  "risk_tolerance": "<conservative | moderate | aggressive>"
}

Rules:
1. target_regions MUST contain 5 to 20 specific cities formatted as "City, ST" (two-letter state code).
2. Choose cities that fall within or logically relate to the user's requested area.
3. Pick cities that represent DIVERSE sub-markets (mix of urban, suburban, college town, etc.) so the comparison is meaningful.
4. analyst_instructions should reference the client's specific budget, goals, and property preferences.
5. If the user does not specify a budget, estimate a reasonable one and note it.
6. If the user asks about a single city, expand to that city plus 5-6 nearby alternatives for comparison.
7. If the user asks about a state or broad region, pick the 5-20 most promising metro areas.
8. investment_goals should be inferred from context if not explicitly stated."""


@app.function(image=sim_image, timeout=600)
def plan(user_prompt: str, session_id: str | None = None) -> dict[str, Any]:
    """
    Break down an investment request into geographic targets.

    Args:
        user_prompt: Free-text investment objective from the client.
        session_id: Optional session ID. Generated if not provided.

    Returns:
        Dict with: session_id, client_budget, investment_goals, target_regions,
                    analyst_instructions, time_horizon, risk_tolerance
    """
    from llm.client import call_llm_json
    from memory.store import save, emit_event, set_status

    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    set_status(session_id, "planning", 0.0, "Analyzing investment request...")

    # Call LLM to decompose the request into geographic targets
    result = call_llm_json(
        prompt=f"Client request: {user_prompt}",
        system_prompt=PLANNER_SYSTEM_PROMPT,
        temperature=0.2,
    )

    # Validate and normalize
    target_regions = result.get("target_regions", [])
    if not target_regions:
        result["target_regions"] = ["Unknown Region"]

    # Ensure regions are clean strings
    target_regions = [str(r).strip() for r in result.get("target_regions", []) if r]

    plan_output = {
        "session_id": session_id,
        "user_prompt": user_prompt,
        "client_budget": result.get("client_budget", "Not specified"),
        "investment_goals": result.get("investment_goals", ["cash flow", "appreciation"]),
        "property_types": result.get("property_types", ["single-family rental"]),
        "target_regions": target_regions,
        "analyst_instructions": result.get(
            "analyst_instructions",
            "Evaluate market feasibility, investment risk, and projected 5-year ROI.",
        ),
        "time_horizon": result.get("time_horizon", "medium-term (3-7 yr)"),
        "risk_tolerance": result.get("risk_tolerance", "moderate"),
    }

    # Persist to shared memory
    save(session_id, "plan", plan_output)
    emit_event(session_id, {
        "event": "plan_complete",
        "session_id": session_id,
        "num_regions": len(target_regions),
        "regions": target_regions,
        "budget": plan_output["client_budget"],
    })
    set_status(
        session_id, "planning", 1.0,
        f"Plan ready: {len(target_regions)} regions targeted",
    )

    return plan_output
