import os
import settings
import pandas as pd
#from storage_dispatch.batterydispatch_for_kWh_ import bat_optimize_
from storage_dispatch.batterydispatch import bat_optimize_

def readStorageDispatchScenario(SCENARIO_LIST):
    # Set scenario path
    INPUT_PATH=os.path.join(os.path.dirname(__file__),"data", "input")
    SCENARIO_FILE = os.path.join(INPUT_PATH, "storage_dispatch_scenarios.csv")

    #read input
    params=settings.read(SCENARIO_FILE)
    SCENARIOS= [list(params.keys())[i-1] for i in SCENARIO_LIST]

    return SCENARIOS, params

def readLoadPrice(area):
    # Set scenario path
    DATA_PATH=os.path.join(os.path.dirname(__file__),"data", "input")
    LOAD_FILE = os.path.join(DATA_PATH, "actual_consumption_"+str(area)+".csv")
    LOAD_PRICE_FILE = os.path.join(DATA_PATH, "day_ahead_prices.csv")
    
    # Read CSV files
    load_df = pd.read_csv(LOAD_FILE)
    price_df = pd.read_csv(LOAD_PRICE_FILE)
    
    load_df['year'] = load_df['Start date'].str.split('/').str[-1].str[:4].astype(int)
    price_df['year'] = price_df['Start date'].str.split('/').str[-1].str[:4].astype(int)

    # Create "t" as the time step within each year
    load_df['t'] = load_df.groupby('year').cumcount()
    price_df['t'] = price_df.groupby('year').cumcount()
    
    return load_df, price_df

def readLoadPrice_odl(load_file, price_file):
    # Set scenario path
    DATA_PATH=os.path.join(os.path.dirname(__file__),"data", "input")
    LOAD_FILE = os.path.join(DATA_PATH, "compiled_load.csv")
    LOAD_PRICE_FILE = os.path.join(DATA_PATH, "compiled_price.csv")
    
    # Read CSV files
    load_df = pd.read_csv(LOAD_FILE)
    price_df = pd.read_csv(LOAD_PRICE_FILE)
    
    load_df['year'] = load_df['Time'].str.split('/').str[-1].str[:4].astype(int)
    price_df['year'] = price_df['Time'].str.split('/').str[-1].str[:4].astype(int)

    # Create "t" as the time step within each year
    load_df['t'] = load_df.groupby('year').cumcount()
    price_df['t'] = price_df.groupby('year').cumcount()
    
    return load_df, price_df

    
def runStorageDispatchCases(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    
    start = int(params['scenario_1']['global']['config']['start']) # start year for horizon simualtion
    end = int(params['scenario_1']['global']['config']['end']) # end year for horizon simulation
    VOLL = float(params['scenario_1']['global']['network']['VOLL'])
    delta = float(params['scenario_1']['global']['tariff']['delta'])
    size = int(params['scenario_1']['global']['parameter']['size'])
    
    STORAGE_RESULT={}
    
    #directory to save data
    output_dir = 'results/CSV'
    os.makedirs(output_dir, exist_ok=True)
    
     
    for scenario in scenario_cases:
        print(scenario)
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            print(year)
            #shadow_price = SHADOW_PRICE[SHADOW_PRICE['year'] == year]['Day-ahead Total Load Forecast [MW]'] 
            #df_load = DF_LOAD[DF_LOAD['year'] == year]['Day-ahead Price [EUR/MWh']
            shadow_price = SHADOW_PRICE[SHADOW_PRICE['year'] == year]
            shadow_price = shadow_price.reset_index(drop=True)
            df_load = DF_LOAD[DF_LOAD['year'] == year]
            df_load = df_load.reset_index(drop=True)
            storage_dispatch = bat_optimize_(params, shadow_price, df_load, scenario, size, base_tariff, VOLL, delta)
            current_data = storage_dispatch.info["data"]
            current_data['Pc'] = current_data['Pc'] * (-1)
            current_data['year'] = year
            df_combined = pd.concat([df_combined, current_data], ignore_index=True)
            
        
        df_combined['price'] = df_combined["base_price"] + df_combined["tariff"]
        df_combined['dispatch'] = df_combined["Pd"] + df_combined["Pc"]
        
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join('results/CSV', f"storage_result_{scenario}.csv"), index=False)
    
            
    STORAGE_RESULT_TEMP=STORAGE_RESULT.copy()
    recovered_cost_tariff = []
    recovered_cost_price = []
    for scenario, data in STORAGE_RESULT_TEMP.items():
        
        if scenario == 'scenario_1':
            continue
        
        df = data
        df['net_load_tariff'] = df['net_load'] * df['tariff']
        net_load_tariff_sum = df['net_load_tariff'].sum()
        recovered_cost_tariff.append({'scenario': scenario, 'recovered_cost': net_load_tariff_sum})
        
        df['net_load_price'] = df['net_load'] * df['price']
        net_load_price_sum = df['net_load_price'].sum()
        recovered_cost_price.append({'scenario': scenario, 'recovered_cost': net_load_price_sum})
        
    results_tariff = pd.DataFrame(recovered_cost_tariff)
    results_price = pd.DataFrame(recovered_cost_price)
    results_tariff.to_csv(os.path.join('results/CSV', f"recovered_costs_by_tariff.csv"), index=False)
    results_price.to_csv(os.path.join('results/CSV', f"recovered_costs_by_price.csv"), index=False)

    return STORAGE_RESULT
    
    
    
def runStorageDispatchSensitivitydelta(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    
    start=int(params[scenario_cases[0]]['global']['config']['start']) # start year for horizon simualtion
    end=int(params[scenario_cases[0]]['global']['config']['end']) # end year for horizon simulation
    VOLL = float(params[scenario_cases[0]]['global']['network']['VOLL'])
    size= int(params[scenario_cases[0]]['global']['parameter']['size'])
    
    STORAGE_RESULT={}
    output_dir_csv = 'results/CSV'
    os.makedirs(output_dir_csv, exist_ok=True)
    
    for scenario in scenario_cases:
        print(scenario)
        delta = float(params[scenario]['global']['tariff']['delta'])
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            print(year)
            shadow_price = SHADOW_PRICE[SHADOW_PRICE['year'] == year]
            shadow_price = shadow_price.reset_index(drop=True)
            df_load = DF_LOAD[DF_LOAD['year'] == year]
            df_load = df_load.reset_index(drop=True)
            storage_dispatch = bat_optimize_(params, shadow_price, df_load, scenario, size, base_tariff, VOLL, delta)
            current_data=storage_dispatch.info["data"]
            current_data['Pc'] = current_data['Pc'] * (-1)
            current_data['year'] = year
            # Concatenate the current data to the overall DataFrame
            df_combined = pd.concat([df_combined, current_data], ignore_index=True)
        
        df_combined['price'] = df_combined["base_price"] + df_combined["tariff"]
        df_combined['dispatch'] = df_combined["Pd"] + df_combined["Pc"]
        
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join(output_dir_csv, f"storage_result_{scenario}.csv"), index=False)

    return STORAGE_RESULT


def runStorageDispatchSensitivityShare(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    
    start=int(params[scenario_cases[0]]['global']['config']['start']) # start year for horizon simualtion
    end=int(params[scenario_cases[0]]['global']['config']['end']) # end year for horizon simulation
    VOLL = float(params[scenario_cases[0]]['global']['network']['VOLL'])
    size= int(params[scenario_cases[0]]['global']['parameter']['size'])
    delta = float(params[scenario_cases[0]]['global']['tariff']['delta'])
    
    STORAGE_RESULT={}
    output_dir_csv = 'results/CSV'
    os.makedirs(output_dir_csv, exist_ok=True)
    for scenario in scenario_cases:
        print(scenario)
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            shadow_price = SHADOW_PRICE[SHADOW_PRICE['year'] == year]
            shadow_price = shadow_price.reset_index(drop=True)
            df_load = DF_LOAD[DF_LOAD['year'] == year]
            df_load = df_load.reset_index(drop=True)
            storage_dispatch = bat_optimize_(params, shadow_price, df_load, scenario, size, base_tariff, VOLL, delta)
            current_data=storage_dispatch.info["data"]
            current_data['Pc'] = current_data['Pc'] * (-1)
            current_data['year'] = year
            # Concatenate the current data to the overall DataFrame
            df_combined = pd.concat([df_combined, current_data], ignore_index=True)
        
        df_combined['price'] = df_combined["base_price"] + df_combined["tariff"]
        df_combined['dispatch'] = df_combined["Pd"] + df_combined["Pc"]
        
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join(output_dir_csv, f"storage_result_{scenario}.csv"), index=False)
    
    return STORAGE_RESULT



def runStorageConfiguration(params, scenario_cases, SHADOW_PRICE, base_tariff, DF_LOAD):
    
    start = int(params[scenario_cases[0]]['global']['config']['start']) 
    end = int(params[scenario_cases[0]]['global']['config']['end']) 
    VOLL = float(params[scenario_cases[0]]['global']['network']['VOLL'])
    size = int(params[scenario_cases[0]]['global']['parameter']['size'])
    delta = float(params[scenario_cases[0]]['global']['tariff']['delta'])
    
    start_hour=int(params[scenario_cases[0]]['global']['plot']['start_hour'])
    end_hour= int(params[scenario_cases[0]]['global']['plot']['end_hour'])
    
    
    
    STORAGE_RESULT={}
    output_dir_csv = 'results/CSV'
    os.makedirs(output_dir_csv, exist_ok=True)
    
    
    for scenario in scenario_cases:
        print(scenario)
        df_combined = pd.DataFrame()
        for year in range(start, end + 1):
            print(year)
            #shadow_price = SHADOW_PRICE[SHADOW_PRICE['year'] == year]
            shadow_price = SHADOW_PRICE[(SHADOW_PRICE['year'] == year) & (SHADOW_PRICE['t'].between(start_hour, end_hour))]
            shadow_price = shadow_price.reset_index(drop=True)
            #df_load = DF_LOAD[DF_LOAD['year'] == year]
            df_load = DF_LOAD[(DF_LOAD['year'] == year) & (DF_LOAD['t'].between(start_hour, end_hour))]
            df_load = df_load.reset_index(drop=True)
            storage_dispatch = bat_optimize_(params, shadow_price, df_load, scenario, size, base_tariff, VOLL, delta)
            current_data = storage_dispatch.info["data"]
            current_data["total_demand"]=current_data["gridload"]+current_data["Pc"]
            current_data["dispatch_load"]=current_data["gridload"]+current_data["Pc"]-current_data["Pd"]
            #current_data["dispatch_load"]=current_data["net_load"]
            
            
            current_data["injection_load"]=current_data["gridload"] - current_data["Pd"]
            #current_data['Pc'] = current_data['Pc'] * (-1)
            current_data['year'] = year
            current_data['capacity limit'] = storage_dispatch.info["capacity limit"]
            current_data['capacity threshold'] = storage_dispatch.info["capacity threshold"]
            df_combined = pd.concat([df_combined, current_data], ignore_index=True)
        
        
        df_combined['price'] = df_combined["base_price"] + df_combined["tariff"]
        df_combined['dispatch'] = df_combined["Pd"] - df_combined["Pc"]
        
        STORAGE_RESULT[scenario] = df_combined
        df_combined.to_csv(os.path.join(output_dir_csv, f"storage_result_CONFIGURATION_{scenario}.csv"), index=False)
    
    return STORAGE_RESULT




