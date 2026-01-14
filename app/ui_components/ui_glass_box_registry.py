"""
app/ui_components/ui_glass_box_registry.py
REGISTRE UNIFIÉ DES MÉTADONNÉES GLASS BOX — VERSION V9.0
Rôle : Source unique de vérité pour les labels, formules et descriptions.
Architecture : Namespaces unifiés CORE_, MC_, AUDIT_.
"""

from __future__ import annotations

from typing import Any, Dict
from app.ui_components.ui_texts import RegistryTexts

# ==============================================================================
# REGISTRE UNIFIÉ DES MÉTADONNÉES
# ==============================================================================

STEP_METADATA: Dict[str, Dict[str, Any]] = {

    # ==========================================================================
    # 1. CORE — CALCULS DE VALORISATION (DCF, RIM, GRAHAM)
    # ==========================================================================

    # --- DCF Standard & Fundamental ---
    "CORE_DCF_FCF_BASE": {
        "label": RegistryTexts.DCF_FCF_BASE_L,
        "formula": r"FCF_0",
        "unit": "currency",
        "description": RegistryTexts.DCF_FCF_BASE_D
    },
    "CORE_DCF_FCF_NORM": {
        "label": RegistryTexts.DCF_FCF_NORM_L,
        "formula": r"FCF_{norm}",
        "unit": "currency",
        "description": RegistryTexts.DCF_FCF_NORM_D
    },
    "CORE_DCF_WACC": {
        "label": RegistryTexts.DCF_WACC_L,
        "formula": r"WACC = w_e \cdot [R_f + \beta \cdot MRP] + w_d \cdot [k_d \cdot (1-\tau)]",
        "unit": "%",
        "description": RegistryTexts.DCF_WACC_D
    },
    "CORE_DCF_PROJ": {
        "label": RegistryTexts.DCF_PROJ_L,
        "formula": r"FCF_t = FCF_{t-1} \times (1+g)",
        "unit": "currency",
        "description": RegistryTexts.DCF_PROJ_D
    },
    "CORE_DCF_TV_GORDON": {
        "label": RegistryTexts.DCF_TV_GORDON_L,
        "formula": r"TV = \frac{FCF_n \times (1+g_n)}{WACC - g_n}",
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_GORDON_D
    },
    "CORE_DCF_TV_MULT": {
        "label": RegistryTexts.DCF_TV_MULT_L,
        "formula": r"TV = EBITDA_n \times Multiple",
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_MULT_D
    },
    "CORE_DCF_EV": {
        "label": RegistryTexts.DCF_EV_L,
        "formula": r"EV = \sum_{t=1}^{n} \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
        "unit": "currency",
        "description": RegistryTexts.DCF_EV_D
    },
    "CORE_DCF_BRIDGE": {
        "label": RegistryTexts.DCF_BRIDGE_L,
        "formula": r"Equity = EV - Debt + Cash - Min. - Prov.",
        "unit": "currency",
        "description": RegistryTexts.DCF_BRIDGE_D
    },
    "CORE_DCF_IV": {
        "label": RegistryTexts.DCF_IV_L,
        "formula": r"IV = \frac{Equity\_Value}{Shares}",
        "unit": "currency",
        "description": RegistryTexts.DCF_IV_D
    },

    # --- DCF Growth (Revenue Driven) ---
    "CORE_GROWTH_REV": {
        "label": RegistryTexts.GROWTH_REV_BASE_L,
        "formula": r"Rev_0",
        "unit": "currency",
        "description": RegistryTexts.GROWTH_REV_BASE_D
    },
    "CORE_GROWTH_MARGIN": {
        "label": RegistryTexts.GROWTH_MARGIN_L,
        "formula": r"Margin_t \to Margin_{target}",
        "unit": "%",
        "description": RegistryTexts.GROWTH_MARGIN_D
    },

    # --- RIM (Residual Income) ---
    "CORE_RIM_BV": {
        "label": RegistryTexts.RIM_BV_L,
        "formula": r"BV_0",
        "unit": "currency",
        "description": RegistryTexts.RIM_BV_D
    },
    "CORE_RIM_KE": {
        "label": RegistryTexts.RIM_KE_L,
        "formula": r"k_e = R_f + \beta \times MRP",
        "unit": "%",
        "description": RegistryTexts.RIM_KE_D
    },
    "CORE_RIM_RI": {
        "label": RegistryTexts.RIM_RI_L,
        "formula": r"RI_t = NI_t - (k_e \times BV_{t-1})",
        "unit": "currency",
        "description": RegistryTexts.RIM_RI_D
    },
    "CORE_RIM_TV": {
        "label": RegistryTexts.RIM_TV_L,
        "formula": r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}",
        "unit": "currency",
        "description": RegistryTexts.RIM_TV_D
    },
    "CORE_RIM_IV": {
        "label": RegistryTexts.RIM_IV_L,
        "formula": r"IV = BV_0 + \sum PV(RI_t) + PV(TV)",
        "unit": "currency",
        "description": RegistryTexts.RIM_IV_D
    },

    # --- Graham ---
    "CORE_GRAHAM_EPS": {
        "label": RegistryTexts.GRAHAM_EPS_L,
        "formula": r"EPS",
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_EPS_D
    },
    "CORE_GRAHAM_MULT": {
        "label": RegistryTexts.GRAHAM_MULT_L,
        "formula": r"M = 8.5 + 2g",
        "unit": "x",
        "description": RegistryTexts.GRAHAM_MULT_D
    },
    "CORE_GRAHAM_IV": {
        "label": RegistryTexts.GRAHAM_IV_L,
        "formula": r"IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}",
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_IV_D
    },

    # ==========================================================================
    # 2. MC — MONTE CARLO (STOCHASTIQUE)
    # ==========================================================================

    "MC_ENGINE_INIT": {
        "label": RegistryTexts.MC_INIT_L,
        "formula": r"\Sigma = \text{Matrix}(\sigma_i, \rho_{ij})",
        "unit": "params",
        "description": RegistryTexts.MC_INIT_D
    },
    "MC_SAMP_VECTOR": {
        "label": RegistryTexts.MC_SAMP_L,
        "formula": r"X = \mu + L \cdot Z, \text{ where } LL^T = \Sigma",
        "unit": "iter",
        "description": RegistryTexts.MC_SAMP_D
    },
    "MC_CONVERGENCE": {
        "label": RegistryTexts.MC_FILT_L,
        "formula": r"N_{valid} / N_{total} \geq 80\%",
        "unit": "ratio",
        "description": RegistryTexts.MC_FILT_D
    },
    "MC_DIST_MEDIAN": {
        "label": RegistryTexts.MC_MED_L,
        "formula": r"\text{P50}(IV_{sim})",
        "unit": "currency",
        "description": RegistryTexts.MC_MED_D
    },
    "MC_RHO_SENSITIVITY": {
        "label": RegistryTexts.MC_SENS_L,
        "formula": r"\Delta \text{P50} / \Delta \rho",
        "unit": "currency",
        "description": RegistryTexts.MC_SENS_D
    },
    "MC_STRESS_TEST": {
        "label": RegistryTexts.MC_STRESS_L,
        "formula": r"IV | \{g=0, \beta=1.5\}",
        "unit": "currency",
        "description": RegistryTexts.MC_STRESS_D
    },

    # ==========================================================================
    # 3. AUDIT — TESTS DE FIABILITÉ (INVARIANTS)
    # ==========================================================================

    "AUDIT_DATA_BETA": {
        "label": RegistryTexts.AUDIT_BETA_L,
        "formula": r"0.4 < \beta < 3.0",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_BETA_D
    },
    "AUDIT_DATA_ICR": {
        "label": RegistryTexts.AUDIT_ICR_L,
        "formula": r"EBIT / Interest > 1.5",
        "unit": "x",
        "description": RegistryTexts.AUDIT_ICR_D
    },
    "AUDIT_DATA_CASH": {
        "label": RegistryTexts.AUDIT_CASH_L,
        "formula": r"Cash / MCap < 1.0",
        "unit": "%",
        "description": RegistryTexts.AUDIT_CASH_D
    },
    "AUDIT_DATA_LIQUIDITY": {
        "label": RegistryTexts.AUDIT_LIQ_L,
        "formula": r"MCap > 250M",
        "unit": "currency",
        "description": RegistryTexts.AUDIT_LIQ_D
    },
    "AUDIT_DATA_LEVERAGE": {
        "label": RegistryTexts.AUDIT_LEV_L,
        "formula": r"Debt / EBIT < 4x",
        "unit": "x",
        "description": RegistryTexts.AUDIT_LEV_D
    },
    "AUDIT_MACRO_G_RF": {
        "label": RegistryTexts.AUDIT_MACRO_L,
        "formula": r"g_{perp} < R_f",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_MACRO_D
    },
    "AUDIT_MACRO_RF_FLOOR": {
        "label": RegistryTexts.AUDIT_RF_L,
        "formula": r"R_f > 1.0\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_RF_D
    },
    "AUDIT_MODEL_REINVEST": {
        "label": RegistryTexts.AUDIT_REINV_L,
        "formula": r"|Capex| / D\&A > 0.8",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_REINV_D
    },
    "AUDIT_MODEL_GLIM": {
        "label": RegistryTexts.AUDIT_GLIM_L,
        "formula": r"g < 20.0\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_GLIM_D
    },
    "AUDIT_MODEL_PAYOUT": {
        "label": RegistryTexts.AUDIT_PAY_L,
        "formula": r"Div / NI < 1.0",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_PAY_D
    },
    "AUDIT_MODEL_WACC": {
        "label": RegistryTexts.AUDIT_WACC_L,
        "formula": r"WACC > 6.0\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_WACC_D
    },
    "AUDIT_MODEL_TVC": {
        "label": RegistryTexts.AUDIT_TVC_L,
        "formula": r"TV / EV < 90.0\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_TVC_D
    },
    "AUDIT_MODEL_G_WACC": {
        "label": RegistryTexts.AUDIT_G_WACC_L,
        "formula": r"g_n < WACC",
        "unit": "bool",
        "description": RegistryTexts.AUDIT_G_WACC_D
    },
    "AUDIT_FIT_SPREAD": {
        "label": RegistryTexts.AUDIT_SPREAD_L,
        "formula": r"ROE - k_e \neq 0",
        "unit": "%",
        "description": RegistryTexts.AUDIT_SPREAD_D
    },
    "AUDIT_FIT_PB": {
        "label": RegistryTexts.AUDIT_PB_L,
        "formula": r"Price / BV < 8x",
        "unit": "x",
        "description": RegistryTexts.AUDIT_PB_D
    },
    "AUDIT_UNKNOWN": {
        "label": RegistryTexts.AUDIT_UNK_L,
        "formula": r"\text{N/A}",
        "unit": "",
        "description": RegistryTexts.AUDIT_UNK_D
    },
}

def get_step_metadata(key: str) -> Dict[str, Any]:
    """Récupère les métadonnées d'une étape par sa clé unifiée."""
    return STEP_METADATA.get(key, {})