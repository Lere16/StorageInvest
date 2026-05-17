# =============================================================================
# LINOPY version — transcription fidèle de storage_dispatch/batterydispatch.py
# Remplace GAMSPy (licence commerciale) par linopy (open-source, MIT)
# Solveur utilisé : HiGHS (libre) via highspy  ou CBC via python-mip
# Toutes les équations, variables et structures de données sont conservées
# à l'identique par rapport à la version GAMSPy originale.
# =============================================================================

import linopy
import pandas as pd
import numpy as np
import os
import sys

from utils.datastructs import OptResult

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS (identiques à la version originale)
# -----------------------------------------------------------------------------

def calculate_slope(g, Cthres):
    """
    Calcule la pente utilisée dans le tarif piecewise.
    g  : Series pandas des charges nodales
    Cthres : seuil de capacité
    """
    y = g.values
    a = np.sum(y)
    b_sum = 0.0
    for val in y:
        if val > Cthres:
            b_sum += (val - Cthres) * val
    slop = a / b_sum
    return slop


# -----------------------------------------------------------------------------
# FONCTION PRINCIPALE D'OPTIMISATION
# Signature identique à la version GAMSPy pour compatibilité avec core.py
# -----------------------------------------------------------------------------

def bat_optimize_(params, price_table, df_load, scenario, size,
                  base_tariff, VOLL, delta):
    """
    Optimise le dispatch d'un système de stockage par batteries.

    Paramètres
    ----------
    params       : dict de scénarios lu par settings.read()
    price_table  : DataFrame avec colonnes ['t', 'DE_LU']
    df_load      : DataFrame avec colonnes ['t', 'Residual load [MWh]']
    scenario     : clé du scénario actif  (ex: 'scenario_1')
    size         : capacité énergie de la batterie [kWh ou MWh selon unités]
    base_tariff  : tarif de réseau de base [EUR/MWh]
    VOLL         : valeur de la perte de charge [EUR/MWh]
    delta        : fraction du pic définissant le seuil de congestion

    Retourne
    --------
    OptResult(status, objective, None, None, info, None)
    """

    # ------------------------------------------------------------------
    # 1. LECTURE DES PARAMÈTRES DU SCÉNARIO (identique à l'original)
    # ------------------------------------------------------------------
    tariff_status = params[scenario]['global']['tariff']['tariff_status']

    storage_duration = float(
        params['scenario_1']['global']['parameter']['storage_duration'])   # 4 h

    Rmax          = size / storage_duration
    charge_eff    = float(params['scenario_1']['global']['parameter']['charge_eff'])
    discharge_eff = float(params['scenario_1']['global']['parameter']['discharge_eff'])
    annual_OM     = float(params['scenario_1']['global']['storage']['annual_OM']) * Rmax
    lifetime      = float(params['scenario_1']['global']['storage']['lifetime'])
    annual_cap_cost = (float(params['scenario_1']['global']['storage']['cap_cost'])
                       * size / lifetime)
    DoD     = float(params['scenario_1']['global']['parameter']['DoD'][:-1]) / 1e2
    reserve = float(params['scenario_1']['global']['parameter']['reserve'][:-1]) / 1e2
    configuration = params[scenario]['global']['tariff']['configuration']

    # ------------------------------------------------------------------
    # 2. INDEX TEMPOREL
    # ------------------------------------------------------------------
    t_index = price_table['t'].tolist()          # liste des pas de temps
    T       = len(t_index)
    t_pos   = {v: i for i, v in enumerate(t_index)}   # t_val -> position 0-based

    # Séries numpy alignées sur t_index
    P_vals        = price_table.set_index('t')['DE_LU'].reindex(t_index).values
    gridload_vals = df_load.set_index('t')['Residual load [MWh]'].reindex(t_index).values

    # ------------------------------------------------------------------
    # 3. SCALAIRES (identiques à l'original)
    # ------------------------------------------------------------------
    SOC0   = size / 2.0
    SOCmax = float(size)
    SOCmin = reserve * size
    eta_c  = charge_eff
    eta_d  = discharge_eff

    Pc_max = SOCmax / storage_duration   # puissance max charge
    Pd_max = SOCmax / storage_duration   # puissance max décharge

    # Charge nodale et seuils de capacité (identiques à l'original)
    nodal_load    = df_load["Residual load [MWh]"]
    cap_limit     = 1.0 * nodal_load.max()
    cap_threshold = (1.0 - delta) * nodal_load.max()

    # ------------------------------------------------------------------
    # 4. INITIALISATION DU MODÈLE LINOPY
    # ------------------------------------------------------------------
    m = linopy.Model(force_dim_names=True)

    coords = t_index   # dimension unique : temps

    # ------------------------------------------------------------------
    # 5. VARIABLES (correspondance exacte avec l'original GAMSPy)
    # ------------------------------------------------------------------
    # SOC : état de charge — free, borné [SOCmin, SOCmax]
    SOC = m.add_variables(lower=SOCmin, upper=SOCmax,
                          coords=[coords], name="SOC")
    

    # Pd : puissance de décharge — positive, bornée [0, Pd_max]
    Pd  = m.add_variables(lower=0.0, upper=Pd_max,
                          coords=coords, name="Pd")

    # Pc : puissance de charge — positive, bornée [0, Pc_max]
    Pc  = m.add_variables(lower=0.0, upper=Pc_max,
                          coords=coords, name="Pc")

    # net_load : charge nette — free (peut être négative si injection)
    net_load = m.add_variables(lower=-np.inf, upper=np.inf,
                               coords=coords, name="net_load")

    # chargestate : binaire — 1=en charge, 0=en décharge
    chargestate = m.add_variables(coords=coords, name="chargestate",
                                  binary=True)

    # tariff_level : niveau de tarif — free
    tariff_level = m.add_variables(lower=-np.inf, upper=np.inf,
                                   coords=coords, name="tariff_level")

    # ------------------------------------------------------------------
    # 6. ÉQUATION D'ÉTAT DE CHARGE (constESS) — identique à l'original
    #    SOC[t] = SOC0              si t est le premier pas
    #           = SOC[t-1] + Pc[t]*eta_c - Pd[t]/eta_d  sinon
    # ------------------------------------------------------------------
    for i, tv in enumerate(t_index):
        if i == 0:
            # Premier pas : SOC[t] == SOC0 + Pc[t]*eta_c - Pd[t]/eta_d
            m.add_constraints(
                SOC.sel(dim_0=tv)
                == SOC0 + Pc.sel(dim_0=tv) * eta_c - Pd.sel(dim_0=tv) / eta_d,
                name=f"constESS_{i}"
            )
        else:
            tv_prev = t_index[i - 1]
            m.add_constraints(
                SOC.sel(dim_0=tv)
                == SOC.sel(dim_0=tv_prev)
                   + Pc.sel(dim_0=tv) * eta_c
                   - Pd.sel(dim_0=tv) / eta_d,
                name=f"constESS_{i}"
            )

    # ------------------------------------------------------------------
    # 7. CONTRAINTES CHARGE / DÉCHARGE SIMULTANÉE (defcharge / defdischarge)
    #    Pc[t] <= chargestate[t] * Pc_max
    #    Pd[t] <= (1 - chargestate[t]) * Pd_max
    # ------------------------------------------------------------------
    m.add_constraints(Pc <= chargestate * Pc_max, name="defcharge")
    m.add_constraints(Pd <= (1 - chargestate) * Pd_max, name="defdischarge")

    # ------------------------------------------------------------------
    # 8. CHARGE NETTE (defnetload) — identique à l'original
    #    ex-post : net_load[t] == gridload[t] + Pc[t] - Pd[t]
    #    ex-ante : net_load[t] == gridload[t]
    # ------------------------------------------------------------------
    gl = linopy.LinearExpression.from_numpy(
        gridload_vals, m, dims=["dim_0"], coords=coords)

    if configuration == "ex-post":
        m.add_constraints(
            net_load == gl + Pc - Pd,
            name="defnetload"
        )
    elif configuration == "ex-ante":
        m.add_constraints(
            net_load == gl,
            name="defnetload"
        )

    # ------------------------------------------------------------------
    # 9. TARIF (identique logiquement à l'original)
    # ------------------------------------------------------------------
    if tariff_status == 'on':

        shape  = params[scenario]['global']['tariff']['shape']
        share  = float(params[scenario]['global']['tariff']['share'])
        EUR_base = base_tariff
        EUR_high = VOLL

        # ---- 9a. TARIF FLAT ---------------------------------------------
        if shape == "flat":
            # is_positive[t] : 1 si net_load[t] >= 0, 0 sinon
            # tariff_level[t] == (2*is_positive[t] - 1) * EUR_base
            # Implémenté via big-M (M = 1e5) — identique à l'original
            M = 1e5
            is_positive = m.add_variables(coords=coords,
                                          name="is_positive", binary=True)

            # net_load[t] <= M * is_positive[t]          (link_positiveL)
            m.add_constraints(net_load <= M * is_positive,
                              name="link_positiveL")
            # net_load[t] >= -M * (1 - is_positive[t])   (link_positiveG)
            m.add_constraints(net_load >= -M * (1 - is_positive),
                              name="link_positiveG")
            # tariff_level[t] == (2*is_positive[t] - 1) * EUR_base
            m.add_constraints(
                tariff_level == (2 * is_positive - 1) * EUR_base,
                name="define_tariff_level"
            )

        # ---- 9b. TARIF PROPORTIONNEL ------------------------------------
        elif shape == "proportional":
            y     = nodal_load.values
            slope = EUR_base * share * np.sum(y) / np.sum(np.power(y, 2))
            # tariff_level[t] == slope * net_load[t] + EUR_base*(1-share)
            m.add_constraints(
                tariff_level == slope * net_load + EUR_base * (1 - share),
                name="deftariff"
            )

        # ---- 9c. TARIF PIECEWISE ----------------------------------------
        elif shape == "piecewise":
            x1 = -cap_limit
            x2 = -cap_threshold
            x3 =  cap_threshold
            x4 =  cap_limit

            y1 = -EUR_high
            y2 =  EUR_base
            y3 =  EUR_base

            segs      = ['s1', 's2', 's3']
            sx_vals   = {'s1': x1, 's2': x2, 's3': x3}
            sy_vals   = {'s1': y1,
                         's2': y2 * (1 - share),
                         's3': y3 * (1 - share)}
            step_up   = {'s1': x2 - x1,
                         's2': x3 - x2,
                         's3': x4 - x3}

            slope_val = calculate_slope(nodal_load, x3) * EUR_base * share
            sslope_vals = {
                's1': slope_val,
                's2': (y3 - y2) * (1 - share) / (x3 - x2),
                's3': slope_val
            }

            # sselect[t, s] : binaire — sélection du segment actif
            # sstep[t, s]   : positive — avancement dans le segment
            ts_coords = [t_index, segs]
            sselect = m.add_variables(
                coords=ts_coords, name="sselect", binary=True)
            sstep   = m.add_variables(
                lower=0.0, upper=np.inf,
                coords=ts_coords, name="sstep")

            # Bornes supérieures de sstep selon le segment
            for s in segs:
                m.add_constraints(
                    sstep.sel(dim_1=s) <= step_up[s] * sselect.sel(dim_1=s),
                    name=f"defslope_{s}"
                )

            # oneSeg[t] : sum_s sselect[t,s] == 1
            m.add_constraints(
                sselect.sum(dims="dim_1") == 1,
                name="oneSeg"
            )

            # defx[t] : net_load[t] == sum_s (sx[s]*sselect[t,s] + sstep[t,s])
            defx_rhs = sum(
                sx_vals[s] * sselect.sel(dim_1=s) + sstep.sel(dim_1=s)
                for s in segs
            )
            m.add_constraints(net_load == defx_rhs, name="defx")

            # defy[t] : tariff_level[t] == sum_s (sy[s]*sselect[t,s] + sstep[t,s]*sslope[s])
            defy_rhs = sum(
                sy_vals[s] * sselect.sel(dim_1=s)
                + sslope_vals[s] * sstep.sel(dim_1=s)
                for s in segs
            )
            m.add_constraints(tariff_level == defy_rhs, name="defy")

            # Borne supérieure sur net_load (originale : net_load.up = cap_limit)
            m.add_constraints(net_load <= cap_limit, name="net_load_upper")

        # ---- Fonction objectif avec tarif (identique à l'original) -----
        # obj == sum_t [ (Pd[t] - Pc[t]) * (P[t] + tariff_level[t]) ]
        P_arr = linopy.LinearExpression.from_numpy(
            P_vals, m, dims=["dim_0"], coords=coords)
        objective_expr = ((Pd - Pc) * P_vals + (Pd - Pc) * tariff_level).sum()
        m.objective = -objective_expr   # linopy minimise → on négative pour MAX

    else:
        # ---- Tarif OFF : fixe tariff_level à quasi-zéro (identique) ----
        m.add_constraints(
            tariff_level == 0.01e-15,
            name="fix_tariff_level"
        )
        # obj == sum_t [ (Pd[t] - Pc[t]) * P[t] ]
        objective_expr = ((Pd - Pc) * P_vals).sum()
        m.objective = -objective_expr   # linopy minimise → négative pour MAX

    # ------------------------------------------------------------------
    # 10. RÉSOLUTION
    # HiGHS est le solveur par défaut de linopy (libre, haute performance).
    # Il supporte les MILP/MIQP. Pour les problèmes purement linéaires
    # (sans piecewise) c'est exact ; pour piecewise (MIQCP relaxé en MILP
    # via reformulation linéaire) HiGHS est optimal.
    # Options alignées sur les intentions de l'original :
    #   mip_gap = 0.03, time_limit = 1800 s
    # ------------------------------------------------------------------
    solver_opts = {
        "mip_rel_gap":  0.03,
        "time_limit":   1800,
        "threads":      32,
        "log_to_stdout": False,
    }
    m.solve(solver="highs", **solver_opts)

    # ------------------------------------------------------------------
    # 11. EXTRACTION DES RÉSULTATS (identique à l'original)
    # ------------------------------------------------------------------
    Pc_sol          = Pc.solution.values
    Pd_sol          = Pd.solution.values
    SOC_sol         = SOC.solution.values
    net_load_sol    = net_load.solution.values
    tariff_sol      = tariff_level.solution.values

    data = pd.DataFrame({
        "Pc":       Pc_sol,
        "Pd":       Pd_sol,
        "SOC":      SOC_sol,
        "net_load": net_load_sol,
        "tariff":   tariff_sol,
    }, index=t_index)

    data['hour']       = data.index.astype(int)
    data['base_price'] = P_vals
    data['gridload']   = gridload_vals

    status    = str(m.status)
    objective = float(-m.objective.value)   # on re-négative pour avoir la valeur MAX

    info = {}
    info["data"]               = data
    info["capacity limit"]     = cap_limit
    info["capacity threshold"] = cap_threshold

    return OptResult(status, objective, None, None, info, None)
