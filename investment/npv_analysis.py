"""
investment/npv_analysis.py
==========================
Compute financial indicators (NPV, IRR, Payback) for a battery storage
project with a given size and tariff.

Annual cash flow:
    CF_t = annual_revenue - annual_OPEX

Initial investment (CAPEX):
    CAPEX = cap_cost [EUR/kWh] x size [kWh]

NPV = -CAPEX + sum_{t=1}^{N} CF_t / (1 + r)^t, where r = hurdle_rate

Annual revenue is estimated from the dispatch optimization result
(optimizer objective = gross arbitrage profit + tariff).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

@dataclass
class ProjectFinancials:
    """Financial and technical project parameters."""
    size_kwh: float          # energy capacity [kWh]
    storage_duration: float  # storage duration [h]
    cap_cost_per_kwh: float  # specific CAPEX [EUR/kWh]
    annual_om_per_kw: float  # annual OPEX [EUR/kW]
    lifetime: int            # lifetime [years]
    hurdle_rate: float       # discount rate

    @property
    def power_kw(self) -> float:
        return self.size_kwh / self.storage_duration

    @property
    def capex(self) -> float:
        return self.cap_cost_per_kwh * self.size_kwh

    @property
    def annual_opex(self) -> float:
        return self.annual_om_per_kw * self.power_kw


@dataclass
class NPVResult:
    """Financial analysis result for a given size."""
    size_kwh: float
    capex: float
    annual_revenue: float   # average annualized revenue (dispatch + tariff)
    annual_opex: float
    annual_cashflow: float
    npv: float
    irr: Optional[float]
    payback_years: Optional[float]
    is_viable: bool         # NPV > 0  AND  IRR > hurdle_rate

    def summary_row(self) -> dict:
        return {
            "size_kWh":        self.size_kwh,
            "CAPEX_EUR":       round(self.capex, 0),
            "Annual_Rev_EUR":  round(self.annual_revenue, 0),
            "Annual_OPEX_EUR": round(self.annual_opex, 0),
            "Annual_CF_EUR":   round(self.annual_cashflow, 0),
            "NPV_EUR":         round(self.npv, 0),
            "IRR_%":           round(self.irr * 100, 2) if self.irr is not None else None,
            "Payback_yr":      round(self.payback_years, 1) if self.payback_years is not None else None,
            "Viable":          self.is_viable,
        }


# ---------------------------------------------------------------------------
# Calculation functions
# ---------------------------------------------------------------------------

def _irr(cashflows: np.ndarray, max_iter: int = 1000, tol: float = 1e-6) -> Optional[float]:
    """
    Compute IRR using the Newton-Raphson method.
    cashflows[0] must be negative (initial investment).
    Return None if no solution is found within [-99%, +500%].
    """
    # Search bound
    f = lambda r: np.sum(cashflows / (1 + r) ** np.arange(len(cashflows)))
    df = lambda r: np.sum(
        -np.arange(len(cashflows)) * cashflows / (1 + r) ** (np.arange(len(cashflows)) + 1)
    )

    r = 0.10  # starting point
    for _ in range(max_iter):
        fr = f(r)
        dfr = df(r)
        if abs(dfr) < 1e-12:
            break
        r_new = r - fr / dfr
        # Keep r within reasonable bounds.
        r_new = max(-0.99, min(r_new, 5.0))
        if abs(r_new - r) < tol:
            return r_new
        r = r_new
    return None


def _payback(cashflows: np.ndarray) -> Optional[float]:
    """Payback period in years. cashflows[0] < 0."""
    cumulative = np.cumsum(cashflows)
    positive_idx = np.where(cumulative > 0)[0]
    if len(positive_idx) == 0:
        return None
    idx = positive_idx[0]
    if idx == 0:
        return 0.0
    # Linear interpolation
    pb = idx - cumulative[idx - 1] / (cumulative[idx] - cumulative[idx - 1])
    return pb


def compute_npv(
    financials: ProjectFinancials,
    annual_revenue: float,
) -> NPVResult:
    """
    Compute NPV, IRR, and Payback for a given project.

    Parameters
    ----------
    financials : ProjectFinancials
    annual_revenue : float
        Estimated gross annual revenue [EUR] from the dispatch optimizer.

    Returns
    -------
    NPVResult
    """
    cf_annual = annual_revenue - financials.annual_opex

    # Cash flows: [-CAPEX, CF1, CF2, ..., CF_N]
    cashflows = np.array(
        [-financials.capex] + [cf_annual] * financials.lifetime
    )

    # NPV
    t = np.arange(len(cashflows))
    npv = np.sum(cashflows / (1 + financials.hurdle_rate) ** t)

    # IRR
    irr = _irr(cashflows)

    # Payback, undiscounted
    payback = _payback(cashflows)

    # Viability: NPV > 0
    is_viable = npv > 0

    return NPVResult(
        size_kwh=financials.size_kwh,
        capex=financials.capex,
        annual_revenue=annual_revenue,
        annual_opex=financials.annual_opex,
        annual_cashflow=cf_annual,
        npv=npv,
        irr=irr,
        payback_years=payback,
        is_viable=is_viable,
    )


def annualize_dispatch_revenue(
    storage_result: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> float:
    """
    Estimate average annual revenue from dispatch results.

    Revenue for one year = sum_t [(Pd_t - Pc_t) x (base_price_t + tariff_t)]
    The value is averaged over the simulation horizon.

    Parameters
    ----------
    storage_result : pd.DataFrame
        DataFrame from runStorageDispatch* with columns: Pd, Pc, base_price, tariff, year.
    start_year, end_year : int
        Simulation horizon.

    Returns
    -------
    float : average annual revenue [EUR]
    """
    revenues = []
    for year in range(start_year, end_year + 1):
        df_year = storage_result[storage_result["year"] == year]
        if df_year.empty:
            continue
        # Pc is already negative in storage_result, following the core sign convention.
        # dispatch = Pd + Pc  (Pc < 0 means charge)
        # revenue = sum(dispatch x price), but we prefer to recompute it explicitly:
        #   revenue = sum((Pd - |Pc|) x price), with price = base_price + tariff
        rev = ((df_year["Pd"] + df_year["Pc"]) * df_year["price"]).sum()
        revenues.append(rev)

    if not revenues:
        return 0.0
    return float(np.mean(revenues))
