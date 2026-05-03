import os
import yaml
from collections import defaultdict
import pandas as pd
import numpy as np
from utils.datastructs import OptDataCEPTech, OptDataCEPNode, OptDataCEPLine, LatLon, OptDataCEP, ClustData, ClustData_f, FullInputData, OptDataCEPCost,OptVariableLine
from utils.optvariable import OptVariable
from utils.utilsfun import check_column
from typing import Tuple, Dict, List, Any, Union


#-----------------------------------------------------------------------------------------------------------------
# ------------------------------------ LOAD TIME SERIES DATA------------------------------------------------------------

# Load time Series data
def load_timeseries_data_provided(region="GER_2", T=24, years=[2016]):
    # Check for the existence of the region in data
    data_directory = os.path.normpath(os.path.join(os.getcwd(), 'data'))
    if region not in os.listdir(data_directory):
        raise Exception(f"The region {region} is not found. The provided regions are: GER_1: Germany 1 node, GER_18: Germany 18 nodes, CA_1: California 1 node, CA_14: California 14 nodes, TX_1: Texas 1 node")

    # Generate the data path based on application and region, att=[]
    data_path = os.path.normpath(os.path.join(os.getcwd(), 'data', region, 'TS'))
    return load_timeseries_data(data_path, region=region, T=T, years=years)


def load_timeseries_data(data_path: str, region: str = "none", T: int = 24, years: List[int] = [2016], att: List[str] = []) -> ClustData:
    dt = {}
    num = 0
    K = 0
    if os.path.isdir(data_path):
        for full_data_name in os.listdir(data_path):
            if full_data_name.endswith(".csv"):
                data_name = full_data_name.split(".")[0]
                if not att or data_name in att:
                    K = add_timeseries_data1(dt, data_name, data_path, K=K, T=T, years=years)
    elif os.path.isfile(data_path):
        full_data_name = os.path.basename(data_path)
        data_name = full_data_name.split(".")[0]
        K = add_timeseries_data(dt, data_name, os.path.dirname(data_path), K=K, T=T, years=years)
    else:
        raise ValueError(f"The path {data_path} is neither recognized as a directory nor as a file")
    ts_input_data = ClustData_f(FullInputData(region, years, num, dt), K, T)
    return ts_input_data


def add_timeseries_data1(dt: Dict[str, List[float]],
                        data_name: str,
                        data_path: str,
                        K: int = 0,
                        T: int = 24,
                        years: List[int] = [2016]) -> Dict[str, List[float]]:
    # Load the data
    data_df = pd.read_csv(os.path.join(data_path, f"{data_name}.csv"))
    return add_timeseries_data(dt, data_name, data_df, K=K, T=T, years=years)


def add_timeseries_data(dt, data_name, data, K=0, T=24, years=[2016]):
    # find the right years to select
    time_name = find_column_name(data, ["Timestamp", "timestamp", "Time", "time", "Zeit", "zeit", "Date", "date", "Datum", "datum"], error=False)
    year_name = find_column_name(data, ["year", "Year", "jahr", "Jahr"])
    data_selected = data[data[year_name].isin(years)] 
    col_name = data_selected.columns
    # Check if the column is a time or year column
    for name in col_name:
        if name not in [time_name, year_name]:
            # Calculate the number of time steps based on the length of the data
            K_calc = int(len(data_selected[name]) / T)
            # Check if the number of time steps is consistent with the previous column
            if K_calc != K and K != 0:
                raise ValueError(f"The time_series {name} has K={K_calc} != K={K} of the previous")
            else:
                K = K_calc
            # Extract the data for the current time step
            dt[data_name + "-" + str(name)] = [float(x) for x in data_selected[name][:int(T * K)]]
    return K

def find_column_name(data, possible_names, error=True):
    found_name = None
    for name in possible_names:
        if hasattr(data, name):
            found_name = name
            break

    if found_name is None and error:
        raise ValueError("None of the possible column names were found in the DataFrame")

    return found_name



#-----------------------------------------------------------------------------------------------------------------
# ------------------------------------ TECHNOLOGIES DATA-----------------------------------------------------------

def load_cep_data_techs(data_path):
    tab = pd.read_csv(os.path.join(data_path, "techs.csv"))
    if 'tech' not in tab.columns:
        raise ValueError("No column called 'tech' in 'techs.csv'")
    
    techs = {}
    
    for tech in tab['tech'].unique():
        name = tech
        categ = tab.loc[tab['tech'] == tech, 'categ'].values[0]
        sector = tab.loc[tab['tech'] == tech, 'sector'].values[0]
        eff = tab.loc[tab['tech'] == tech, 'eff'].values[0]
        time_series = tab.loc[tab['tech'] == tech, 'time_series'].values[0]
        lifetime = tab.loc[tab['tech'] == tech, 'lifetime'].values[0]
        financial_lifetime = tab.loc[tab['tech'] == tech, 'financial_lifetime'].values[0]
        discount_rate = tab.loc[tab['tech'] == tech, 'discount_rate'].values[0]
        
        annuityfactor = round((1 + discount_rate) ** min(financial_lifetime, lifetime) * discount_rate / ((1 + discount_rate) ** min(financial_lifetime, lifetime) - 1), 9)
        
        techs[tech] = OptDataCEPTech(name, categ, sector, eff, time_series, lifetime, financial_lifetime, discount_rate, annuityfactor)
    
    return techs

#-----------------------------------------------------------------------------------------------------------------
# ------------------------------------ NODES DATA-------------------------------------------------------------------

def load_cep_data_nodes(data_path, techs):
    tab = pd.read_csv(os.path.join(data_path, "nodes.csv"))
    check_column(tab, ["node", "infrastruct"]) # modified
    nodes = {}
    for tech in techs:
        for node in tab["node"].unique():
            name = node
            power_ex = tab.loc[(tab["node"] == node) & (tab["infrastruct"] == "ex"), tech].iloc[0]
            data = tab.loc[(tab["node"] == node) & (tab["infrastruct"] == "lim"), tech]
            power_lim = float('inf') if data.empty else data.iloc[0]
            region = tab.loc[tab["node"] == node, "region"].iloc[0]
            latlon = LatLon(tab.loc[tab["node"] == node, "lat"].iloc[0], tab.loc[tab["node"] == node, "lon"].iloc[0])
            #nodes[tech, node] = OptDataCEPNode(name, power_ex, power_lim, region, latlon)
            nodes[node] = OptDataCEPNode(name, power_ex, power_lim, region, latlon)
    return nodes

def load_cep_data_nodes_2(data_path, techs):
    tab = pd.read_csv(os.path.join(data_path, "nodes.csv"))
    check_column(tab, ["node", "infrastruct"]) # modified
    nodes = {}
    for tech in techs:
        for node in tab["node"].unique():
            name = node
            power_ex = tab.loc[(tab["node"] == node) & (tab["infrastruct"] == "ex"), tech].iloc[0]
            data = tab.loc[(tab["node"] == node) & (tab["infrastruct"] == "lim"), tech]
            power_lim = float('inf') if data.empty else data.iloc[0]
            region = tab.loc[tab["node"] == node, "region"].iloc[0]
            latlon = LatLon(tab.loc[tab["node"] == node, "lat"].iloc[0], tab.loc[tab["node"] == node, "lon"].iloc[0])
            nodes[tech, node] = OptDataCEPNode(name, power_ex, power_lim, region, latlon)
            #nodes[node] = OptDataCEPNode(name, power_ex, power_lim, region, latlon)
    return nodes



# #-----------------------------------------------------------------------------------------------------------------
# ------------------------------------ LINES DATA------------------------------------------------------------
    
def load_cep_data_lines(data_path, techs):
    if os.path.isfile(os.path.join(data_path, "lines.csv")):
        tab = pd.read_csv(os.path.join(data_path, "lines.csv"))
        # Check existence of necessary column
        check_column(tab, ["line"])  # modified

        # Create empty OptVariable
        lines = {}
        for tech in pd.unique(tab['tech']):
            for line in pd.unique(tab['line']):
                # name
                name = line
                # node_start
                node_start = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'node_start'].values[0]
                # node_end
                node_end = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'node_end'].values[0]
                # reactance
                reactance = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'reactance'].values[0]
                # resistance
                resistance = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'resistance'].values[0]
                # power_ex
                power_ex = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'power_ex'].values[0]
                # power_lim
                power_lim = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'power_lim'].values[0]
                # circuits
                circuits = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'circuits'].values[0]
                # voltage
                voltage = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'voltage'].values[0]
                # length
                length = tab.loc[(tab['tech'] == tech) & (tab['line'] == line), 'length'].values[0]
                # eff calculate the efficiency provided as eff/km in techs
                # η=1-l_{line}⋅(1-η_{tech}) [-]
                eff = 1 - length * (1 - techs[tech].eff)
                lines[tech, line] = OptDataCEPLine(name, node_start, node_end, reactance, resistance, power_ex, power_lim, circuits, voltage, length, eff)
                #lines[line] = OptDataCEPLine(name, node_start, node_end, reactance, resistance, power_ex, power_lim, circuits, voltage, length, eff)
        return lines
    else:
        lines = {}
        return lines


# #-----------------------------------------------------------------------------------------------------------------
# ------------------------------------ COSTS DATA-------------------------------------------------------------------

def load_cep_data_costs(data_path: str, techs, nodes) -> OptVariable:
    tab = pd.read_csv(os.path.join(data_path, "costs.csv"))
    impacts = tab.columns[tab.columns.get_loc("|")+1:]
    costs = defaultdict(float)
    for tech in techs:
        for node in nodes:
            for year in tab["year"].unique():
                for impact in impacts:
                    account = "cap_fix"
                    cap_location = get_location_data(nodes, tab, tech, node, "cap")
                    total_cap_cost = tab.loc[(tab["tech"] == tech) & (tab["location"] == cap_location) & (tab["account"] == "cap") & (tab["year"] == year)][impact].iloc[0]
                    if impact == impacts[0]:
                        annulized_cap_cost = round(total_cap_cost * techs[tech].annuityfactor)
                    else:
                        annulized_cap_cost = round(total_cap_cost / techs[tech].lifetime)
                    fix_location = get_location_data(nodes, tab, tech, node, "fix")
                    fix_cost = tab.loc[(tab["tech"] == tech) & (tab["location"] == fix_location) & (tab["account"] == "fix") & (tab["year"] == year)][impact].iloc[0]
                    #costs[(tech, node, year, account, impact)] = annulized_cap_cost + fix_cost
                    costs[tech, node, year, account, impact] = annulized_cap_cost + fix_cost
                    account = "var"
                    var_location = get_location_data(nodes, tab, tech, node, account)
                    var_cost = tab.loc[(tab["tech"] == tech) & (tab["location"] == var_location) & (tab["account"] == account) & (tab["year"] == year)][impact].iloc[0]
                    #costs[(tech, node, year, account, impact)] = var_cost
                    costs[tech, node, year, account, impact] = var_cost
    return OptDataCEPCost(costs)



def get_location_data(nodes, tab, tech, node, account):
    # determine region for this technology and node based on information in nodes
    region = nodes[node].region
    
    # determine regions provided for this tech and this account in the data
    locations_data = tab[(tab["tech"] == tech) & (tab["account"] == account)]["location"].unique()
    
    # check if either specific `node`, `region` or a value for `all` regions is given
    if node in locations_data:
        return node
    elif region in locations_data:
        return region
    elif "all" in locations_data:
        return "all"
    else:
        raise ValueError(f"region {region} not provided in {tab}")
    



def load_cep_data(data_path: str, region: str = "none") -> OptDataCEP:
    techs = load_cep_data_techs(data_path)
    nodes = load_cep_data_nodes(data_path, techs)
    lines = load_cep_data_lines(data_path, techs)
    costs = load_cep_data_costs(data_path, techs, nodes)
    return OptDataCEP(region, costs, techs, nodes, lines)



def load_cep_data_provided(region: str):
    data_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data", region))
    return load_cep_data(data_path, region=region)




