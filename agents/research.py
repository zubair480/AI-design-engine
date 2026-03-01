"""
Research Agent — Analyzes synthetic demographic, foot traffic, and competitor data.

Runs in parallel across multiple research subtasks. Each call loads the
relevant dataset and produces structured quantitative findings.
"""

from __future__ import annotations

import json
from typing import Any

import modal
from config import app, sim_image


# ---------------------------------------------------------------------------
# Embedded data loaders (datasets bundled into the container image)
# ---------------------------------------------------------------------------

def _load_csv(filename: str) -> list[dict]:
    """Load a CSV file from the bundled data directory."""
    import csv
    import os
    # Try multiple paths for the data files
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
        os.path.join("/data", filename),
        filename,
    ]
    for path in possible_paths:
        if os.path.exists(path):
            for enc in ("utf-8-sig", "latin-1"):
                try:
                    with open(path, "r", encoding=enc, newline="") as f:
                        return list(csv.DictReader(f))
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError("csv", b"", 0, 1, f"Unsupported encoding for {filename}")
    raise FileNotFoundError(f"Dataset not found: {filename}")


def _analyze_demographics() -> dict[str, Any]:
    """Analyze demographic data and return summary statistics."""
    import statistics

    rows = _load_csv("demographics.csv")
    populations = [int(r["population"]) for r in rows]
    incomes = [int(r["median_income"]) for r in rows]
    ages = [float(r["median_age"]) for r in rows]
    student_pcts = [float(r["pct_students"]) for r in rows]
    densities = [int(r["housing_density"]) for r in rows]

    # Identify high-potential tracts (high population + high student %)
    high_potential = [
        r for r in rows
        if int(r["population"]) > 4000 and float(r["pct_students"]) > 0.25
    ]

    return {
        "total_tracts": len(rows),
        "total_population": sum(populations),
        "avg_population": round(statistics.mean(populations)),
        "median_income": round(statistics.median(incomes)),
        "avg_median_age": round(statistics.mean(ages), 1),
        "avg_student_pct": round(statistics.mean(student_pcts), 3),
        "avg_housing_density": round(statistics.mean(densities)),
        "high_potential_tracts": len(high_potential),
        "high_potential_ids": [r["tract_id"] for r in high_potential[:5]],
        "income_range": {"min": min(incomes), "max": max(incomes)},
        "target_demographic": "college students and young professionals" if statistics.mean(student_pcts) > 0.15 else "general population",
    }


def _analyze_foot_traffic() -> dict[str, Any]:
    """Analyze foot traffic patterns across candidate locations."""
    import statistics

    rows = _load_csv("foot_traffic.csv")

    # Group by location
    locations: dict[str, list[int]] = {}
    peak_hours: dict[str, dict[int, list[int]]] = {}
    for r in rows:
        loc = r["location_id"]
        avg = int(r["avg_pedestrians"])
        hour = int(r["hour"])
        locations.setdefault(loc, []).append(avg)
        peak_hours.setdefault(loc, {}).setdefault(hour, []).append(avg)

    # Rank locations by total traffic
    loc_totals = {loc: sum(vals) for loc, vals in locations.items()}
    ranked = sorted(loc_totals.items(), key=lambda x: -x[1])

    best_loc = ranked[0][0]
    best_hourly = peak_hours[best_loc]
    peak_hour = max(best_hourly.items(), key=lambda x: statistics.mean(x[1]))

    # Daily average for best location
    daily_avg = round(loc_totals[best_loc] / 7)  # 7 days in data

    return {
        "total_locations_analyzed": len(locations),
        "best_location": best_loc,
        "best_location_weekly_traffic": loc_totals[best_loc],
        "best_location_daily_avg": daily_avg,
        "peak_hour": peak_hour[0],
        "peak_hour_avg_traffic": round(statistics.mean(peak_hour[1])),
        "location_ranking": [{"id": loc, "weekly_total": total} for loc, total in ranked[:5]],
        "estimated_daily_foot_traffic_mean": daily_avg,
        "estimated_daily_foot_traffic_std": round(daily_avg * 0.25),
    }


def _analyze_competitors() -> dict[str, Any]:
    """Analyze competitive landscape."""
    import statistics

    rows = _load_csv("competitors.csv")
    ratings = [float(r["avg_rating"]) for r in rows]
    revenues = [int(r["est_daily_revenue"]) for r in rows]
    distances = [float(r["distance_km"]) for r in rows]

    nearby = [r for r in rows if float(r["distance_km"]) < 2.0]
    price_tiers = {}
    for r in rows:
        tier = r["price_tier"]
        price_tiers[tier] = price_tiers.get(tier, 0) + 1

    return {
        "total_competitors": len(rows),
        "nearby_competitors": len(nearby),
        "avg_competitor_rating": round(statistics.mean(ratings), 2),
        "avg_competitor_daily_revenue": round(statistics.mean(revenues)),
        "median_distance_km": round(statistics.median(distances), 2),
        "price_tier_distribution": price_tiers,
        "market_saturation": "high" if len(nearby) > 8 else "moderate" if len(nearby) > 4 else "low",
        "competitive_gap": "premium quality" if statistics.mean(ratings) < 4.0 else "price or convenience",
        "top_competitors": [
            {"name": r["name"], "rating": float(r["avg_rating"]), "distance_km": float(r["distance_km"])}
            for r in sorted(rows, key=lambda x: -float(x["avg_rating"]))[:5]
        ],
    }


# ---------------------------------------------------------------------------
# Modal function
# ---------------------------------------------------------------------------

@app.function(image=sim_image, timeout=600)
def research(subtask_id: str, session_id: str, params: dict | None = None) -> dict[str, Any]:
    """
    Execute a single research subtask.

    Args:
        subtask_id: One of 'demographics', 'foot_traffic', 'competitor_analysis'
        session_id: Session identifier for memory storage.
        params: Optional parameters from the planner.

    Returns:
        Research findings dict.
    """
    from memory.store import save, emit_event

    emit_event(session_id, {
        "event": "research_started",
        "subtask_id": subtask_id,
    })

    # Route to the appropriate analyzer
    analyzers = {
        "demographics": _analyze_demographics,
        "foot_traffic": _analyze_foot_traffic,
        "competitor_analysis": _analyze_competitors,
    }

    analyzer = analyzers.get(subtask_id)
    if analyzer is None:
        # For unrecognized subtasks, use LLM to generate analysis
        from llm.client import call_llm_json
        result = call_llm_json(
            prompt=f"Provide quantitative analysis for: {subtask_id}. Include realistic numbers and ranges.",
            system_prompt="You are a business research analyst. Output JSON with numeric metrics.",
        )
    else:
        result = analyzer()

    # Add metadata
    result["_subtask_id"] = subtask_id
    result["_session_id"] = session_id

    # Persist to memory
    save(session_id, f"research:{subtask_id}", result)

    # Also write a lightweight embedding summary to the supermemory (optional)
    try:
        from memory.store import save_embedding

        # Build a short textual summary for vector storage
        summary_parts = []
        for k, v in result.items():
            if k.startswith("_"):
                continue
            # Keep small pieces only
            if isinstance(v, (str, int, float)):
                summary_parts.append(f"{k}: {v}")
        summary_text = " | ".join(summary_parts[:10])[:1000]
        save_embedding(session_id, f"research:{subtask_id}", summary_text, metadata={"subtask": subtask_id})
    except Exception:
        # Embeddings are optional — failure must not break the research flow
        pass

    emit_event(session_id, {
        "event": "research_complete",
        "subtask_id": subtask_id,
        "summary": {k: v for k, v in result.items() if not k.startswith("_")},
    })

    return result
