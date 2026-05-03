import os
import pandas as pd
import numpy as np
from copy import deepcopy



def path_to_dict(path, value):
    depth = len(path)
    d = {}
    for i, v in enumerate(reversed(path)):
        if i == 0:
            d = {v: value}
        elif i < depth:
            d = {v: deepcopy(d)}
    return d

def update_dict(d_all, d_new, max_depth):
    d_node = d_all
    i = 0
    while i < max_depth:
        new_key = list(d_new.keys())[0]
        if new_key in d_node.keys():
            d_node = d_node[new_key]
            d_new = d_new[new_key]
        else:
            d_node[new_key] = d_new[new_key]
        i += 1
    return d_all


def read(path_scenario_source_file):
    scenarios = pd.read_csv(path_scenario_source_file)
    dict_scenario = {}

    for scenario in range(1, len(scenarios.columns)):
        d_scenario = {}
        for row, variable in enumerate(scenarios.iloc[:, 0]):
            path = variable.split(":")
            depth = len(path)
            value = scenarios.iloc[row, scenario]
            if row == 0:
                d_scenario = path_to_dict(path, value)
            else:
                d_scenario = update_dict(d_scenario, path_to_dict(path, value), depth)
        dict_scenario["scenario_" + str(scenario)] = d_scenario

    return dict_scenario

print()

