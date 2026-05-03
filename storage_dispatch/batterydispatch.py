# GAMSPY version-----------------------------------------------------------------

from gamspy import (
    Container,
    Set,
    Parameter,
    Variable,
    Equation,
    Model,
    Sum,
    Ord,
)
from gamspy.math import exp, abs, sign, sqrt
import pandas as pd
import numpy as np
import os
import sys

from utils.datastructs import OptResult

# HELPER FUNCTIONS:-------------------------------------------------------


def calculate_slope(g, Cthres):
    y = g.values
    a = np.sum(y)
    b_sum = 0
    for val in y:
        if val > Cthres:
            b_sum += (val - Cthres) * val
    slop = a / b_sum
    
    return slop

def bat_optimize_(params, price_table, df_load, scenario, size, base_tariff, VOLL, delta):
    
    #node=params['scenario_1']['global']['network']['node']
    tariff_status=params[scenario]['global']['tariff']['tariff_status']
    
    storage_duration = float(params['scenario_1']['global']['parameter']['storage_duration'])  # 4 hours of storage duration
    
    Rmax= size / storage_duration
    charge_eff = float(params['scenario_1']['global']['parameter']['charge_eff'])
    discharge_eff = float(params['scenario_1']['global']['parameter']['discharge_eff'])
    annual_OM = float(params['scenario_1']['global']['storage']['annual_OM'])*Rmax 
    lifetime = float(params['scenario_1']['global']['storage']['lifetime'])
    annual_cap_cost = float(params['scenario_1']['global']['storage']['cap_cost'])*size /lifetime
    DoD = float(params['scenario_1']['global']['parameter']['DoD'][:-1])/1e2
    reserve = float(params['scenario_1']['global']['parameter']['reserve'][:-1])/1e2
    configuration = params[scenario]['global']['tariff']['configuration'] 
    
    #MODEL INITIALIZATION
    #bat = Container(working_directory=os.path.join(os.getcwd(), "debugg_bat"))
    bat = Container(
        system_directory=os.getenv("SYSTEM_DIRECTORY", None),
        delayed_execution=int(os.getenv("DELAYED_EXECUTION", False)),
    )
    
    # Parameters 
    t=Set(bat, name = "t", records = price_table.t.tolist(), description = " hours")
    P=Parameter(bat,"P", domain=[t], records=price_table[['t', 'DE_LU']], description="Day ahead Price")
    gridload = Parameter(bat, 'gridload', domain=[t], records= df_load[["t","Residual load [MWh]"]])
    #gridload.records.to_csv("gridload.csv")
    #P.records.to_csv("P.csv")
    
    #SCALARS
    SOC0 = Parameter(bat, name="SOC0", records=size/2)
    SOCmax = Parameter(bat, name="SOCmax", records=size)
    SOCmin = Parameter(bat, name="SOCmin", records=reserve*size)
    eta_c = Parameter(bat, name="eta_c", records= charge_eff)
    eta_d = Parameter(bat, name="eta_d", records= discharge_eff)
    
    # Variables
    SOC = Variable(bat, name="SOC", type="free", domain=t)
    Pd = Variable(bat, name="Pd", type="Positive", domain=t)
    Pc = Variable(bat, name="Pc", type="Positive", domain=t)
    net_load = Variable(bat, 'net_load', domain=[t], type='free')
    chargestate = Variable(bat, 'chargestate', domain=[t], type='binary')
    tariff_level = Variable(bat, 'tarrif_level', domain=[t], type='free')
    
    obj = Variable(
        bat, name="obj", type="free", description="Objective function"
    )
    
    # Equations 
    SOC.up[t] = SOCmax
    SOC.lo[t] = SOCmin
    
    Pc.up[t] = SOCmax/storage_duration
    Pc.lo[t] = 0
    Pd.up[t] = SOCmax/storage_duration
    Pd.lo[t] = 0
    
    constESS = Equation(bat, name="constESS", type="regular", domain=t)
    defobj = Equation(bat, "defobj")
    
    
    constESS[t] = (
        SOC[t]
        == SOC0.where[Ord(t) == 1]
        + SOC[t.lag(1)].where[Ord(t) > 1]
        + Pc[t] * eta_c
        - Pd[t] / eta_d
    )
    
    #periodESS = Equation(bat, name="periodESS", type="regular", domain=t)
    #periodESS[t] = SOC['0'] == SOC[t].where[t.last]
    
    # Avoid charging and dishcraging at the same time
    defcharge = Equation(bat, name="defcharge", type="regular", domain=t)
    defdischarge = Equation(bat, name="defdischarge", type="regular", domain=t)
    defcharge[t] = Pc[t] <= chargestate[t] * Pc.up[t]
    defdischarge[t] = Pd[t] <= (1-chargestate[t]) * Pd.up[t]
    
    defnetload = Equation(bat, name="netload", domain=[t])
    if configuration == "ex-post":
        defnetload[t] = net_load[t] == gridload[t] + Pc[t] - Pd[t]
    elif configuration == "ex-ante":
        defnetload[t] = net_load[t] == gridload[t]
        
     #Initilaize cap_limit and cap_threshold for info dictionnary 
    nodal_load = df_load["Residual load [MWh]"]
    cap_limit = 1*nodal_load.max(axis=0) #manage to exact cap_limit
    cap_threshold = (1-delta)*nodal_load.max(axis=0) 
    
    
    if tariff_status == 'on':
        
        # Read scalars from params
        shape=params[scenario]['global']['tariff']['shape']
        share=float(params[scenario]['global']['tariff']['share'])
        EUR_base = base_tariff
        EUR_high = VOLL
        
        if shape == "flat":
             #tariff_level.fx[t]= EUR_base
            define_tariff_level = Equation(bat, name="define_tariff_level", domain=[t])
            
            is_positive = Variable(bat, 'is_positive', domain=[t], type='binary')
            link_positiveL = Equation(bat, name="link_positiveL", domain=[t])
            link_positiveG = Equation(bat, name="link_positiveG", domain=[t])
            link_positiveL[t] = net_load[t] <= 1e5 * is_positive[t]
            link_positiveG[t] = net_load[t] >= -1e5 * (1 - is_positive[t])
            define_tariff_level[t] = tariff_level[t] == (2 * is_positive[t] - 1)* EUR_base
            
        elif shape== "proportional":
            deftariff = Equation(bat, name="deftariff", domain=[t])
            #calculate slope 
            y = nodal_load.values
            slope= EUR_base*share*(np.sum(y))/np.sum(np.power(y, 2))
            
            deftariff[t] = tariff_level[t] == slope*net_load[t]+EUR_base*(1-share)
            
        elif shape == "piecewise":
    
        
            x1 = -cap_limit
            x2 = -cap_threshold
            x3 = cap_threshold
            x4 = cap_limit
            
            
            y1 = -EUR_high
            y2 = EUR_base
            y3 = EUR_base
            
        
            #3 segments 
            s = Set(bat, 's', records=['s1','s2','s3'])
            sx = Parameter(bat, 'sx', domain=[s], records=[ ['s1',x1], ['s2',x2], ['s3',x3]])
            sy = Parameter(bat, 'sy', domain=[s], records=[ ['s1',y1], ['s2',y2*(1-share)], ['s3',y3*(1-share)]])
            sslope = Parameter(bat, 'sslope', domain=[s])
            
            sslope['s1'] = calculate_slope(nodal_load, x3)*EUR_base*share
            sslope['s2'] = (y3-y2)*(1-share)/(x3-x2)
            sslope['s3'] = calculate_slope(nodal_load, x3)*EUR_base*share
            
            sselect = Variable(bat, 'sselect', domain=[t,s], type='binary')
            sstep = Variable(bat, 'sstep', domain=[t,s], type='Positive')
            sstep.up[t,'s1'] = x2-x1
            sstep.up[t,'s2'] = x3-x2
            sstep.up[t,'s3'] = x4-x3
        
            # Equations
            oneSeg = Equation(bat, name="oneSeg", domain=[t])
            defy = Equation(bat, name="defy", domain=[t])
            defx = Equation(bat, name="defx", domain=[t])
            defslope = Equation(bat, name="defslope", domain=[t,s])
            
            oneSeg[t] = Sum(s, sselect[t,s]) == 1
            defy[t] = tariff_level[t] == Sum(s, sy[s]*sselect[t,s] + sstep[t,s]*sslope[s])
            defx[t] = net_load[t] == Sum(s, sx[s]*sselect[t,s] + sstep[t,s])
            defslope[t,s] = sstep[t,s] <= sstep.up[t,s]*sselect[t,s] 
            
        # define ojective function when tariff is on
        defobj[...] = obj == Sum(t, (Pd[t] - Pc[t]) * (P[t] + tariff_level[t])) - 0#(annual_cap_cost + annual_OM)
        
        opt = Model(
            bat,
            name="opt",
            equations=bat.getEquations(),
            problem="MIQCP",
            sense="MAX",
            objective=obj,
        )
    else: # objective function Without tariff
        tariff_level.fx[t]= 0.01e-15
        defobj[...] = obj == Sum(t, (Pd[t] - Pc[t]) * P[t]) - 0#(annual_cap_cost + annual_OM)
        opt = Model(
            bat,
            name="opt",
            equations=bat.getEquations(),
            problem="MIP",
            sense="MAX",
            objective=obj,
        )
    
     
    opt.solve(solver="CPLEX", solver_options={'optimalitytarget': 3, 'subalg': 4, 'mipdisplay': 5, 'mipgap':0.03,'timelimit': 1800, 'mipemphasis': 3, 'threads': 32}, ) # output=sys.stdout
    #reporting data and parameters 
    rep = Parameter(bat, name="rep", domain=[t, "*"])
    rep[t, "Pc"] = Pc.l[t]
    rep[t, "Pd"] = Pd.l[t]
    rep[t, "SOC"] = SOC.l[t]
    rep[t, "net_load"] = net_load.l[t]
    rep[t, "tariff"] = tariff_level.l[t]
    
    data=rep.pivot()
    data['hour'] = data.index
    data['base_price'] = P.records['value'].values
    data['hour'] = data['hour'].astype(int)
    data['gridload']= gridload.records["value"].values
    status=opt.status
    objective=opt.objective_value
    info={}
    info["data"]=data
    info["capacity limit"]=cap_limit
    info["capacity threshold"]=cap_threshold

    
    return OptResult(status, objective, None, None, info, None)

    
    
