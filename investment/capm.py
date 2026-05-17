"""
investment/capm.py
==================
Calcul du hurdle rate pour les projets de stockage par batteries.

Méthode : WACC avec coût des fonds propres estimé via CAPM.

    Ke  = rf + β × (rm - rf)          [CAPM]
    WACC = E/V × Ke + D/V × Kd × (1 - tax)

Le hurdle rate retenu est max(WACC, WACC + risk_premium) afin de tenir
compte d'une prime de risque spécifique au projet (illiquidité, technologie).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import numpy as np



# ---------------------------------------------------------------------------
# Structures de données
# ---------------------------------------------------------------------------

@dataclass
class CAPMInputs:
    """Paramètres nécessaires au calcul CAPM / WACC."""

    # ---- CAPM ----
    rf: float = 0.03          # taux sans risque (ex. OAT 10 ans)
    beta: float = 0.85        # béta du projet stockage (≈ utilités régulées)
    market_premium: float = 0.055  # prime de marché (ERP historique Europe)

    # ---- Structure de capital ----
    equity_share: float = 0.40    # part fonds propres  E/V
    debt_share: float = 0.60      # part dette          D/V
    cost_of_debt: float = 0.045   # Kd avant impôt
    tax_rate: float = 0.30        # taux marginal d'imposition

    # ---- Prime de risque projet ----
    project_risk_premium: float = 0.01  # risque technologique / marché

    def __post_init__(self):
        if abs(self.equity_share + self.debt_share - 1.0) > 1e-6:
            raise ValueError("equity_share + debt_share doit être égal à 1.")


@dataclass
class HurdleRateResult:
    """Résultat du calcul du hurdle rate."""
    ke: float          # coût des fonds propres (CAPM)
    kd_after_tax: float  # coût de la dette après impôt
    wacc: float        # WACC
    hurdle_rate: float # taux retenu (WACC + prime projet)
    inputs: CAPMInputs = field(repr=False)

    def summary(self) -> str:
        lines = [
            "=" * 50,
            "  Calcul du Hurdle Rate (CAPM / WACC)",
            "=" * 50,
            f"  Taux sans risque  rf      : {self.inputs.rf*100:.2f} %",
            f"  Béta projet       β       : {self.inputs.beta:.2f}",
            f"  Prime de marché   ERP     : {self.inputs.market_premium*100:.2f} %",
            f"  Coût fonds propres Ke     : {self.ke*100:.2f} %",
            f"  Coût dette (après impôt)  : {self.kd_after_tax*100:.2f} %",
            f"  Structure  E/V={self.inputs.equity_share:.0%}  D/V={self.inputs.debt_share:.0%}",
            f"  WACC                      : {self.wacc*100:.2f} %",
            f"  Prime risque projet       : {self.inputs.project_risk_premium*100:.2f} %",
            f"  ► Hurdle Rate retenu      : {self.hurdle_rate*100:.2f} %",
            "=" * 50,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def compute_hurdle_rate(inputs: Optional[CAPMInputs] = None, **kwargs) -> HurdleRateResult:
    """
    Calcule le hurdle rate à partir des paramètres CAPM / WACC.

    Parameters
    ----------
    inputs : CAPMInputs, optional
        Objet contenant tous les paramètres. Si None, utilise les valeurs
        par défaut, éventuellement surchargées par **kwargs.
    **kwargs :
        Surcharge individuelle de champs de CAPMInputs
        (ex. rf=0.035, beta=1.1).

    Returns
    -------
    HurdleRateResult
    """
    if inputs is None:
        inputs = CAPMInputs(**{k: v for k, v in kwargs.items()
                               if k in CAPMInputs.__dataclass_fields__})
    else:
        # Appliquer les surcharges éventuelles
        for k, v in kwargs.items():
            if hasattr(inputs, k):
                setattr(inputs, k, v)

    # CAPM → coût des fonds propres
    ke = inputs.rf + inputs.beta * inputs.market_premium

    # Coût de la dette après impôt
    kd_after_tax = inputs.cost_of_debt * (1 - inputs.tax_rate)

    # WACC
    wacc = inputs.equity_share * ke + inputs.debt_share * kd_after_tax

    # Hurdle rate = WACC + prime de risque projet
    hurdle_rate = wacc + inputs.project_risk_premium

    return HurdleRateResult(
        ke=ke,
        kd_after_tax=kd_after_tax,
        wacc=wacc,
        hurdle_rate=hurdle_rate,
        inputs=inputs,
    )


# ---------------------------------------------------------------------------
# Aide : construction depuis les paramètres du fichier scénarios
# ---------------------------------------------------------------------------

def capm_from_params(params: dict, scenario: str = "scenario_1") -> HurdleRateResult:
    """
    Construit un HurdleRateResult en lisant les paramètres du dict `params`
    issu de settings.read().  Les clés attendues (toutes optionnelles) :

        global:parameter:rf          → taux sans risque
        global:parameter:k           → prime de risque projet (kappa)
    """
    p = params.get(scenario, params.get("scenario_1", {}))
    global_p = p.get("global", {}).get("parameter", {})

    rf = float(global_p.get("rf", 0.03))
    k  = float(global_p.get("k",  0.01))

    return compute_hurdle_rate(rf=rf, project_risk_premium=k)
