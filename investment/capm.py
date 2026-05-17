"""
investment/capm.py
==================
Compute the hurdle rate for battery storage projects.

Method: WACC with the cost of equity estimated via CAPM.

    Ke   = rf + beta x (rm - rf)        [CAPM]
    WACC = E/V x Ke + D/V x Kd x (1 - tax)

The retained hurdle rate is max(WACC, WACC + risk_premium) to account
for a project-specific risk premium (illiquidity, technology).
"""


from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import numpy as np



# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CAPMInputs:
    """Parameters required for CAPM / WACC calculation."""

    # ---- CAPM ----
    rf: float = 0.03          # risk-free rate, e.g. 10-year OAT
    beta: float = 0.85        # storage project beta, close to regulated utilities
    market_premium: float = 0.055  # market premium, historical European ERP

    # ---- Capital structure ----
    equity_share: float = 0.40    # equity share  E/V
    debt_share: float = 0.60      # debt share    D/V
    cost_of_debt: float = 0.045   # pre-tax Kd
    tax_rate: float = 0.30        # marginal tax rate

    # ---- Project risk premium ----
    project_risk_premium: float = 0.01  # technology / market risk

    def __post_init__(self):
        if abs(self.equity_share + self.debt_share - 1.0) > 1e-6:
            raise ValueError("equity_share + debt_share must be equal to 1.")


@dataclass
class HurdleRateResult:
    """Result of the hurdle rate calculation."""
    ke: float          # cost of equity (CAPM)
    kd_after_tax: float  # after-tax cost of debt
    wacc: float        # WACC
    hurdle_rate: float # retained rate (WACC + project premium)
    inputs: CAPMInputs = field(repr=False)

    def summary(self) -> str:
        lines = [
            "=" * 50,
            "  Hurdle Rate Calculation (CAPM / WACC)",
            "=" * 50,
            f"  Risk-free rate  rf       : {self.inputs.rf*100:.2f} %",
            f"  Project beta             : {self.inputs.beta:.2f}",
            f"  Market premium ERP       : {self.inputs.market_premium*100:.2f} %",
            f"  Cost of equity Ke        : {self.ke*100:.2f} %",
            f"  Cost of debt (after tax) : {self.kd_after_tax*100:.2f} %",
            f"  Structure  E/V={self.inputs.equity_share:.0%}  D/V={self.inputs.debt_share:.0%}",
            f"  WACC                     : {self.wacc*100:.2f} %",
            f"  Project risk premium     : {self.inputs.project_risk_premium*100:.2f} %",
            f"  Retained Hurdle Rate     : {self.hurdle_rate*100:.2f} %",
            "=" * 50,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def compute_hurdle_rate(inputs: Optional[CAPMInputs] = None, **kwargs) -> HurdleRateResult:
    """
    Compute the hurdle rate from CAPM / WACC parameters.

    Parameters
    ----------
    inputs : CAPMInputs, optional
        Object containing all parameters. If None, uses the default values,
        optionally overridden by **kwargs.
    **kwargs :
        Individual overrides for CAPMInputs fields
        (e.g. rf=0.035, beta=1.1).

    Returns
    -------
    HurdleRateResult
    """
    if inputs is None:
        inputs = CAPMInputs(**{k: v for k, v in kwargs.items()
                               if k in CAPMInputs.__dataclass_fields__})
    else:
        # Apply any overrides.
        for k, v in kwargs.items():
            if hasattr(inputs, k):
                setattr(inputs, k, v)

    # CAPM -> cost of equity
    ke = inputs.rf + inputs.beta * inputs.market_premium

    # After-tax cost of debt
    kd_after_tax = inputs.cost_of_debt * (1 - inputs.tax_rate)

    # WACC
    wacc = inputs.equity_share * ke + inputs.debt_share * kd_after_tax

    # Hurdle rate = WACC + project risk premium
    hurdle_rate = wacc + inputs.project_risk_premium

    return HurdleRateResult(
        ke=ke,
        kd_after_tax=kd_after_tax,
        wacc=wacc,
        hurdle_rate=hurdle_rate,
        inputs=inputs,
    )


# ---------------------------------------------------------------------------
# Helper: build from scenario file parameters
# ---------------------------------------------------------------------------

def capm_from_params(params: dict, scenario: str = "scenario_1") -> HurdleRateResult:
    """
    Build a HurdleRateResult by reading parameters from the `params` dict
    produced by settings.read(). Expected keys, all optional:

        global:parameter:rf          -> risk-free rate
        global:parameter:k           -> project risk premium (kappa)
    """
    p = params.get(scenario, params.get("scenario_1", {}))
    global_p = p.get("global", {}).get("parameter", {})

    rf = float(global_p.get("rf", 0.03))
    k  = float(global_p.get("k",  0.01))

    return compute_hurdle_rate(rf=rf, project_risk_premium=k)
