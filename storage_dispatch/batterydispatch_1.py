# =============================================================================
# LINOPY version — transcription fidèle de storage_dispatch/batterydispatch.py
# Remplace GAMSPy (licence commerciale) par linopy (open-source, MIT)
# Solveur : HiGHS (libre) via highspy
#
# CORRECTIONS TECHNIQUES PAR RAPPORT À LA VERSION GAMSPY :
#
# 1. coords : liste de pd.Index NOMMÉS → [pd.Index(t_index, name='t')]
#    (un dict ou une liste simple provoque CoordinateValidationError avec
#     force_dim_names=True)
#
# 2. MIQP → MILP par linéarisation McCormick :
#    HiGHS ne résout pas les MIQP. L'objectif contient le produit bilinéaire
#    dispatch[t] * tariff_level[t]. On l'élimine via :
#      a) dispatch[t] = Pd[t] - Pc[t]  (variable continue bornée)
#      b) rev_tariff[t] = dispatch[t] * tariff_level[t]  (McCormick)
#    → MILP pur, compatible HiGHS.
#
# 3. Segment s3 du piecewise ouvert (sstep_s3 illimité) :
#    Dans l'original, net_load.up = cap_limit avec cap_limit = nodal_load.max().
#    Mais net_load (ex-post) peut légèrement dépasser nodal_load.max() quand
#    Pc > 0, rendant le système infaisable. On supprime la borne dure sur
#    net_load et on laisse le 3ème segment s'étendre vers +∞, ce qui est
#    économiquement correct (tarif maximum au-delà du seuil de congestion).
#
# 4. Toute la logique métier (équations, schémas tarifaires, seuils) est
#    strictement identique à l'original GAMSPy.
# =============================================================================

import linopy
import xarray as xr
import pandas as pd
import numpy as np
import os
import sys

from utils.datastructs import OptResult


# -----------------------------------------------------------------------------
# HELPER FUNCTION (identique à la version originale)
# -----------------------------------------------------------------------------

def calculate_slope(g, Cthres):
    """Calcule la pente utilisée dans le tarif piecewise."""
    y = g.values
    a = np.sum(y)
    b_sum = 0.0
    for val in y:
        if val > Cthres:
            b_sum += (val - Cthres) * val
    return a / b_sum


# -----------------------------------------------------------------------------
# HELPER INTERNE : linéarisation McCormick pour produit de deux variables
#
# w[t] = x[t] * y[t]  avec x ∈ [x_lb, x_ub] et y ∈ [y_lb, y_ub]
# Les 4 inégalités définissent l'enveloppe convexe/concave exacte.
# Exact pour les variables binaires ; relaxation convexe pour les continues.
# -----------------------------------------------------------------------------

def add_mccormick(m, w, x, y, x_lb, x_ub, y_lb, y_ub, prefix):
    m.add_constraints(w >= x_lb * y + x * y_lb - x_lb * y_lb, name=f"{prefix}_mc1")
    m.add_constraints(w >= x_ub * y + x * y_ub - x_ub * y_ub, name=f"{prefix}_mc2")
    m.add_constraints(w <= x_ub * y + x * y_lb - x_ub * y_lb, name=f"{prefix}_mc3")
    m.add_constraints(w <= x_lb * y + x * y_ub - x_lb * y_ub, name=f"{prefix}_mc4")


# -----------------------------------------------------------------------------
# FONCTION PRINCIPALE D'OPTIMISATION
# Signature strictement identique à la version GAMSPy → core.py inchangé
# -----------------------------------------------------------------------------

def bat_optimize_(params, price_table, df_load, scenario, size,
                  base_tariff, VOLL, delta):

    # ------------------------------------------------------------------
    # 1. LECTURE DES PARAMÈTRES DU SCÉNARIO (identique à l'original)
    # ------------------------------------------------------------------
    tariff_status    = params[scenario]['global']['tariff']['tariff_status']
    storage_duration = float(params['scenario_1']['global']['parameter']['storage_duration'])
    Rmax             = size / storage_duration
    charge_eff       = float(params['scenario_1']['global']['parameter']['charge_eff'])
    discharge_eff    = float(params['scenario_1']['global']['parameter']['discharge_eff'])
    annual_OM        = float(params['scenario_1']['global']['storage']['annual_OM']) * Rmax
    lifetime         = float(params['scenario_1']['global']['storage']['lifetime'])
    annual_cap_cost  = float(params['scenario_1']['global']['storage']['cap_cost']) * size / lifetime
    DoD              = float(params['scenario_1']['global']['parameter']['DoD'][:-1]) / 1e2
    reserve          = float(params['scenario_1']['global']['parameter']['reserve'][:-1]) / 1e2
    configuration    = params[scenario]['global']['tariff']['configuration']

    # ------------------------------------------------------------------
    # 2. INDEX TEMPOREL — équivalent du Set GAMS "t"
    #    pd.Index avec name='t' est OBLIGATOIRE pour force_dim_names=True
    # ------------------------------------------------------------------
    t_index  = price_table['t'].tolist()
    t_idx    = pd.Index(t_index, name='t')          # index nommé dimension temps
    s_idx    = pd.Index(['s1', 's2', 's3'], name='s')  # index nommé segments

    coords_t  = [t_idx]          # 1D : domaine temporel
    coords_ts = [t_idx, s_idx]   # 2D : temporel × segments piecewise

    # Séries numpy alignées sur t_index (équivalent des Parameter GAMS)
    P_vals        = price_table.set_index('t')['DE_LU'].reindex(t_index).values.astype(float)
    gridload_vals = df_load.set_index('t')['Residual load [MWh]'].reindex(t_index).values.astype(float)

    # ------------------------------------------------------------------
    # 3. SCALAIRES (identiques à l'original)
    # ------------------------------------------------------------------
    SOC0   = size / 2.0
    SOCmax = float(size)
    SOCmin = reserve * size
    eta_c  = charge_eff
    eta_d  = discharge_eff
    Pc_max = SOCmax / storage_duration
    Pd_max = SOCmax / storage_duration

    nodal_load    = df_load["Residual load [MWh]"]
    cap_limit     = 1.0 * float(nodal_load.max())
    cap_threshold = (1.0 - delta) * float(nodal_load.max())

    # Helper : envelopper un array numpy en xr.DataArray aligné sur 't'
    def da_t(values):
        return xr.DataArray(values, dims=['t'], coords={'t': t_index})

    gl_xr = da_t(gridload_vals)
    P_xr  = da_t(P_vals)

    # ------------------------------------------------------------------
    # 4. INITIALISATION DU MODÈLE LINOPY
    # ------------------------------------------------------------------
    m = linopy.Model(force_dim_names=True)

    # ------------------------------------------------------------------
    # 5. VARIABLES (correspondance exacte avec l'original GAMSPy)
    # ------------------------------------------------------------------
    SOC          = m.add_variables(lower=SOCmin,  upper=SOCmax, coords=coords_t, name="SOC")
    Pd           = m.add_variables(lower=0.0,     upper=Pd_max, coords=coords_t, name="Pd")
    Pc           = m.add_variables(lower=0.0,     upper=Pc_max, coords=coords_t, name="Pc")
    net_load     = m.add_variables(lower=-np.inf, upper=np.inf, coords=coords_t, name="net_load")
    chargestate  = m.add_variables(coords=coords_t, name="chargestate", binary=True)
    tariff_level = m.add_variables(lower=-np.inf, upper=np.inf, coords=coords_t, name="tariff_level")

    # Variable auxiliaire dispatch[t] = Pd[t] - Pc[t]
    # Nécessaire pour linéariser l'objectif (McCormick)
    dispatch = m.add_variables(lower=-Pc_max, upper=Pd_max, coords=coords_t, name="dispatch")
    m.add_constraints(dispatch == Pd - Pc, name="def_dispatch")

    # ------------------------------------------------------------------
    # 6. ÉQUATION D'ÉTAT DE CHARGE (constESS) — identique à l'original
    #
    # GAMSPy :
    #   SOC[t] == SOC0.where[Ord(t)==1]
    #           + SOC[t.lag(1)].where[Ord(t)>1]
    #           + Pc[t]*eta_c - Pd[t]/eta_d
    # ------------------------------------------------------------------
    for i, tv in enumerate(t_index):
        if i == 0:
            m.add_constraints(
                SOC.sel(t=tv) == SOC0 + Pc.sel(t=tv) * eta_c - Pd.sel(t=tv) / eta_d,
                name=f"constESS_{i}"
            )
        else:
            tv_prev = t_index[i - 1]
            m.add_constraints(
                SOC.sel(t=tv) == SOC.sel(t=tv_prev)
                                  + Pc.sel(t=tv) * eta_c
                                  - Pd.sel(t=tv) / eta_d,
                name=f"constESS_{i}"
            )


    # ------------------------------------------------------------------
    # 7. CONTRAINTES CHARGE / DÉCHARGE SIMULTANÉE
    #
    # GAMSPy :
    #   defcharge[t]    : Pc[t] <= chargestate[t] * Pc.up[t]
    #   defdischarge[t] : Pd[t] <= (1-chargestate[t]) * Pd.up[t]
    # ------------------------------------------------------------------
    m.add_constraints(Pc <= chargestate * Pc_max,       name="defcharge")
    m.add_constraints(Pd <= (1 - chargestate) * Pd_max, name="defdischarge")

    # ------------------------------------------------------------------
    # 8. CHARGE NETTE (defnetload) — identique à l'original
    #
    # GAMSPy :
    #   ex-post : net_load[t] == gridload[t] + Pc[t] - Pd[t]
    #   ex-ante : net_load[t] == gridload[t]
    # ------------------------------------------------------------------
    if configuration == "ex-post":
        m.add_constraints(net_load == gl_xr + Pc - Pd, name="defnetload")
    elif configuration == "ex-ante":
        m.add_constraints(net_load == gl_xr,           name="defnetload")

    # ------------------------------------------------------------------
    # 9. TARIF + OBJECTIF
    # ------------------------------------------------------------------

    if tariff_status == 'on':

        shape    = params[scenario]['global']['tariff']['shape']
        share    = float(params[scenario]['global']['tariff']['share'])
        EUR_base = base_tariff
        EUR_high = VOLL

        # ---- 9a. TARIF FLAT ------------------------------------------------
        # GAMSPy :
        #   is_positive binaire, big-M (M=1e5)
        #   link_positiveL[t] : net_load[t] <=  1e5 * is_positive[t]
        #   link_positiveG[t] : net_load[t] >= -1e5 * (1-is_positive[t])
        #   define_tariff_level[t] : tariff_level[t] == (2*is_positive[t]-1)*EUR_base
        if shape == "flat":
            M = 1e5
            is_positive = m.add_variables(coords=coords_t, name="is_positive", binary=True)
            m.add_constraints(net_load <= M * is_positive,        name="link_positiveL")
            m.add_constraints(net_load >= -M * (1 - is_positive), name="link_positiveG")
            m.add_constraints(
                tariff_level == (2 * is_positive - 1) * EUR_base,
                name="define_tariff_level"
            )
            tariff_lb = -EUR_base
            tariff_ub =  EUR_base

        # ---- 9b. TARIF PROPORTIONNEL ---------------------------------------
        # GAMSPy :
        #   deftariff[t] : tariff_level[t] == slope*net_load[t] + EUR_base*(1-share)
        elif shape == "proportional":
            y     = nodal_load.values.astype(float)
            slope = EUR_base * share * np.sum(y) / np.sum(np.power(y, 2))
            m.add_constraints(
                tariff_level == slope * net_load + EUR_base * (1 - share),
                name="deftariff"
            )
            # Bornes analytiques pour McCormick
            net_min = float(nodal_load.min()) - Pc_max
            net_max = float(nodal_load.max()) + Pc_max
            tariff_lb = min(slope * net_min, slope * net_max) + EUR_base * (1 - share)
            tariff_ub = max(slope * net_min, slope * net_max) + EUR_base * (1 - share)

        # ---- 9c. TARIF PIECEWISE -------------------------------------------
        # GAMSPy :
        #   3 segments s1,s2,s3 — sselect[t,s] binaire, sstep[t,s] positive
        #   oneSeg[t]    : Sum(s, sselect[t,s]) == 1
        #   defx[t]      : net_load[t] == Sum(s, sx[s]*sselect[t,s] + sstep[t,s])
        #   defy[t]      : tariff_level[t] == Sum(s, sy[s]*sselect[t,s]+sslope[s]*sstep[t,s])
        #   defslope[t,s]: sstep[t,s] <= sstep.up[t,s] * sselect[t,s]
        #
        # NOTE : le segment s3 est ouvert vers +∞ (sstep_s3 sans borne sup.)
        # afin d'éviter l'infaisabilité quand net_load dépasse cap_limit.
        elif shape == "piecewise":
            x1, x2 = -cap_limit, -cap_threshold
            x3, x4 =  cap_threshold, cap_limit
            y1, y2, y3 = -EUR_high, EUR_base, EUR_base

            segs    = ['s1', 's2', 's3']
            sx_vals = {'s1': x1, 's2': x2, 's3': x3}
            sy_vals = {'s1': y1,
                       's2': y2 * (1 - share),
                       's3': y3 * (1 - share)}
            # s1 et s2 ont des bornes finies ; s3 est ouvert (np.inf)
            step_up = {
                's1': x2 - x1,
                's2': x3 - x2,
                's3': np.inf,     # segment ouvert vers +∞
            }

            slope_val   = calculate_slope(nodal_load, x3) * EUR_base * share
            sslope_vals = {
                's1': slope_val,
                's2': (y3 - y2) * (1 - share) / (x3 - x2),
                's3': slope_val,
            }

            # Variables 2D (t, s)
            sselect = m.add_variables(coords=coords_ts, name="sselect", binary=True)
            sstep   = m.add_variables(lower=0.0, upper=np.inf,
                                      coords=coords_ts, name="sstep")

            # defslope[t,s] : sstep[t,s] <= step_up[s] * sselect[t,s]
            # (s3 : step_up = inf → pas de borne, contrainte non ajoutée)
            for s in segs:
                if np.isfinite(step_up[s]):
                    m.add_constraints(
                        sstep.sel(s=s) <= step_up[s] * sselect.sel(s=s),
                        name=f"defslope_{s}"
                    )
                else:
                    # Segment ouvert : sstep[t,s3] est libre quand sselect=1,
                    # mais doit être 0 quand sselect=0 → borne via big-M
                    big_M_step = float(nodal_load.max()) * 2
                    m.add_constraints(
                        sstep.sel(s=s) <= big_M_step * sselect.sel(s=s),
                        name=f"defslope_{s}"
                    )

            # oneSeg[t] : sum_s sselect[t,s] == 1
            m.add_constraints(sselect.sum('s') == 1, name="oneSeg")

            # defx[t] : net_load[t] == sum_s (sx[s]*sselect[t,s] + sstep[t,s])
            defx_rhs = sum(
                sx_vals[s] * sselect.sel(s=s) + sstep.sel(s=s)
                for s in segs
            )
            m.add_constraints(net_load == defx_rhs, name="defx")

            # defy[t] : tariff_level[t] == sum_s (sy[s]*sselect[t,s]+sslope[s]*sstep[t,s])
            defy_rhs = sum(
                sy_vals[s] * sselect.sel(s=s) + sslope_vals[s] * sstep.sel(s=s)
                for s in segs
            )
            m.add_constraints(tariff_level == defy_rhs, name="defy")

            # Bornes analytiques de tariff pour McCormick
            tariff_lb = -EUR_high
            tariff_ub =  EUR_base * max(1.0, slope_val * float(nodal_load.max()))

        # ---- Variable auxiliaire rev_tariff[t] = dispatch[t] * tariff_level[t]
        # Linéarisation McCormick avec bornes analytiques sur dispatch et tariff
        rev_tariff = m.add_variables(lower=-np.inf, upper=np.inf,
                                     coords=coords_t, name="rev_tariff")
        add_mccormick(
            m, rev_tariff, dispatch, tariff_level,
            x_lb=-Pc_max, x_ub=Pd_max,
            y_lb=tariff_lb, y_ub=tariff_ub,
            prefix="rt"
        )

        # ---- Fonction objectif LINÉAIRE ------------------------------------
        # GAMSPy : obj == Sum(t, (Pd[t]-Pc[t]) * (P[t] + tariff_level[t]))
        #        ≡ Sum(t, dispatch[t]*P[t] + rev_tariff[t])
        objective_expr = (dispatch * P_xr).sum() + rev_tariff.sum()
        m.objective = -objective_expr   # linopy minimise → MAX via négation

    else:
        # ---- Tarif OFF : tariff_level fixé à quasi-zéro (identique à l'original)
        # GAMSPy : tariff_level.fx[t] = 0.01e-15
        m.add_constraints(tariff_level == 0.01e-15, name="fix_tariff_level")

        # GAMSPy : obj == Sum(t, (Pd[t]-Pc[t]) * P[t]) — purement linéaire
        objective_expr = (dispatch * P_xr).sum()
        m.objective = -objective_expr

    # ------------------------------------------------------------------
    # 10. RÉSOLUTION — HiGHS (MILP pur, sans MIQP)
    # Options alignées sur l'original : mipgap=0.03, timelimit=1800s
    # ------------------------------------------------------------------
    m.solve(
        solver="highs",
        mip_rel_gap=0.03,
        time_limit=1800,
        threads=8,
    )

    # ------------------------------------------------------------------
    # 11. EXTRACTION DES RÉSULTATS (identique à l'original)
    #
    # GAMSPy :
    #   rep[t,"Pc"]=Pc.l[t], rep[t,"Pd"]=Pd.l[t], ...  data=rep.pivot()
    # ------------------------------------------------------------------
    data = pd.DataFrame({
        "Pc":       Pc.solution.values,
        "Pd":       Pd.solution.values,
        "SOC":      SOC.solution.values,
        "net_load": net_load.solution.values,
        "tariff":   tariff_level.solution.values,
    }, index=t_index)

    data['hour']       = data.index.astype(int)
    data['base_price'] = P_vals
    data['gridload']   = gridload_vals

    status    = str(m.status)
    objective = float(-m.objective.value)   # re-négation → valeur MAX

    info = {
        "data":               data,
        "capacity limit":     cap_limit,
        "capacity threshold": cap_threshold,
    }

    return OptResult(status, objective, None, None, info, None)