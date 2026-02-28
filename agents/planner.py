"""
Planner Agent — Decomposes a user objective into a directed acyclic graph (DAG)
of parallelizable subtasks.

Input:  Free-text business objective (e.g. "Design a profitable coffee shop in Urbana")
Output: Structured task graph with dependency edges, stored in shared memory.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import modal
from config import app, sim_image


PLANNER_SYSTEM_PROMPT = """You are a strategic business planning AI. Given a user's business objective, decompose it into concrete, quantifiable subtasks that can be executed by specialist agents.

You MUST output valid JSON matching this exact schema:

{
  "objective": "<restated objective>",
  "business_type": "<type of business, e.g. coffee_shop, warehouse, food_truck>",
  "location": "<target location if mentioned>",
  "subtasks": [
    {
      "id": "<unique snake_case id>",
      "type": "research | simulation | evaluation",
      "title": "<human-readable title>",
      "description": "<what this task does>",
      "depends_on": ["<id of prerequisite task>"],
      "params": {}
    }
  ]
}

Rules:
1. Always include these research tasks: demographics, foot_traffic, competitor_analysis
2. Always include these simulation tasks: revenue_simulation, cost_modeling
3. Always include an evaluation task: risk_analysis (depends on simulations)
4. Research tasks have NO dependencies (they run in parallel)
5. Simulation tasks depend on relevant research tasks
6. Evaluation depends on simulation tasks
7. Keep subtasks to 5-8 total for efficiency
8. Each subtask must have a unique id"""


@app.function(image=sim_image, timeout=600)
def plan(user_prompt: str, session_id: str | None = None) -> dict[str, Any]:
    """
    Break a user objective into a task DAG.

    Args:
        user_prompt: The raw business objective from the user.
        session_id: Optional session ID. Generated if not provided.

    Returns:
        Dict with keys: session_id, objective, subtasks, execution_waves
    """
    from llm.client import call_llm_json
    from memory.store import save, emit_event, set_status

    if session_id is None:
        session_id = uuid.uuid4().hex[:12]

    set_status(session_id, "planning", 0.0, "Analyzing objective...")

    # Call LLM to generate task DAG
    result = call_llm_json(
        prompt=f"Business objective: {user_prompt}",
        system_prompt=PLANNER_SYSTEM_PROMPT,
        temperature=0.2,
    )

    # Validate and normalize the plan
    subtasks = result.get("subtasks", [])
    task_ids = {t["id"] for t in subtasks}

    for task in subtasks:
        # Ensure depends_on references exist
        task["depends_on"] = [d for d in task.get("depends_on", []) if d in task_ids]
        task.setdefault("params", {})

    # Topological sort into execution waves (groups of parallelizable tasks)
    waves = _compute_waves(subtasks)

    plan_output = {
        "session_id": session_id,
        "objective": result.get("objective", user_prompt),
        "business_type": result.get("business_type", "unknown"),
        "location": result.get("location", "unknown"),
        "subtasks": subtasks,
        "execution_waves": waves,
    }

    # Persist plan to shared memory
    save(session_id, "plan", plan_output)
    emit_event(session_id, {
        "event": "plan_complete",
        "session_id": session_id,
        "objective": plan_output["objective"],
        "num_tasks": len(subtasks),
        "num_waves": len(waves),
        "tasks": [{"id": t["id"], "title": t["title"], "type": t["type"]} for t in subtasks],
    })
    set_status(session_id, "planning", 1.0, f"Plan ready: {len(subtasks)} tasks in {len(waves)} waves")

    return plan_output


def _compute_waves(subtasks: list[dict]) -> list[list[str]]:
    """
    Topologically sort tasks into execution waves.

    Wave N contains all tasks whose dependencies are fully in waves 0..N-1.
    Tasks in the same wave can run in parallel.
    """
    task_map = {t["id"]: t for t in subtasks}
    completed: set[str] = set()
    waves: list[list[str]] = []

    remaining = set(task_map.keys())
    while remaining:
        # Find all tasks whose deps are satisfied
        wave = [
            tid for tid in remaining
            if all(d in completed for d in task_map[tid].get("depends_on", []))
        ]
        if not wave:
            # Circular dependency — break it by forcing remaining into one wave
            wave = list(remaining)
        waves.append(sorted(wave))
        completed.update(wave)
        remaining -= set(wave)

    return waves
