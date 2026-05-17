"""
main.py  —  Point d'entrée du projet de dispatch + investissement batterie
===========================================================================
Étapes disponibles :

  STEP 0  Calcul du hurdle rate (CAPM / WACC)
  STEP 1  Comparaison du dispatch pour différents schémas tarifaires
  STEP 2  Analyse de sensibilité sur delta
  STEP 3  Analyse de sensibilité sur share
  STEP 4  Comparaison ex-ante vs ex-post
  STEP 5  Frontière d'investissement (module investissement)
"""

from core import (
    readStorageDispatchScenario,
    readLoadPrice,
    runStorageDispatchCases,
    runStorageDispatchSensitivitydelta,
    runStorageDispatchSensitivityShare,
    runStorageConfiguration,
    # ── Nouveau ──────────────────────────────
    computeHurdleRate,
    runInvestmentFrontier,
)
from results_analysis import (
    plotStorageDispatchCases,
    plotStorageDispatchSensitivitydelta,
    plotStorageDispatchSensitivityShare,
    plotStorageConfiguration,
    plotdataAnalysis,
)

# ---------------------------------------------------------------------------
# Lecture des scénarios et des données
# ---------------------------------------------------------------------------
SCENARIO_LIST = list(range(1, 30))
SCENARIOS, params = readStorageDispatchScenario(SCENARIO_LIST)

base_tariff = float(params["scenario_1"]["global"]["network"]["base_tariff"])
area        = params["scenario_1"]["global"]["network"]["area"]

DF_LOAD, DF_PRICE = readLoadPrice(area)


# ---------------------------------------------------------------------------
# STEP 0 : Hurdle Rate (CAPM / WACC)
# ---------------------------------------------------------------------------
print("STEP 0 : CALCUL DU HURDLE RATE (CAPM / WACC)")
HR_RESULT = computeHurdleRate(
    params,
    scenario="scenario_1",
    # Valeurs par défaut — à ajuster selon le contexte de marché :
    beta=0.85,             # risque systématique du stockage (≈ utilités)
    market_premium=0.055,  # prime de risque de marché Europe
    equity_share=0.40,     # structure de capital typique projet énergie
    cost_of_debt=0.045,    # coût de la dette (OAT + spread)
    tax_rate=0.30,
)


# ---------------------------------------------------------------------------
# STEP 1 : Comparaison dispatch par schéma tarifaire
# ---------------------------------------------------------------------------
print("\nSTEP 1 : STORAGE DISPATCH INCLUDING TARIFF SIGNALS")
scenario_cases  = SCENARIOS[:4]
selected_years  = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]

STORAGE_RESULT1 = runStorageDispatchCases(
    params, scenario_cases, DF_PRICE, base_tariff, DF_LOAD
)
plotStorageDispatchCases(scenario_cases, STORAGE_RESULT1, selected_years, params)


# ---------------------------------------------------------------------------
# STEP 5 : Frontière d'investissement  ← NOUVEAU
# ---------------------------------------------------------------------------
print("\nSTEP 5 : FRONTIÈRE D'INVESTISSEMENT PAR SCHÉMA TARIFAIRE")

# Scénarios max_invest (indices 28-44 dans le CSV → scenario_29 à scenario_45)
# Adaptez la plage selon votre fichier.
invest_scenario_list = list(range(29, 46))
invest_scenario_list = [s for s in invest_scenario_list if s <= len(SCENARIOS)]
INVEST_SCENARIOS = [list(params.keys())[i - 1] for i in invest_scenario_list
                    if i - 1 < len(params)]

if INVEST_SCENARIOS:
    INV_SUMMARY = runInvestmentFrontier(
        params=params,
        scenario_cases=INVEST_SCENARIOS,
        DF_PRICE=DF_PRICE,
        DF_LOAD=DF_LOAD,
        hr_result=HR_RESULT,
        output_dir="results/investment",
        verbose=True,
    )
    print("\nTableau de synthèse sauvegardé dans results/investment/investment_summary.csv")
else:
    print("  Aucun scénario d'investissement trouvé — vérifiez SCENARIO_LIST.")


# ---------------------------------------------------------------------------
# Étapes commentées (décommenter selon besoin)
# ---------------------------------------------------------------------------

'''
print("STEP 2 : SENSITIVITY ANALYSIS FOR STORAGE DISPATCH — delta")
scenario_cases  = SCENARIOS[4:12]
STORAGE_RESULT2 = runStorageDispatchSensitivitydelta(
    params, scenario_cases, DF_PRICE, base_tariff, DF_LOAD)
plotStorageDispatchSensitivitydelta(
    params, STORAGE_RESULT2, ["Revenue Market", "Revenue Tariff", "Total Revenue"])
'''

'''
print("STEP 3 : SENSITIVITY ANALYSIS — share")
scenario_cases  = SCENARIOS[12:24]
STORAGE_RESULT3 = runStorageDispatchSensitivityShare(
    params, scenario_cases, DF_PRICE, base_tariff, DF_LOAD)
plotStorageDispatchSensitivityShare(params, STORAGE_RESULT3)
'''

'''
print("STEP 4 : EX-ANTE TARIFF VS EX-POST TARIFF")
scenario_cases  = SCENARIOS[24:28]
STORAGE_RESULT4 = runStorageConfiguration(
    params, scenario_cases, DF_PRICE, base_tariff, DF_LOAD)
plotStorageConfiguration(scenario_cases, STORAGE_RESULT4, params)
'''
