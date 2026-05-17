import os

import linopy
import numpy as np
import pandas as pd
import xarray as xr

from utils.datastructs import OptResult


def calculate_slope(g, Cthres):
    y = g.values
    a = np.sum(y)
    b_sum = 0
    for val in y:
        if val > Cthres:
            b_sum += (val - Cthres) * val
    slop = a / b_sum

    return slop


def _data_array(values, index, dim):
    return xr.DataArray(values, dims=[dim], coords={dim: index})


def _choose_solver(tariff_status):
    solver_name = os.getenv("LINOPY_SOLVER")
    if solver_name:
        return solver_name

    if tariff_status == "on" and "gurobi" in linopy.available_solvers:
        return "gurobi"
    if "highs" in linopy.available_solvers:
        return "highs"
    if "gurobi" in linopy.available_solvers:
        return "gurobi"
    return solver_name


def _default_solver_options(solver_name, quadratic_objective):
    if solver_name == "gurobi":
        options = {
            "MIPGap": 0.03,
            "TimeLimit": 1800,
            "MIPFocus": 3,
            "Threads": 32,
        }
        if quadratic_objective:
            options["NonConvex"] = 2
        return options

    if solver_name == "highs":
        return {
            "mip_rel_gap": 0.03,
            "time_limit": 1800,
            "threads": 32,
        }

    return {}


def bat_optimize_(params, price_table, df_load, scenario, size, base_tariff, VOLL, delta):
    tariff_status = params[scenario]["global"]["tariff"]["tariff_status"]

    storage_duration = float(
        params["scenario_1"]["global"]["parameter"]["storage_duration"]
    )

    Rmax = size / storage_duration
    charge_eff = float(params["scenario_1"]["global"]["parameter"]["charge_eff"])
    discharge_eff = float(
        params["scenario_1"]["global"]["parameter"]["discharge_eff"]
    )
    annual_OM = (
        float(params["scenario_1"]["global"]["storage"]["annual_OM"]) * Rmax
    )
    lifetime = float(params["scenario_1"]["global"]["storage"]["lifetime"])
    annual_cap_cost = (
        float(params["scenario_1"]["global"]["storage"]["cap_cost"]) * size / lifetime
    )
    DoD = float(params["scenario_1"]["global"]["parameter"]["DoD"][:-1]) / 1e2
    reserve = (
        float(params["scenario_1"]["global"]["parameter"]["reserve"][:-1]) / 1e2
    )
    configuration = params[scenario]["global"]["tariff"]["configuration"]

    t_index = pd.Index(price_table["t"].tolist(), name="t")
    P_vals = (
        price_table.set_index("t")["DE_LU"]
        .reindex(t_index)
        .to_numpy(dtype=float)
    )
    gridload_vals = (
        df_load.set_index("t")["Residual load [MWh]"]
        .reindex(t_index)
        .to_numpy(dtype=float)
    )

    P = _data_array(P_vals, t_index, "t")
    gridload = _data_array(gridload_vals, t_index, "t")

    SOC0 = size / 2
    SOCmax = size
    SOCmin = reserve * size
    eta_c = charge_eff
    eta_d = discharge_eff

    nodal_load = df_load["Residual load [MWh]"]
    cap_limit = 1 * nodal_load.max(axis=0)
    cap_threshold = (1 - delta) * nodal_load.max(axis=0)

    m = linopy.Model(force_dim_names=True)

    SOC = m.add_variables(lower=SOCmin, upper=SOCmax, coords=[t_index], name="SOC")
    Pd = m.add_variables(
        lower=0,
        upper=SOCmax / storage_duration,
        coords=[t_index],
        name="Pd",
    )
    Pc = m.add_variables(
        lower=0,
        upper=SOCmax / storage_duration,
        coords=[t_index],
        name="Pc",
    )
    net_load = m.add_variables(coords=[t_index], name="net_load")
    chargestate = m.add_variables(coords=[t_index], name="chargestate", binary=True)
    tariff_level = m.add_variables(coords=[t_index], name="tariff_level")
    
    # Constraint SOC level
    m.add_constraints(
    SOC.isel(t=0) == SOC0 + Pc.isel(t=0) * eta_c - Pd.isel(t=0) / eta_d,
    name="constESS_initial",
)
    if len(t_index) > 1:
        SOC_previous = SOC.isel(t=slice(None, -1)).assign_coords(t=t_index[1:])
        m.add_constraints(
            SOC.isel(t=slice(1, None))
            == SOC_previous
            + Pc.isel(t=slice(1, None)) * eta_c
            - Pd.isel(t=slice(1, None)) / eta_d,
            name="constESS",
        )
    # End constraint SOC level
    m.add_constraints(
        Pc <= chargestate * (SOCmax / storage_duration),
        name="defcharge",
    )
    m.add_constraints(
        Pd <= (1 - chargestate) * (SOCmax / storage_duration),
        name="defdischarge",
    )

    if configuration == "ex-post":
        m.add_constraints(net_load == Pc - Pd + gridload, name="netload")
    elif configuration == "ex-ante":
        m.add_constraints(net_load == gridload, name="netload")
    else:
        raise ValueError(f"Unknown tariff configuration: {configuration}")

    if tariff_status == "on":
        shape = params[scenario]["global"]["tariff"]["shape"]
        share = float(params[scenario]["global"]["tariff"]["share"])
        EUR_base = base_tariff
        EUR_high = VOLL

        if shape == "flat":
            is_positive = m.add_variables(
                coords=[t_index], name="is_positive", binary=True
            )
            m.add_constraints(
                net_load <= 1e5 * is_positive,
                name="link_positiveL",
            )
            m.add_constraints(
                net_load >= -1e5 * (1 - is_positive),
                name="link_positiveG",
            )
            m.add_constraints(
                tariff_level == (2 * is_positive - 1) * EUR_base,
                name="define_tariff_level",
            )

        elif shape == "proportional":
            y = nodal_load.values
            slope = EUR_base * share * (np.sum(y)) / np.sum(np.power(y, 2))
            m.add_constraints(
                tariff_level == slope * net_load + EUR_base * (1 - share),
                name="deftariff",
            )

        elif shape == "piecewise":
            x1 = -cap_limit
            x2 = -cap_threshold
            x3 = cap_threshold
            x4 = cap_limit

            y1 = -EUR_high
            y2 = EUR_base
            y3 = EUR_base

            s_index = pd.Index(["s1", "s2", "s3"], name="s")
            sx = _data_array([x1, x2, x3], s_index, "s")
            sy = _data_array(
                [y1, y2 * (1 - share), y3 * (1 - share)],
                s_index,
                "s",
            )
            sslope = _data_array(
                [
                    calculate_slope(nodal_load, x3) * EUR_base * share,
                    (y3 - y2) * (1 - share) / (x3 - x2),
                    calculate_slope(nodal_load, x3) * EUR_base * share,
                ],
                s_index,
                "s",
            )
            sstep_up = _data_array(
                [x2 - x1, x3 - x2, x4 - x3],
                s_index,
                "s",
            )

            sselect = m.add_variables(
                coords=[t_index, s_index],
                name="sselect",
                binary=True,
            )
            sstep = m.add_variables(
                lower=0,
                coords=[t_index, s_index],
                name="sstep",
            )

            m.add_constraints(sselect.sum("s") == 1, name="oneSeg")
            m.add_constraints(
                tariff_level == (sselect * sy + sstep * sslope).sum("s"),
                name="defy",
            )
            m.add_constraints(
                net_load == (sselect * sx + sstep).sum("s"),
                name="defx",
            )
            m.add_constraints(
                sstep <= sselect * sstep_up,
                name="defslope",
            )

        else:
            raise ValueError(f"Unknown tariff shape: {shape}")

        objective_expr = ((Pd - Pc) * (tariff_level + P)).sum()

    else:
        m.add_constraints(tariff_level == 0.01e-15, name="fix_tariff_level")
        objective_expr = ((Pd - Pc) * P).sum()

    m.add_objective(objective_expr, sense="max")

    solver_name = _choose_solver(tariff_status)
    solver_options = _default_solver_options(
        solver_name,
        quadratic_objective=m.is_quadratic,
    )
    status, termination_condition = m.solve(
        solver_name=solver_name,
        **solver_options,
    )

    data = pd.DataFrame(
        {
            "Pc": Pc.solution.values,
            "Pd": Pd.solution.values,
            "SOC": SOC.solution.values,
            "net_load": net_load.solution.values,
            "tariff": tariff_level.solution.values,
        },
        index=t_index,
    )
    data["hour"] = data.index.astype(int)
    data["base_price"] = P_vals
    data["gridload"] = gridload_vals

    info = {}
    info["data"] = data
    info["capacity limit"] = cap_limit
    info["capacity threshold"] = cap_threshold
    info["solver"] = solver_name
    info["termination condition"] = termination_condition

    return OptResult(status, m.objective.value, None, None, info, None)
