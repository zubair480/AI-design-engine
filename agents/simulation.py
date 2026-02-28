"""
Simulation Agent — The heavy compute centerpiece.

Runs Monte Carlo simulations to model business profitability.
Launches 100 parallel containers, each running a batch of 50 scenarios,
producing 5,000 total simulations.

This is what produces: "5,000 simulations in 12 seconds using parallel workers."
"""

from __future__ import annotations

import json
import time
from typing import Any

import modal
from config import app, sim_image, results_vol, SIM_NUM_SCENARIOS, SIM_BATCH_SIZE, SIM_NUM_BATCHES


# ---------------------------------------------------------------------------
# Single batch worker (runs on its own container)
# ---------------------------------------------------------------------------

@app.function(image=sim_image, timeout=300)
def run_single_batch(params: dict) -> dict[str, Any]:
    """
    Run a batch of Monte Carlo scenarios for a single container.

    params keys:
        batch_id: int - identifier for this batch
        batch_size: int - number of scenarios to simulate
        seed: int - random seed for reproducibility
        foot_traffic_mean: float - avg daily foot traffic
        foot_traffic_std: float - std dev of daily foot traffic
        conversion_rate_alpha: float - Beta distribution alpha
        conversion_rate_beta: float - Beta distribution beta
        avg_order_value_mean: float - LogNormal mu for AOV
        avg_order_value_std: float - LogNormal sigma for AOV
        monthly_rent: float - base monthly rent
        rent_variance: float - rent variance factor (0-1)
        monthly_labor: float - monthly labor cost
        monthly_cogs_pct: float - COGS as % of revenue
        monthly_utilities: float - monthly utilities
        initial_investment: float - startup cost
        seasonal_amplitude: float - seasonal variation (0-1)
    """
    import numpy as np

    seed = params.get("seed", 0)
    batch_size = params.get("batch_size", SIM_BATCH_SIZE)
    rng = np.random.default_rng(seed)

    # Extract parameters
    ft_mean = params.get("foot_traffic_mean", 250)
    ft_std = params.get("foot_traffic_std", 60)
    cr_alpha = params.get("conversion_rate_alpha", 8.0)
    cr_beta = params.get("conversion_rate_beta", 20.0)
    aov_mean = params.get("avg_order_value_mean", 1.6)  # log-space
    aov_std = params.get("avg_order_value_std", 0.3)
    base_rent = params.get("monthly_rent", 3500)
    rent_var = params.get("rent_variance", 0.05)
    labor = params.get("monthly_labor", 8000)
    cogs_pct = params.get("monthly_cogs_pct", 0.30)
    utilities = params.get("monthly_utilities", 800)
    initial_inv = params.get("initial_investment", 150000)
    seasonal_amp = params.get("seasonal_amplitude", 0.15)

    annual_profits = []
    annual_revenues = []
    annual_costs = []
    monthly_details = []

    for _ in range(batch_size):
        yearly_revenue = 0.0
        yearly_cost = 0.0

        for month in range(12):
            # Seasonal multiplier (peaks in fall/spring for college towns)
            seasonal = 1.0 + seasonal_amp * np.sin(2 * np.pi * (month - 2) / 12)

            days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]
            month_revenue = 0.0

            for _ in range(days_in_month):
                # Daily foot traffic
                daily_traffic = max(0, rng.normal(ft_mean * seasonal, ft_std))

                # Conversion rate (what fraction buys)
                conversion = rng.beta(cr_alpha, cr_beta)

                # Average order value
                aov = rng.lognormal(aov_mean, aov_std)

                daily_rev = daily_traffic * conversion * aov
                month_revenue += daily_rev

            # Monthly costs
            month_rent = base_rent * (1 + rng.normal(0, rent_var))
            month_cost = month_rent + labor + (month_revenue * cogs_pct) + utilities

            yearly_revenue += month_revenue
            yearly_cost += month_cost

        annual_profit = yearly_revenue - yearly_cost
        annual_profits.append(float(annual_profit))
        annual_revenues.append(float(yearly_revenue))
        annual_costs.append(float(yearly_cost))

    return {
        "batch_id": params.get("batch_id", 0),
        "batch_size": batch_size,
        "profits": annual_profits,
        "revenues": annual_revenues,
        "costs": annual_costs,
    }


# ---------------------------------------------------------------------------
# Full simulation orchestrator (fan-out + aggregation)
# ---------------------------------------------------------------------------

@app.function(
    image=sim_image,
    volumes={"/results": results_vol},
    timeout=600,
)
def run_full_simulation(
    session_id: str,
    research_data: dict[str, Any] | None = None,
    override_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Launch all Monte Carlo batches in parallel and aggregate results.

    Args:
        session_id: Session identifier.
        research_data: Dict of research findings to parameterize simulation.
        override_params: Optional overrides (e.g., {"monthly_rent": 4200} for follow-up).

    Returns:
        Aggregated simulation results with statistics.
    """
    import numpy as np
    import os
    from memory.store import save, emit_event, set_status

    set_status(session_id, "simulating", 0.0, "Preparing simulation parameters...")

    # Build simulation parameters from research data
    sim_params = _build_sim_params(research_data or {})

    # Apply any overrides (for follow-up queries)
    if override_params:
        sim_params.update(override_params)

    # Create batch configurations
    batches = []
    for i in range(SIM_NUM_BATCHES):
        batch_params = {**sim_params}
        batch_params["batch_id"] = i
        batch_params["batch_size"] = SIM_BATCH_SIZE
        batch_params["seed"] = i * 1000 + 42
        batches.append(batch_params)

    emit_event(session_id, {
        "event": "simulation_started",
        "total_scenarios": SIM_NUM_SCENARIOS,
        "num_containers": SIM_NUM_BATCHES,
        "batch_size": SIM_BATCH_SIZE,
    })

    # 🔥 PARALLEL EXECUTION — launch all batches across Modal containers
    start_time = time.time()
    all_profits = []
    all_revenues = []
    all_costs = []
    completed = 0

    for batch_result in run_single_batch.map(batches):
        all_profits.extend(batch_result["profits"])
        all_revenues.extend(batch_result["revenues"])
        all_costs.extend(batch_result["costs"])
        completed += batch_result["batch_size"]

        # Emit progress events every 10 batches
        if completed % (SIM_BATCH_SIZE * 10) == 0 or completed >= SIM_NUM_SCENARIOS:
            emit_event(session_id, {
                "event": "simulation_progress",
                "completed": completed,
                "total": SIM_NUM_SCENARIOS,
                "pct": round(completed / SIM_NUM_SCENARIOS * 100, 1),
            })
            set_status(
                session_id, "simulating",
                completed / SIM_NUM_SCENARIOS,
                f"Completed {completed}/{SIM_NUM_SCENARIOS} simulations..."
            )

    elapsed = round(time.time() - start_time, 2)

    # Aggregate statistics
    profits = np.array(all_profits)
    revenues = np.array(all_revenues)
    costs = np.array(all_costs)

    initial_investment = sim_params.get("initial_investment", 150000)

    results = {
        "session_id": session_id,
        "total_scenarios": len(profits),
        "elapsed_seconds": elapsed,
        "num_containers": SIM_NUM_BATCHES,
        "parameters_used": sim_params,
        "profit": {
            "mean": round(float(np.mean(profits)), 2),
            "median": round(float(np.median(profits)), 2),
            "std": round(float(np.std(profits)), 2),
            "p10": round(float(np.percentile(profits, 10)), 2),
            "p25": round(float(np.percentile(profits, 25)), 2),
            "p50": round(float(np.percentile(profits, 50)), 2),
            "p75": round(float(np.percentile(profits, 75)), 2),
            "p90": round(float(np.percentile(profits, 90)), 2),
            "min": round(float(np.min(profits)), 2),
            "max": round(float(np.max(profits)), 2),
        },
        "revenue": {
            "mean": round(float(np.mean(revenues)), 2),
            "median": round(float(np.median(revenues)), 2),
            "std": round(float(np.std(revenues)), 2),
        },
        "cost": {
            "mean": round(float(np.mean(costs)), 2),
            "median": round(float(np.median(costs)), 2),
            "std": round(float(np.std(costs)), 2),
        },
        "roi": {
            "mean_pct": round(float(np.mean(profits) / initial_investment * 100), 2),
            "median_pct": round(float(np.median(profits) / initial_investment * 100), 2),
        },
        "risk": {
            "prob_loss": round(float(np.mean(profits < 0) * 100), 2),
            "var_10": round(float(np.percentile(profits, 10)), 2),
            "max_loss": round(float(np.min(profits)), 2),
        },
        "histogram": _compute_histogram(profits, bins=30),
    }

    # Persist results
    save(session_id, "simulation", results)

    # Write detailed results to volume
    os.makedirs(f"/results/{session_id}", exist_ok=True)
    with open(f"/results/{session_id}/simulation.json", "w") as f:
        json.dump(results, f, indent=2)
    results_vol.commit()

    emit_event(session_id, {
        "event": "simulation_complete",
        "total_scenarios": len(profits),
        "elapsed_seconds": elapsed,
        "mean_profit": results["profit"]["mean"],
        "prob_loss": results["risk"]["prob_loss"],
    })
    set_status(
        session_id, "simulating", 1.0,
        f"Simulation complete: {len(profits)} scenarios in {elapsed}s"
    )

    return results


def _build_sim_params(research_data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert research findings into simulation parameters.
    Uses sensible defaults when research data is incomplete.
    """
    # Extract foot traffic data
    ft = research_data.get("foot_traffic", {})
    demo = research_data.get("demographics", {})
    comp = research_data.get("competitor_analysis", {})

    # Check if LLM-generated business params were provided
    llm_params = research_data.get("_llm_business_params", {})

    # Foot traffic — prefer LLM estimate, fallback to research data
    ft_mean = llm_params.get("foot_traffic_mean") or ft.get("estimated_daily_foot_traffic_mean", 250)
    ft_std = llm_params.get("foot_traffic_std") or ft.get("estimated_daily_foot_traffic_std", 60)

    # Adjust based on demographics (higher student % = more coffee demand)
    student_pct = demo.get("avg_student_pct", 0.15)
    if student_pct > 0.3 and not llm_params.get("foot_traffic_mean"):
        ft_mean = int(ft_mean * 1.15)  # 15% boost for college towns

    # Market saturation affects conversion
    saturation = comp.get("market_saturation", "moderate")
    cr_alpha = llm_params.get("conversion_rate_alpha", 8.0)
    cr_beta = llm_params.get("conversion_rate_beta", 20.0)
    if not llm_params.get("conversion_rate_beta"):
        if saturation == "high":
            cr_beta = 25.0
        elif saturation == "low":
            cr_beta = 16.0

    # AOV in log-space: exp(1.6) ≈ $5.00
    aov_mean = llm_params.get("avg_order_value_mean", 1.6)
    aov_std = llm_params.get("avg_order_value_std", 0.3)

    # Rent — prefer LLM, fallback to income-adjusted
    if llm_params.get("monthly_rent"):
        base_rent = llm_params["monthly_rent"]
    else:
        median_income = demo.get("median_income", 50000)
        base_rent = 3500 if median_income < 40000 else 4500 if median_income < 60000 else 5500

    return {
        "foot_traffic_mean": ft_mean,
        "foot_traffic_std": ft_std,
        "conversion_rate_alpha": cr_alpha,
        "conversion_rate_beta": cr_beta,
        "avg_order_value_mean": aov_mean,
        "avg_order_value_std": aov_std,
        "monthly_rent": base_rent,
        "rent_variance": llm_params.get("rent_variance", 0.05),
        "monthly_labor": llm_params.get("monthly_labor", 8000),
        "monthly_cogs_pct": llm_params.get("monthly_cogs_pct", 0.30),
        "monthly_utilities": llm_params.get("monthly_utilities", 800),
        "initial_investment": llm_params.get("initial_investment", 150000),
        "seasonal_amplitude": llm_params.get("seasonal_amplitude", 0.15),
    }


def _compute_histogram(data, bins: int = 30) -> dict[str, Any]:
    """Compute a histogram suitable for frontend charting."""
    import numpy as np
    counts, edges = np.histogram(data, bins=bins)
    return {
        "counts": [int(c) for c in counts],
        "bin_edges": [round(float(e), 2) for e in edges],
        "bin_labels": [
            f"${round(float(edges[i])/1000, 1)}K - ${round(float(edges[i+1])/1000, 1)}K"
            for i in range(len(counts))
        ],
    }
