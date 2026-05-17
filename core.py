"""
core.py  (extended version with investment module)
==================================================
Project orchestration functions:
  - read scenarios and data
  - run the dispatch optimizer
  - NEW: investment frontier analysis (CAPM + NPV)
"""


import os
import settings
import pandas as pd

from storage_dispatch.batterydispatch import bat_optimize_

# -- New investment module ---------------------------------------------------
from investment.capm import compute_hurdle_rate, capm_from_params, CAPMInputs
from investment.investment_frontier import run_investment_frontier


# ===========================================================================
# Data loading
# ===========================================================================

def readStorageDispatchScenario(SCENARIO_LIST):
    INPUT_PATH   = os.path.join(os.path.dirname(__file__), "data", "input")
    SCENARIO_FILE = os.path.join(INPUT_PATH, "storage_dispatch_scenarios.csv")
    params   = settings.read(SCENARIO_FILE)
    SCENARIOS = [list(params.keys())[i - 1] for i in SCENARIO_LIST]
    return SCENARIOS, params


def readLoadPrice(area):
    DATA_PATH       = os.path.join(os.path.dirname(__file__), "data", "input")
    LOAD_FILE       = os.path.join(DATA_PATH, f"actual_consumption_{area}.csv")
    LOAD_PRICE_FILE = os.path.join(DATA_PATH, "day_ahead_prices.csv")

    load_df  = pd.read_csv(LOAD_FILE)
    price_df = pd.read_csv(LOAD_PRICE_FILE)

    load_df["year"]  = load_df["Start date"].str.split("/").str[-1].str[:4].astype(int)
    price_df["year"] = price_df["Start date"].str.split("/").str[-1].str[:4].astype(int)

    load_df["t"]  = load_df.groupby("year").cumcount()
    price_df["t"] = price_df.groupby("year").cumcount()

    return load_df, price_df


def readLoadPrice_odl(load_file, price_file):
    DATA_PATH       = os.path.join(os.path.dirname(__file__), "data", "input")
    LOAD_FILE       = os.path.join(DATA_PATH, "compiled_load.csv")
    LOAD_PRICE_FILE = os.path.join(DATA_PATH, "compiled_price.csv")

    load_df  = pd.read_csv(LOAD_FILE)
    price_df = pd.read_csv(LOAD_PRICE_FILE)

    load_df["year"]  = load_df["Time"].str.split("/").str[-1].str[:4].astype(int)
    price_df["year"] = price_df["Time"].str.split("/").str[-1].str[:4].astype(int)

    load_df["t"]  = load_df.groupby("year").cumcount()
    price_df["t"] = price_df.groupby("year").cumcount()

    return load_df, price_df


# ===========================================================================
# Dispatch cases
# ===========================================================================

def runStorageDispatchCases(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    start = int(params["scenario_1"]["global"]["config"]["start"])
    end   = int(params["scenario_1"]["global"]["config"]["end"])
    VOLL  = float(params["scenario_1"]["global"]["network"]["VOLL"])
    delta = float(params["scenario_1"]["global"]["tariff"]["delta"])
    size  = int(params["scenario_1"]["global"]["parameter"]["size"])

    STORAGE_RESULT = {}
    output_dir = "results/CSV"
    os.makedirs(output_dir, exist_ok=True)

    for scenario in scenario_cases:
        print(scenario)
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            print(year)
            shadow_price = SHADOW_PRICE[SHADOW_PRICE["year"] == year].reset_index(drop=True)
            df_load      = DF_LOAD[DF_LOAD["year"] == year].reset_index(drop=True)
            storage_dispatch = bat_optimize_(params, shadow_price, df_load, scenario,
                                            size, base_tariff, VOLL, delta)
            cur = storage_dispatch.info["data"]
            cur["Pc"]   = cur["Pc"] * (-1)
            cur["year"] = year
            df_combined = pd.concat([df_combined, cur], ignore_index=True)

        df_combined["price"]    = df_combined["base_price"] + df_combined["tariff"]
        df_combined["dispatch"] = df_combined["Pd"] + df_combined["Pc"]
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join(output_dir, f"storage_result_{scenario}.csv"), index=False)

    # Recovered costs
    STORAGE_RESULT_TEMP   = STORAGE_RESULT.copy()
    recovered_cost_tariff = []
    recovered_cost_price  = []
    for scenario, data in STORAGE_RESULT_TEMP.items():
        if scenario == "scenario_1":
            continue
        df = data
        df["net_load_tariff"] = df["net_load"] * df["tariff"]
        recovered_cost_tariff.append({"scenario": scenario,
                                      "recovered_cost": df["net_load_tariff"].sum()})
        df["net_load_price"] = df["net_load"] * df["price"]
        recovered_cost_price.append({"scenario": scenario,
                                     "recovered_cost": df["net_load_price"].sum()})

    pd.DataFrame(recovered_cost_tariff).to_csv(
        os.path.join(output_dir, "recovered_costs_by_tariff.csv"), index=False)
    pd.DataFrame(recovered_cost_price).to_csv(
        os.path.join(output_dir, "recovered_costs_by_price.csv"), index=False)

    return STORAGE_RESULT


def runStorageDispatchSensitivitydelta(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    start = int(params[scenario_cases[0]]["global"]["config"]["start"])
    end   = int(params[scenario_cases[0]]["global"]["config"]["end"])
    VOLL  = float(params[scenario_cases[0]]["global"]["network"]["VOLL"])
    size  = int(params[scenario_cases[0]]["global"]["parameter"]["size"])

    STORAGE_RESULT = {}
    output_dir = "results/CSV"
    os.makedirs(output_dir, exist_ok=True)

    for scenario in scenario_cases:
        print(scenario)
        delta       = float(params[scenario]["global"]["tariff"]["delta"])
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            print(year)
            shadow_price = SHADOW_PRICE[SHADOW_PRICE["year"] == year].reset_index(drop=True)
            df_load      = DF_LOAD[DF_LOAD["year"] == year].reset_index(drop=True)
            cur = bat_optimize_(params, shadow_price, df_load, scenario,
                                size, base_tariff, VOLL, delta).info["data"]
            cur["Pc"]   = cur["Pc"] * (-1)
            cur["year"] = year
            df_combined = pd.concat([df_combined, cur], ignore_index=True)

        df_combined["price"]    = df_combined["base_price"] + df_combined["tariff"]
        df_combined["dispatch"] = df_combined["Pd"] + df_combined["Pc"]
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join(output_dir, f"storage_result_{scenario}.csv"), index=False)

    return STORAGE_RESULT


def runStorageDispatchSensitivityShare(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    start = int(params[scenario_cases[0]]["global"]["config"]["start"])
    end   = int(params[scenario_cases[0]]["global"]["config"]["end"])
    VOLL  = float(params[scenario_cases[0]]["global"]["network"]["VOLL"])
    size  = int(params[scenario_cases[0]]["global"]["parameter"]["size"])
    delta = float(params[scenario_cases[0]]["global"]["tariff"]["delta"])

    STORAGE_RESULT = {}
    output_dir = "results/CSV"
    os.makedirs(output_dir, exist_ok=True)

    for scenario in scenario_cases:
        print(scenario)
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            shadow_price = SHADOW_PRICE[SHADOW_PRICE["year"] == year].reset_index(drop=True)
            df_load      = DF_LOAD[DF_LOAD["year"] == year].reset_index(drop=True)
            cur = bat_optimize_(params, shadow_price, df_load, scenario,
                                size, base_tariff, VOLL, delta).info["data"]
            cur["Pc"]   = cur["Pc"] * (-1)
            cur["year"] = year
            df_combined = pd.concat([df_combined, cur], ignore_index=True)

        df_combined["price"]    = df_combined["base_price"] + df_combined["tariff"]
        df_combined["dispatch"] = df_combined["Pd"] + df_combined["Pc"]
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join(output_dir, f"storage_result_{scenario}.csv"), index=False)

    return STORAGE_RESULT


def runStorageConfiguration(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    start      = int(params[scenario_cases[0]]["global"]["config"]["start"])
    end        = int(params[scenario_cases[0]]["global"]["config"]["end"])
    VOLL       = float(params[scenario_cases[0]]["global"]["network"]["VOLL"])
    size       = int(params[scenario_cases[0]]["global"]["parameter"]["size"])
    delta      = float(params[scenario_cases[0]]["global"]["tariff"]["delta"])
    start_hour = int(params[scenario_cases[0]]["global"]["plot"]["start_hour"])
    end_hour   = int(params[scenario_cases[0]]["global"]["plot"]["end_hour"])

    STORAGE_RESULT = {}
    output_dir = "results/CSV"
    os.makedirs(output_dir, exist_ok=True)

    for scenario in scenario_cases:
        print(scenario)
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            print(year)
            shadow_price = SHADOW_PRICE[
                (SHADOW_PRICE["year"] == year) &
                (SHADOW_PRICE["t"].between(start_hour, end_hour))
            ].reset_index(drop=True)
            df_load = DF_LOAD[
                (DF_LOAD["year"] == year) &
                (DF_LOAD["t"].between(start_hour, end_hour))
            ].reset_index(drop=True)

            result = bat_optimize_(params, shadow_price, df_load, scenario,
                                   size, base_tariff, VOLL, delta)
            cur = result.info["data"].copy()
            cur["total_demand"]   = cur["gridload"] + cur["Pc"]
            cur["dispatch_load"]  = cur["gridload"] + cur["Pc"] - cur["Pd"]
            cur["injection_load"] = cur["gridload"] - cur["Pd"]
            cur["year"]               = year
            cur["capacity limit"]     = result.info["capacity limit"]
            cur["capacity threshold"] = result.info["capacity threshold"]
            df_combined = pd.concat([df_combined, cur], ignore_index=True)

        df_combined["price"]    = df_combined["base_price"] + df_combined["tariff"]
        df_combined["dispatch"] = df_combined["Pd"] - df_combined["Pc"]
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(
            os.path.join(output_dir, f"storage_result_CONFIGURATION_{scenario}.csv"),
            index=False,
        )

    return STORAGE_RESULT


# ===========================================================================
# NEW: Investment module
# ===========================================================================

def computeHurdleRate(params, scenario: str = "scenario_1",
                      beta: float = 0.85,
                      market_premium: float = 0.055,
                      equity_share: float = 0.40,
                      cost_of_debt: float = 0.045,
                      tax_rate: float = 0.30):
    """
    Calculate the hurdle rate via CAPM/WACC.

    The risk-free rate (rf) and the project risk premium (k) are read
    from the scenario file. The other parameters can be overridden
    through the function arguments.

    Parameters
    ----------
    params : dict          Parameters from the scenario file.
    scenario : str         Reference scenario (default: scenario_1).
    beta : float           Project beta (systematic risk).
    market_premium : float Market risk premium (ERP).
    equity_share : float   Equity share in the capital structure.
    cost_of_debt : float   Pre-tax cost of debt.
    tax_rate : float       Marginal tax rate.

    Returns
    -------
    HurdleRateResult
    """
    
    p = params.get(scenario, params.get("scenario_1", {}))
    global_p = p.get("global", {}).get("parameter", {})

    rf = float(global_p.get("rf", 0.03))
    k  = float(global_p.get("k",  0.01))

    capm_inputs = CAPMInputs(
        rf=rf,
        beta=beta,
        market_premium=market_premium,
        equity_share=equity_share,
        debt_share=1.0 - equity_share,
        cost_of_debt=cost_of_debt,
        tax_rate=tax_rate,
        project_risk_premium=k,
    )

    from investment.capm import compute_hurdle_rate
    hr = compute_hurdle_rate(capm_inputs)
    print(hr.summary())
    return hr


def runInvestmentFrontier(params, scenario_cases, DF_PRICE, DF_LOAD,
                          hr_result=None,
                          output_dir: str = "results/investment",
                          verbose: bool = True):
    """
    Run the investment frontier analysis for each scenario.

    For each scenario, progressively increases the battery size
    by the `step_size` defined in the scenario CSV and computes the
    NPV. Stops as soon as the NPV becomes negative.

    Parameters
    ----------
    params : dict
    scenario_cases : list[str]
    DF_PRICE, DF_LOAD : pd.DataFrame
    hr_result : HurdleRateResult, optional
        If None, automatically computed from scenario_1.
    output_dir : str
    verbose : bool

    Returns
    -------
    pd.DataFrame  Summary table.
    """
    if hr_result is None:
        hr_result = computeHurdleRate(params)

    return run_investment_frontier(
        params=params,
        scenario_cases=scenario_cases,
        DF_PRICE=DF_PRICE,
        DF_LOAD=DF_LOAD,
        hr_result=hr_result,
        output_dir=output_dir,
        verbose=verbose,
    )
