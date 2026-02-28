"""
Generate realistic synthetic datasets for the AI Decision Engine demos.

Run this script once to produce CSV files:
  python data/generator.py

Datasets model a business analysis scenario in Urbana, IL.
"""

import csv
import os
import random
import math

SEED = 42
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_demographics(outpath: str, n_tracts: int = 50) -> None:
    """
    Generate synthetic census tract data near Urbana, IL.
    Columns: tract_id, population, median_income, median_age,
             pct_students, housing_density, lat, lng
    """
    rng = random.Random(SEED)

    rows = []
    for i in range(n_tracts):
        is_campus = i < 10  # first 10 tracts are near campus
        pop = rng.randint(1800, 6500) if not is_campus else rng.randint(4000, 12000)
        income = rng.randint(22000, 48000) if is_campus else rng.randint(38000, 95000)
        age = round(rng.gauss(24, 3), 1) if is_campus else round(rng.gauss(38, 8), 1)
        pct_students = round(rng.uniform(0.35, 0.80), 3) if is_campus else round(rng.uniform(0.02, 0.15), 3)
        density = rng.randint(2500, 8000) if is_campus else rng.randint(500, 3500)
        lat = round(40.1106 + rng.uniform(-0.04, 0.04), 6)
        lng = round(-88.2073 + rng.uniform(-0.05, 0.05), 6)

        rows.append({
            "tract_id": f"T{i+1:03d}",
            "population": pop,
            "median_income": income,
            "median_age": max(18, age),
            "pct_students": pct_students,
            "housing_density": density,
            "lat": lat,
            "lng": lng,
        })

    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Written {len(rows)} tracts -> {outpath}")


def generate_foot_traffic(outpath: str, n_locations: int = 10) -> None:
    """
    Generate hourly foot traffic for candidate locations.
    Columns: location_id, hour, day_of_week, avg_pedestrians, std_dev
    """
    rng = random.Random(SEED + 1)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Baseline hourly patterns (multiplier)
    weekday_pattern = {
        6: 0.1, 7: 0.5, 8: 1.2, 9: 1.0, 10: 0.8, 11: 1.1,
        12: 1.4, 13: 1.2, 14: 0.9, 15: 0.8, 16: 1.0, 17: 1.3,
        18: 1.1, 19: 0.7, 20: 0.4, 21: 0.2, 22: 0.1,
    }
    weekend_pattern = {
        8: 0.2, 9: 0.5, 10: 0.9, 11: 1.2, 12: 1.5, 13: 1.4,
        14: 1.3, 15: 1.1, 16: 1.0, 17: 0.8, 18: 0.6, 19: 0.4,
        20: 0.3, 21: 0.1,
    }

    rows = []
    for loc_id in range(1, n_locations + 1):
        base_traffic = rng.randint(80, 400)  # location attractiveness
        for day in days:
            is_weekend = day in ("Saturday", "Sunday")
            pattern = weekend_pattern if is_weekend else weekday_pattern
            for hour in range(6, 23):
                mult = pattern.get(hour, 0.05)
                avg = max(1, int(base_traffic * mult * rng.uniform(0.8, 1.2)))
                std = max(1, int(avg * rng.uniform(0.15, 0.35)))
                rows.append({
                    "location_id": f"L{loc_id:02d}",
                    "hour": hour,
                    "day_of_week": day,
                    "avg_pedestrians": avg,
                    "std_dev": std,
                })

    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Written {len(rows)} rows -> {outpath}")


def generate_competitors(outpath: str, n_competitors: int = 20) -> None:
    """
    Generate nearby competitor coffee shops.
    Columns: name, lat, lng, avg_rating, price_tier, est_daily_revenue, distance_km
    """
    rng = random.Random(SEED + 2)

    chain_names = [
        "Starbucks", "Dunkin'", "Caffe Bene", "Espresso Royale", "Café Kopi",
        "Brew Lab", "Aroma Café", "Flying Machine", "Java Hut", "Perk Place",
        "The Grind", "Morning Buzz", "Bean & Leaf", "Sip House", "Roast Republic",
        "Mugshot Coffee", "Drip Drop Café", "Press & Grind", "The Pour Over", "Latte Lounge",
    ]

    rows = []
    for i, name in enumerate(chain_names[:n_competitors]):
        lat = round(40.1106 + rng.uniform(-0.03, 0.03), 6)
        lng = round(-88.2073 + rng.uniform(-0.04, 0.04), 6)
        distance = round(math.sqrt((lat - 40.1106)**2 + (lng + 88.2073)**2) * 111, 2)  # approx km
        rating = round(rng.uniform(3.2, 4.9), 1)
        price_tier = rng.choice(["$", "$$", "$$$"])
        daily_rev = rng.randint(400, 2800)
        rows.append({
            "name": name,
            "lat": lat,
            "lng": lng,
            "avg_rating": rating,
            "price_tier": price_tier,
            "est_daily_revenue": daily_rev,
            "distance_km": distance,
        })

    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Written {len(rows)} competitors -> {outpath}")


if __name__ == "__main__":
    print("Generating synthetic datasets...")
    generate_demographics(os.path.join(DATA_DIR, "demographics.csv"))
    generate_foot_traffic(os.path.join(DATA_DIR, "foot_traffic.csv"))
    generate_competitors(os.path.join(DATA_DIR, "competitors.csv"))
    print("Done.")
