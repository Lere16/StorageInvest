"""
investment/investment_frontier.py
==================================
Search for the optimal investment frontier for each tariff scheme.

Algorithm
---------

1. For each scenario (= tariff scheme):
   a. Start from a minimum size (step_size).
   b. Run the dispatch optimizer for this size.
   c. Compute NPV via npv_analysis.compute_npv.
   d. If NPV > 0, record it, increase the size, and repeat.
   e. If NPV <= 0, the frontier has been reached: stop.

2. Summarize: maximum viable size, NPV, IRR, and payback by scenario.

The module exposes one main function:
    run_investment_frontier(params, scenario_cases, DF_PRICE, DF_LOAD,
                            hr_result, output_dir) -> pd.DataFrame
"""

from __future__ import annotations

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

from investment.capm import HurdleRateResult
from investment.npv_analysis import (
    ProjectFinancials,
    NPVResult,
    compute_npv,
    annualize_dispatch_revenue,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_financials(params: dict, scenario: str, size_kwh: float,
                      hurdle_rate: float) -> ProjectFinancials:
    """Build ProjectFinancials from the params dict."""
    p1 = params["scenario_1"]["global"]
    return ProjectFinancials(
        size_kwh=size_kwh,
        storage_duration=float(p1["parameter"]["storage_duration"]),
        cap_cost_per_kwh=float(p1["storage"]["cap_cost"]),
        annual_om_per_kw=float(p1["storage"]["annual_OM"]),
        lifetime=int(p1["storage"]["lifetime"]),
        hurdle_rate=hurdle_rate,
    )


def _run_dispatch_for_size(
    params: dict,
    scenario: str,
    size: float,
    DF_PRICE: pd.DataFrame,
    DF_LOAD: pd.DataFrame,
    base_tariff: float,
    VOLL: float,
    delta: float,
    start: int,
    end: int,
) -> pd.DataFrame:
    """Run the dispatch optimizer over the horizon and return df_combined."""
    # Import here to avoid circular imports.
    from storage_dispatch.batterydispatch import bat_optimize_

    df_combined = pd.DataFrame()
    for year in range(start, end + 1):
        shadow_price = DF_PRICE[DF_PRICE["year"] == year].reset_index(drop=True)
        df_load      = DF_LOAD[DF_LOAD["year"] == year].reset_index(drop=True)

        result = bat_optimize_(
            params, shadow_price, df_load, scenario,
            size, base_tariff, VOLL, delta
        )
        cur = result.info["data"].copy()
        cur["Pc"]   = cur["Pc"] * (-1)
        cur["year"] = year
        df_combined = pd.concat([df_combined, cur], ignore_index=True)

    if df_combined.empty:
        return df_combined

    df_combined["price"]    = df_combined["base_price"] + df_combined["tariff"]
    df_combined["dispatch"] = df_combined["Pd"] + df_combined["Pc"]
    return df_combined


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def run_investment_frontier(
    params: dict,
    scenario_cases: List[str],
    DF_PRICE: pd.DataFrame,
    DF_LOAD: pd.DataFrame,
    hr_result: HurdleRateResult,
    output_dir: str = "results/investment",
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Iteratively search for the maximum profitable investment size
    for each scenario (tariff scheme).

    Parameters
    ----------
    params : dict
        Parameter dictionary read by settings.read().
    scenario_cases : list[str]
        Names of the scenarios to analyze, e.g. ['scenario_1', 'scenario_2'].
    DF_PRICE, DF_LOAD : pd.DataFrame
    hr_result : HurdleRateResult
        CAPM/WACC result that provides the hurdle_rate.
    output_dir : str
        Output directory for CSV files.
    verbose : bool

    Returns
    -------
    pd.DataFrame
        Summary table: one row per scenario with indicators for the last
        profitable size and the first non-profitable size.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Common parameters, read from scenario_1 as the project convention.
    p1      = params["scenario_1"]["global"]
    start   = int(p1["config"]["start"])
    end     = int(p1["config"]["end"])

    hurdle_rate = hr_result.hurdle_rate
    summary_rows = []

    for scenario in scenario_cases:
        ps  = params[scenario]["global"]
        VOLL        = float(ps["network"]["VOLL"])
        base_tariff = float(ps["network"].get("base_tariff",
                            params["scenario_1"]["global"]["network"]["base_tariff"]))
        delta       = float(ps["tariff"]["delta"])
        step_size   = float(ps["parameter"].get("step_size", 100))
        max_size    = float(ps["parameter"].get("size", 5 * step_size))

        shape       = ps["tariff"]["shape"]
        config      = ps["tariff"]["configuration"]
        descriptor  = ps["config"].get("scenario_descriptor", scenario)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Scenario : {scenario}  |  Tariff : {shape}  |  Config : {config}")
            print(f"  Step : {step_size} MWh  |  Max tested : {max_size} MWh")
            print(f"  Hurdle rate : {hurdle_rate*100:.2f} %")

        scenario_records: List[dict] = []
        last_viable: Optional[NPVResult] = None
        first_non_viable: Optional[NPVResult] = None

        size = step_size
        while size <= max_size + 1e-6:
            if verbose:
                print(f"  -> Size {size:.0f} MWh ...", end=" ", flush=True)

            # 1. Dispatch
            """ 
            try:
                df = _run_dispatch_for_size(
                    params, scenario, size,
                    DF_PRICE, DF_LOAD,
                    base_tariff, VOLL, delta,
                    start, end,
                )
            except Exception as exc:
                print(f"Dispatch error: {exc}")
                break
            """
            df = _run_dispatch_for_size(
                    params, scenario, size,
                    DF_PRICE, DF_LOAD,
                    base_tariff, VOLL, delta,
                    start, end,
                )
            
            if df.empty:
                print("no data")
                break

            # 2. Average annual revenue
            annual_rev = annualize_dispatch_revenue(df, start, end)

            # 3. Financial indicators
            financials = _build_financials(params, scenario, size, hurdle_rate)
            npv_res    = compute_npv(financials, annual_rev)

            row = {
                "scenario":       scenario,
                "descriptor":     descriptor,
                "tariff_shape":   shape,
                "configuration":  config,
                "delta":          delta,
                **npv_res.summary_row(),
                "hurdle_rate_%":  round(hurdle_rate * 100, 2),
            }
            scenario_records.append(row)

            if verbose:
                status = "viable" if npv_res.is_viable else "not viable"
                print(f"NPV = {npv_res.npv:+,.0f} EUR  IRR = "
                      f"{npv_res.irr*100:.1f}%  {status}"
                      if npv_res.irr is not None
                      else f"NPV = {npv_res.npv:+,.0f} EUR  IRR = N/A  {status}")

            if npv_res.is_viable:
                last_viable = npv_res
            else:
                first_non_viable = npv_res
                # The frontier has been reached: stop.
                break

            size += step_size

        # Detailed save by scenario
        if scenario_records:
            df_scen = pd.DataFrame(scenario_records)
            df_scen.to_csv(
                os.path.join(output_dir, f"investment_frontier_{scenario}.csv"),
                index=False,
            )

        # Summary row
        summary_rows.append(_build_summary_row(
            scenario, descriptor, shape, config, delta, hurdle_rate,
            last_viable, first_non_viable,
        ))

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(
        os.path.join(output_dir, "investment_summary.csv"), index=False
    )

    if verbose:
        print("\n\n" + "=" * 60)
        print("  SUMMARY - INVESTMENT FRONTIER")
        print("=" * 60)
        _print_summary(df_summary)

    return df_summary


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_summary_row(
    scenario: str,
    descriptor: str,
    shape: str,
    config: str,
    delta: float,
    hurdle_rate: float,
    last_viable: Optional[NPVResult],
    first_non_viable: Optional[NPVResult],
) -> dict:
    row = {
        "scenario":             scenario,
        "descriptor":           descriptor,
        "tariff_shape":         shape,
        "configuration":        config,
        "delta":                delta,
        "hurdle_rate_%":        round(hurdle_rate * 100, 2),
    }
    if last_viable:
        row.update({
            "max_viable_size_kWh":  last_viable.size_kwh,
            "max_viable_NPV_EUR":   round(last_viable.npv, 0),
            "max_viable_IRR_%":     round(last_viable.irr * 100, 2)
                                    if last_viable.irr is not None else None,
            "max_viable_payback_yr": round(last_viable.payback_years, 1)
                                    if last_viable.payback_years is not None else None,
        })
    else:
        row.update({
            "max_viable_size_kWh":   0,
            "max_viable_NPV_EUR":    None,
            "max_viable_IRR_%":      None,
            "max_viable_payback_yr": None,
        })

    if first_non_viable:
        row.update({
            "first_nonviable_size_kWh": first_non_viable.size_kwh,
            "first_nonviable_NPV_EUR":  round(first_non_viable.npv, 0),
        })
    else:
        row.update({
            "first_nonviable_size_kWh": None,
            "first_nonviable_NPV_EUR":  None,
        })
    return row


def _print_summary(df: pd.DataFrame) -> None:
    cols = [
        "scenario", "tariff_shape", "configuration", "delta",
        "max_viable_size_kWh", "max_viable_NPV_EUR",
        "max_viable_IRR_%", "max_viable_payback_yr",
        "hurdle_rate_%",
    ]
    cols_present = [c for c in cols if c in df.columns]
    print(df[cols_present].to_string(index=False))
