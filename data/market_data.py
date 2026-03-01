"""
Market Data Fetcher — Downloads real estate data from Zillow Research & Redfin.

Fetches actual market statistics (home values, rents, inventory) for specific
cities/regions and packages them for injection into Analyst agent prompts.

Data Sources:
  - Zillow ZHVI (Home Value Index): public CSV from zillow.com/research/data
  - Zillow ZORI (Rent Index): public CSV from zillow.com/research/data
  - Redfin (reteps/redfin): supplementary listing-level data (best-effort)
"""

from __future__ import annotations

import io
from typing import Any


# ---------------------------------------------------------------------------
# Zillow Research public CSV URLs
# ---------------------------------------------------------------------------
ZILLOW_ZHVI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zhvi/"
    "City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
ZILLOW_ZORI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "City_zori_uc_sfrcondomfr_sm_sa_month.csv"
)


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def fetch_all_market_data(regions: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch market data for ALL target regions in one shot.

    Downloads Zillow CSVs once, filters for every city, then attempts
    Redfin supplementary data per-city.

    Args:
        regions: List of region strings, e.g. ["Carbondale, IL", "Marion, IL"]

    Returns:
        Dict mapping region string → market data dict with keys:
            zillow, redfin, summary (human-readable text for LLM injection)
    """
    import pandas as pd

    parsed = {r: _parse_region(r) for r in regions}

    # ── Download Zillow CSVs once ──────────────────────────────────────
    zhvi_df = _download_csv(ZILLOW_ZHVI_URL, "Zillow ZHVI")
    zori_df = _download_csv(ZILLOW_ZORI_URL, "Zillow ZORI")

    results: dict[str, dict[str, Any]] = {}

    for region, (city, state) in parsed.items():
        zillow = _extract_zillow(zhvi_df, zori_df, city, state)
        redfin = _fetch_redfin(city, state)

        summary = _build_summary(city, state, zillow, redfin)

        results[region] = {
            "city": city,
            "state": state,
            "zillow": zillow,
            "redfin": redfin,
            "summary": summary,
        }

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Zillow helpers
# ═══════════════════════════════════════════════════════════════════════════

def _download_csv(url: str, label: str):
    """Download a CSV into a DataFrame. Returns None on failure."""
    import httpx
    import pandas as pd

    try:
        print(f"  📥 Downloading {label}...")
        with httpx.Client(timeout=45.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        print(f"  ✅ {label}: {len(df):,} rows")
        return df
    except Exception as e:
        print(f"  ⚠️ Failed to download {label}: {e}")
        return None


def _extract_zillow(zhvi_df, zori_df, city: str, state: str) -> dict[str, Any]:
    """Extract Zillow data for a single city from the pre-loaded DataFrames."""
    import pandas as pd

    data: dict[str, Any] = {}

    # Zillow CSVs use 2-letter state abbreviations in both StateName and State
    state_abbrev = _state_to_abbrev(state)

    # ── ZHVI (Home Values) ─────────────────────────────────────────────
    if zhvi_df is not None:
        try:
            match = zhvi_df[
                (zhvi_df["RegionName"].str.lower() == city.lower())
                & (zhvi_df["StateName"].str.upper() == state_abbrev.upper())
            ]
            if not match.empty:
                row = match.iloc[0]
                date_cols = [c for c in zhvi_df.columns if str(c)[:2] == "20"]
                if date_cols:
                    latest_col = date_cols[-1]
                    yoy_col = date_cols[-13] if len(date_cols) > 13 else date_cols[0]
                    fiveyr_col = date_cols[-61] if len(date_cols) > 61 else date_cols[0]

                    val = row[latest_col]
                    if pd.notna(val):
                        data["median_home_value"] = round(float(val))

                    yoy_val = row[yoy_col]
                    if pd.notna(val) and pd.notna(yoy_val) and float(yoy_val) > 0:
                        data["home_value_yoy_pct"] = round(
                            (float(val) - float(yoy_val)) / float(yoy_val) * 100, 2
                        )

                    fiveyr_val = row[fiveyr_col]
                    if pd.notna(val) and pd.notna(fiveyr_val) and float(fiveyr_val) > 0:
                        data["home_value_5yr_pct"] = round(
                            (float(val) - float(fiveyr_val)) / float(fiveyr_val) * 100, 2
                        )

                    data["metro"] = str(row.get("Metro", "N/A"))
                    data["county"] = str(row.get("CountyName", "N/A"))
        except Exception as e:
            data["zhvi_error"] = str(e)[:200]

    # ── ZORI (Rents) ──────────────────────────────────────────────────
    if zori_df is not None:
        try:
            match = zori_df[
                (zori_df["RegionName"].str.lower() == city.lower())
                & (zori_df["StateName"].str.upper() == state_abbrev.upper())
            ]
            if not match.empty:
                row = match.iloc[0]
                date_cols = [c for c in zori_df.columns if str(c)[:2] == "20"]
                if date_cols:
                    latest_col = date_cols[-1]
                    yoy_col = date_cols[-13] if len(date_cols) > 13 else date_cols[0]

                    rent = row[latest_col]
                    if pd.notna(rent):
                        data["median_rent"] = round(float(rent))

                    yoy_rent = row[yoy_col]
                    if pd.notna(rent) and pd.notna(yoy_rent) and float(yoy_rent) > 0:
                        data["rent_yoy_pct"] = round(
                            (float(rent) - float(yoy_rent)) / float(yoy_rent) * 100, 2
                        )
        except Exception as e:
            data["zori_error"] = str(e)[:200]

    return data


# ═══════════════════════════════════════════════════════════════════════════
# Redfin helper (best-effort via reteps/redfin)
# ═══════════════════════════════════════════════════════════════════════════

def _fetch_redfin(city: str, state: str) -> dict[str, Any]:
    """
    Attempt to pull supplementary data from Redfin.
    Falls back gracefully if the package is missing or the API fails.
    """
    data: dict[str, Any] = {}
    try:
        from redfin import Redfin

        client = Redfin()
        query = f"{city}, {_state_to_abbrev(state)}"
        response = client.search(query)
        payload = response.get("payload", {})

        # Try to extract region-level info from the exact match
        exact = payload.get("exactMatch") or {}
        if exact:
            data["redfin_name"] = exact.get("name", "")
            data["redfin_url"] = exact.get("url", "")
            data["redfin_id"] = exact.get("id", "")

        # Try getting listing-count-level data from search results
        sections = payload.get("sections", [])
        for section in sections:
            rows = section.get("rows", [])
            if rows:
                data["redfin_listings_found"] = len(rows)
                break

    except ImportError:
        data["redfin_note"] = "redfin package not installed — skipped"
    except Exception as e:
        data["redfin_note"] = f"Redfin lookup failed: {str(e)[:150]}"

    return data


# ═══════════════════════════════════════════════════════════════════════════
# Summary builder (human-readable text for LLM prompt injection)
# ═══════════════════════════════════════════════════════════════════════════

def _build_summary(city: str, state: str, zillow: dict, redfin: dict) -> str:
    """Build a human-readable market data block the Analyst LLM can reason over."""
    lines = [f"=== Live Market Data for {city}, {_state_to_abbrev(state)} ==="]

    # Zillow home values
    if "median_home_value" in zillow:
        lines.append(f"Median Home Value (Zillow ZHVI): ${zillow['median_home_value']:,}")
    if "home_value_yoy_pct" in zillow:
        lines.append(f"  Year-over-Year Change: {zillow['home_value_yoy_pct']:+.1f}%")
    if "home_value_5yr_pct" in zillow:
        lines.append(f"  5-Year Appreciation: {zillow['home_value_5yr_pct']:+.1f}%")
    if "metro" in zillow and zillow["metro"] != "N/A":
        lines.append(f"  Metro Area: {zillow['metro']}")
    if "county" in zillow and zillow["county"] != "N/A":
        lines.append(f"  County: {zillow['county']}")

    # Zillow rents
    if "median_rent" in zillow:
        lines.append(f"Median Rent (Zillow ZORI): ${zillow['median_rent']:,}/month")
    if "rent_yoy_pct" in zillow:
        lines.append(f"  Rent Year-over-Year: {zillow['rent_yoy_pct']:+.1f}%")

    # Redfin supplementary
    if redfin.get("redfin_listings_found"):
        lines.append(f"Active Redfin Listings: {redfin['redfin_listings_found']}")

    # ── Derived investment metrics ──
    if "median_home_value" in zillow and "median_rent" in zillow:
        annual_rent = zillow["median_rent"] * 12
        home_val = zillow["median_home_value"]
        gross_yield = annual_rent / home_val * 100
        price_rent_ratio = home_val / annual_rent

        lines.append("")
        lines.append("--- Derived Investment Metrics ---")
        lines.append(f"Gross Rental Yield: {gross_yield:.2f}%")
        lines.append(f"Price-to-Rent Ratio: {price_rent_ratio:.1f}")

        if price_rent_ratio < 15:
            lines.append("  → Market FAVORS INVESTORS (buy & rent)")
        elif price_rent_ratio > 21:
            lines.append("  → Market is EXPENSIVE relative to rents")
        else:
            lines.append("  → Market is NEUTRAL for investors")

        # Cap rate estimate (gross yield minus ~40% expenses)
        est_cap_rate = gross_yield * 0.60
        lines.append(f"Estimated Cap Rate (after ~40% expenses): {est_cap_rate:.2f}%")

    # Data quality note
    has_home = "median_home_value" in zillow
    has_rent = "median_rent" in zillow
    if not has_home and not has_rent:
        lines.append("")
        lines.append(
            "⚠️ LIMITED DATA: No Zillow data found for this city. "
            "Analysis will rely on your general knowledge of this market."
        )
    elif not has_rent:
        lines.append("")
        lines.append("⚠️ No rental data available — rental yield cannot be computed.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Region / state parsing utilities
# ═══════════════════════════════════════════════════════════════════════════

def _parse_region(region: str) -> tuple[str, str]:
    """Parse 'City, ST' or 'City, State' into (city, full_state_name)."""
    parts = [p.strip() for p in region.split(",")]
    if len(parts) >= 2:
        city = parts[0]
        state_raw = parts[1]
        state = _abbrev_to_state(state_raw) if len(state_raw) <= 3 else state_raw
        return city, state
    words = region.strip().split()
    if len(words) >= 2:
        state_raw = words[-1]
        city = " ".join(words[:-1])
        state = _abbrev_to_state(state_raw) if len(state_raw) <= 3 else state_raw
        return city, state
    return region, ""


_ABBREV_TO_STATE = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}
_STATE_TO_ABBREV = {v.upper(): k for k, v in _ABBREV_TO_STATE.items()}


def _abbrev_to_state(abbrev: str) -> str:
    return _ABBREV_TO_STATE.get(abbrev.strip().upper(), abbrev.strip())


def _state_to_abbrev(state: str) -> str:
    if len(state.strip()) <= 2:
        return state.strip().upper()
    return _STATE_TO_ABBREV.get(state.strip().upper(), state[:2].upper())
