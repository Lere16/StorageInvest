"""
main.py  -  Entry point for the battery dispatch and investment project
========================================================================
Available steps:

  STEP 0  Hurdle rate calculation (CAPM / WACC)
  STEP 1  Dispatch comparison across tariff schemes
  STEP 2  Sensitivity analysis on delta
  STEP 3  Sensitivity analysis on share
  STEP 4  Ex-ante vs ex-post comparison
  STEP 5  Investment frontier (investment module)
"""


from core import (
    readStorageDispatchScenario,
    readLoadPrice,
    runStorageDispatchCases,
    runStorageDispatchSensitivitydelta,
    runStorageDispatchSensitivityShare,
    runStorageConfiguration,
    # -- New ------------------------------
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
# Read scenarios and data
# ---------------------------------------------------------------------------
SCENARIO_LIST = list(range(1, 30))
SCENARIOS, params = readStorageDispatchScenario(SCENARIO_LIST)

base_tariff = float(params["scenario_1"]["global"]["network"]["base_tariff"])
area        = params["scenario_1"]["global"]["network"]["area"]

DF_LOAD, DF_PRICE = readLoadPrice(area)


# ---------------------------------------------------------------------------
# STEP 0 : Hurdle Rate (CAPM / WACC)
# ---------------------------------------------------------------------------
print("STEP 0 : HURDLE RATE CALCULATION (CAPM / WACC)")
HR_RESULT = computeHurdleRate(
    params,
    scenario="scenario_1",
    # Default values - adjust according to the market context:
    beta=0.85,             # systematic risk of storage, close to utilities
    market_premium=0.055,  # European market risk premium
    equity_share=0.40,     # typical capital structure for an energy project
    cost_of_debt=0.02,    # cost of debt (OAT + spread)
    tax_rate= 0.05,
)


# ---------------------------------------------------------------------------
# STEP 1 : Dispatch comparison by tariff scheme
# ---------------------------------------------------------------------------

#print("\nSTEP 1 : STORAGE DISPATCH INCLUDING TARIFF SIGNALS")
#scenario_cases  = SCENARIOS[:4]
#selected_years  = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]

#STORAGE_RESULT1 = runStorageDispatchCases(
#    params, scenario_cases, DF_PRICE, base_tariff, DF_LOAD
#)
#plotStorageDispatchCases(scenario_cases, STORAGE_RESULT1, selected_years, params)


# ---------------------------------------------------------------------------
# STEP 5 : Investment frontier  <- NEW
# ---------------------------------------------------------------------------
print("\nSTEP 5 : INVESTMENT FRONTIER BY TARIFF SCHEME")

# max_invest scenarios (indices 28-44 in the CSV -> scenario_29 to scenario_45)
# Adjust the range according to your file.
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
        hr_result= HR_RESULT,
        output_dir="results/investment",
        verbose=True,
    )
    print("\nSummary table saved to results/investment/investment_summary.csv")
else:
    print("  No investment scenario found - check SCENARIO_LIST.")


# ---------------------------------------------------------------------------
# Commented steps (uncomment as needed)
# ---------------------------------------------------------------------------

'''
print("STEP 2 : SENSITIVITY ANALYSIS FOR STORAGE DISPATCH - delta")
scenario_cases  = SCENARIOS[4:12]
STORAGE_RESULT2 = runStorageDispatchSensitivitydelta(
    params, scenario_cases, DF_PRICE, base_tariff, DF_LOAD)
plotStorageDispatchSensitivitydelta(
    params, STORAGE_RESULT2, ["Revenue Market", "Revenue Tariff", "Total Revenue"])
'''

'''
print("STEP 3 : SENSITIVITY ANALYSIS - share")
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
