import numpy as np
from typing_extensions import Literal
from typing import Tuple, Dict, List, Any, Union
import math
from numbers import Number
from collections import defaultdict


### data structures ###
class InputData:
    pass

class OptData(InputData):
    pass

class TSData(InputData):
    pass

class AbstractClustResult:
    pass

# Added functions and constructors 

class FullInputData:
    def __init__(self, region: str, years: List[int], N: int, data: Dict[str, List]):
        self.region = region
        self.years = years
        self.N = N
        self.data = data

class ClustData:
    def __init__(self, region: str, years: List[int], K: int, T: int, data: Dict[str, List], weights: List[float], mean: Dict[str, List], sdv: Dict[str, List], delta_t: List[List[float]], k_ids: List[int]):
        self.region = region
        self.years = years
        self.K = K
        self.T = T
        self.data = data
        self.weights = weights
        self.mean = mean
        self.sdv = sdv
        self.delta_t = delta_t
        self.k_ids = k_ids
        

def ClustData_fun(region: str,
              years: List[int],
              K: int,
              T: int,
              data: Dict[str, List],
              weights: List[float],
              k_ids: List[int],
              delta_t: List[List[float]] = None,
              mean: Dict[str, List] = {},
              sdv: Dict[str, List] = {}
              ):
    if delta_t is None:
        delta_t = [[1.0] * K for _ in range(T)]
    # Rest of the code...
    if not data:
        raise ValueError("Need to provide at least one input data stream")
    mean_sdv_provided = (mean and sdv)
    if not mean_sdv_provided:
        for k, v in data.items():
            mean[k] = [0.0] * T
            sdv[k] = [1.0] * T
    # TODO check if right keywords are used
    return ClustData(region, years, K, T, data, weights, mean, sdv, delta_t, k_ids) # Constructor 


def ClustData_f(data, K, T):
    
    data_reshape = {}
    for k, v in data.data.items():
        data_reshape[k] = np.array(v).reshape(K, T).T
    return ClustData_fun(data.region, data.years, K, T, data_reshape, np.ones(K), list(range(1, K+1)))

class ClustResult(AbstractClustResult):
    def __init__(self, clust_data, cost, config):
        self.clust_data = clust_data
        self.cost = cost
        self.config = config

#-------------------------------------------------

class OptModelCEP:
    def __init__(self, model, info: list[str], sets):
        self.model = model
        self.info = info
        self.sets = sets


      
class OptVariable(np.ndarray):
    def __new__(cls, data: np.ndarray, axes: Tuple, lookup: Dict, axes_names: np.ndarray, type_: str):
        obj = np.asarray(data).view(cls)
        obj.axes = axes
        obj.lookup = lookup
        obj.axes_names = axes_names
        obj.type_ = type_
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.axes = getattr(obj, 'axes', None)
        self.lookup = getattr(obj, 'lookup', None)
        self.axes_names = getattr(obj, 'axes_names', None)
        self.type_ = getattr(obj, 'type_', None)        

class OptResult:
    def __init__(self, status: str, objective: float, variables: Dict[str, Any], config: Dict[str, Any], info: Dict[str, Any], sets: Dict[str, Any]):
        self.status = status
        self.objective = objective
        self.variables = variables
        self.config = config
        self.info = info
        self.sets = sets

class OptDataCEP(OptData):
    def __init__(self, region: str, costs, techs, nodes, lines):
        self.region = region
        self.costs = costs
        self.techs = techs
        self.nodes = nodes
        self.lines = lines
        

class LatLon:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    @classmethod
    def from_dict(cls, d: dict):
        return cls(d['lat'], d['lon'])

    def __repr__(self):
        return f"LatLon(lat={self.lat}°, lon={self.lon}°)"

    def __eq__(self, other):
        if isinstance(other, LatLon):
            return self.lat == other.lat and self.lon == other.lon
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.lat, self.lon))

    def isapprox(self, other, atol=1e-6, **kwargs):
        R = 6.371e6  # Earth's radius in meters
        return abs(self.lat - other.lat) <= atol * 180 / (R * math.pi) and abs(self.lon - other.lon) <= atol * 180 / (R * math.pi)
    

class OptDataCEPNode(OptData):
    def __init__(self, name: str, power_ex: Union[int, float], power_lim: Union[int, float], region: str, latlon: LatLon):
        self.name = name
        self.power_ex = power_ex
        self.power_lim = power_lim
        self.region = region
        self.latlon = latlon


class OptDataCEPLine(OptData):
            def __init__(self, name: str, node_start: str, node_end: str, reactance: Number, resistance: Number, power_ex: Number, power_lim: Number, circuits: int, voltage: Number, length: Number, eff: Number):
                self.name = name
                self.node_start = node_start
                self.node_end = node_end
                self.reactance = reactance
                self.resistance = resistance
                self.power_ex = power_ex
                self.power_lim = power_lim
                self.circuits = circuits
                self.voltage = voltage
                self.length = length
                self.eff = eff

        
class OptDataCEPTech(OptData):
        def __init__(self, name, categ, sector, eff, time_series, lifetime, financial_lifetime, discount_rate, annuityfactor):
            self.name = name
            self.categ = categ
            self.sector = sector
            self.eff = eff
            self.time_series = time_series
            self.lifetime = lifetime
            self.financial_lifetime = financial_lifetime
            self.discount_rate = discount_rate
            self.annuityfactor = annuityfactor

class OptDataCEPCost(OptData):
    """ Constructor for costs data"""
    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.tech = np.unique([key[0] for key in data_dict.keys()])
        self.node= np.unique([key[1] for key in data_dict.keys()])
        self.year= np.unique([key[2] for key in data_dict.keys()])
        self.account= np.unique([key[3] for key in data_dict.keys()])
        self.impact= np.unique([key[4] for key in data_dict.keys()])
        self.data=data_dict
          

class OptVariableLine(OptData):
    """ Constructor for line data"""
    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.tech = np.unique([key[0] for key in data_dict.keys()])
        self.line = np.unique([key[1] for key in data_dict.keys()])
        self.data = self.construct_matrix()

    def construct_matrix(self):
        data = np.array([[self.data_dict[(tech, line)] for line in self.line] for tech in self.tech])
        return data

    def display_info(self):
        print("Dimension 1 - tech:", self.tech)
        print("Dimension 2 - line:", self.line)
        print("Data:")
        print(self.data)
        
        
        
class Scenario:
    def __init__(self, descriptor: str, clust_res: Any, opt_res: OptResult):
        self.descriptor = descriptor
        self.clust_res = clust_res
        self.opt_res = opt_res
