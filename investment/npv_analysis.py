"""
investment/npv_analysis.py
==========================
Calcul des indicateurs financiers (NPV, IRR, Payback) d'un projet de
stockage par batteries pour une taille donnée et un tarif donné.

Flux de trésorerie annuel :
    CF_t = Revenu_annuel - OPEX_annuel

Investissement initial (CAPEX) :
    CAPEX = cap_cost [€/kWh] × size [kWh]

NPV = -CAPEX + Σ_{t=1}^{N} CF_t / (1 + r)^t   où r = hurdle_rate

On estime le revenu annuel à partir du résultat d'optimisation du dispatch
(objectif de l'optimiseur = profit brut de l'arbitrage + tarif).
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
    """Paramètres financiers et techniques du projet."""
    size_kwh: float          # capacité énergie [kWh]
    storage_duration: float  # durée de stockage [h]
    cap_cost_per_kwh: float  # CAPEX spécifique [€/kWh]
    annual_om_per_kw: float  # OPEX annuel [€/kW]
    lifetime: int            # durée de vie [années]
    hurdle_rate: float       # taux d'actualisation

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
    """Résultat de l'analyse financière pour une taille donnée."""
    size_kwh: float
    capex: float
    annual_revenue: float   # revenu moyen annualisé (dispatch + tarif)
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
# Fonctions de calcul
# ---------------------------------------------------------------------------

def _irr(cashflows: np.ndarray, max_iter: int = 1000, tol: float = 1e-6) -> Optional[float]:
    """
    Calcule l'IRR par la méthode de Newton-Raphson.
    cashflows[0] doit être négatif (investissement initial).
    Retourne None si aucune solution n'est trouvée dans [−99 %, +500 %].
    """
    # Borne de recherche
    f = lambda r: np.sum(cashflows / (1 + r) ** np.arange(len(cashflows)))
    df = lambda r: np.sum(
        -np.arange(len(cashflows)) * cashflows / (1 + r) ** (np.arange(len(cashflows)) + 1)
    )

    r = 0.10  # point de départ
    for _ in range(max_iter):
        fr = f(r)
        dfr = df(r)
        if abs(dfr) < 1e-12:
            break
        r_new = r - fr / dfr
        # Garder r dans des limites raisonnables
        r_new = max(-0.99, min(r_new, 5.0))
        if abs(r_new - r) < tol:
            return r_new
        r = r_new
    return None


def _payback(cashflows: np.ndarray) -> Optional[float]:
    """Délai de récupération (années). cashflows[0] < 0."""
    cumulative = np.cumsum(cashflows)
    positive_idx = np.where(cumulative > 0)[0]
    if len(positive_idx) == 0:
        return None
    idx = positive_idx[0]
    if idx == 0:
        return 0.0
    # interpolation linéaire
    pb = idx - cumulative[idx - 1] / (cumulative[idx] - cumulative[idx - 1])
    return pb


def compute_npv(
    financials: ProjectFinancials,
    annual_revenue: float,
) -> NPVResult:
    """
    Calcule NPV, IRR et Payback pour un projet donné.

    Parameters
    ----------
    financials : ProjectFinancials
    annual_revenue : float
        Revenu annuel brut estimé [€] (issu du dispatch optimizer).

    Returns
    -------
    NPVResult
    """
    cf_annual = annual_revenue - financials.annual_opex

    # Flux : [-CAPEX, CF1, CF2, …, CF_N]
    cashflows = np.array(
        [-financials.capex] + [cf_annual] * financials.lifetime
    )

    # NPV
    t = np.arange(len(cashflows))
    npv = np.sum(cashflows / (1 + financials.hurdle_rate) ** t)

    # IRR
    irr = _irr(cashflows)

    # Payback (non actualisé)
    payback = _payback(cashflows)

    # Viabilité : NPV > 0
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
    Estime le revenu annuel moyen à partir des résultats de dispatch.

    Le revenu d'une année = Σ_t [ (Pd_t - Pc_t) × (base_price_t + tariff_t) ]
    On fait la moyenne sur l'horizon de simulation.

    Parameters
    ----------
    storage_result : pd.DataFrame
        DataFrame issu de runStorageDispatch* (colonnes : Pd, Pc, base_price, tariff, year).
    start_year, end_year : int
        Horizon de simulation.

    Returns
    -------
    float : revenu annuel moyen [€]
    """
    revenues = []
    for year in range(start_year, end_year + 1):
        df_year = storage_result[storage_result["year"] == year]
        if df_year.empty:
            continue
        # Pc est déjà négatif dans storage_result (convention de signe du core)
        # dispatch = Pd + Pc  (Pc < 0 → charge)
        # revenu = Σ dispatch × price   mais on préfère recalculer proprement :
        #   revenu = Σ (Pd - |Pc|) × price   avec price = base_price + tariff
        rev = ((df_year["Pd"] + df_year["Pc"]) * df_year["price"]).sum()
        revenues.append(rev)

    if not revenues:
        return 0.0
    return float(np.mean(revenues))
