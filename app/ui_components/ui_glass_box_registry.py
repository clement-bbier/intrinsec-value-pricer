"""
app/ui_components/ui_glass_box_registry.py
REGISTRE UNIFIÉ DES MÉTADONNÉES GLASS BOX — VERSION V8.2
Rôle : Source unique de vérité pour les labels et formules, textes déportés dans RegistryTexts.
"""

from __future__ import annotations

from typing import Any, Dict
from app.ui_components.ui_texts import RegistryTexts

# ==============================================================================
# REGISTRE UNIFIÉ DES MÉTADONNÉES
# ==============================================================================

STEP_METADATA: Dict[str, Dict[str, Any]] = {

    # ==========================================================================
    # 1. DCF — FLUX DE TRÉSORERIE ACTUALISÉS
    # ==========================================================================

    "FCF_BASE_SELECTION": {
        "label": RegistryTexts.DCF_FCF_BASE_L,
        "formula": r"FCF_0",
        "unit": "currency",
        "description": RegistryTexts.DCF_FCF_BASE_D
    },
    "FCF_NORM_SELECTION": {
        "label": RegistryTexts.DCF_FCF_NORM_L,
        "formula": r"FCF_{norm}",
        "unit": "currency",
        "description": RegistryTexts.DCF_FCF_NORM_D
    },
    "FCF_STABILITY_CHECK": {
        "label": RegistryTexts.DCF_STABILITY_L,
        "formula": r"FCF_{norm} > 0",
        "unit": "bool",
        "description": RegistryTexts.DCF_STABILITY_D
    },
    "WACC_CALC": {
        "label": RegistryTexts.DCF_WACC_L,
        "formula": r"WACC = w_e \cdot [R_f + \beta \cdot MRP] + w_d \cdot [k_d \cdot (1-\tau)]",
        "unit": "%",
        "description": RegistryTexts.DCF_WACC_D
    },
    "FCF_PROJ": {
        "label": RegistryTexts.DCF_PROJ_L,
        "formula": r"FCF_t = FCF_{t-1} \times (1+g)",
        "unit": "currency",
        "description": RegistryTexts.DCF_PROJ_D
    },
    "TV_GORDON": {
        "label": RegistryTexts.DCF_TV_GORDON_L,
        "formula": r"TV = \frac{FCF_n \times (1+g_n)}{WACC - g_n}",
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_GORDON_D
    },
    "TV_MULTIPLE": {
        "label": RegistryTexts.DCF_TV_MULT_L,
        "formula": r"TV = EBITDA_n \times Multiple",
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_MULT_D
    },
    "NPV_CALC": {
        "label": RegistryTexts.DCF_EV_L,
        "formula": r"EV = \sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
        "unit": "currency",
        "description": RegistryTexts.DCF_EV_D
    },
    "EQUITY_BRIDGE": {
        "label": RegistryTexts.DCF_BRIDGE_L,
        "formula": r"Equity = EV - Dette + Cash - Minoritaires - Provisions",
        "unit": "currency",
        "description": RegistryTexts.DCF_BRIDGE_D
    },
    "VALUE_PER_SHARE": {
        "label": RegistryTexts.DCF_IV_L,
        "formula": r"IV = \frac{Equity\_Value}{Actions}",
        "unit": "currency",
        "description": RegistryTexts.DCF_IV_D
    },

    # ==========================================================================
    # 2. DCF GROWTH — REVENUE-DRIVEN
    # ==========================================================================

    "GROWTH_REV_BASE": {
        "label": RegistryTexts.GROWTH_REV_BASE_L,
        "formula": r"Rev_0",
        "unit": "currency",
        "description": RegistryTexts.GROWTH_REV_BASE_D
    },
    "GROWTH_MARGIN_CONV": {
        "label": RegistryTexts.GROWTH_MARGIN_L,
        "formula": r"Margin_t \to Margin_{target}",
        "unit": "%",
        "description": RegistryTexts.GROWTH_MARGIN_D
    },

    # ==========================================================================
    # 3. RIM — RESIDUAL INCOME MODEL
    # ==========================================================================

    "RIM_BV_INITIAL": {
        "label": RegistryTexts.RIM_BV_L,
        "formula": r"BV_0",
        "unit": "currency",
        "description": RegistryTexts.RIM_BV_D
    },
    "RIM_KE_CALC": {
        "label": RegistryTexts.RIM_KE_L,
        "formula": r"k_e = R_f + \beta \times MRP",
        "unit": "%",
        "description": RegistryTexts.RIM_KE_D
    },
    "RIM_RI_CALC": {
        "label": RegistryTexts.RIM_RI_L,
        "formula": r"RI_t = NI_t - (k_e \times BV_{t-1})",
        "unit": "currency",
        "description": RegistryTexts.RIM_RI_D
    },
    "RIM_TV_OHLSON": {
        "label": RegistryTexts.RIM_TV_L,
        "formula": r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}",
        "unit": "currency",
        "description": RegistryTexts.RIM_TV_D
    },
    "RIM_FINAL_VALUE": {
        "label": RegistryTexts.RIM_IV_L,
        "formula": r"IV = BV_0 + \sum PV(RI_t) + PV(TV)",
        "unit": "currency",
        "description": RegistryTexts.RIM_IV_D
    },
    "RIM_PAYOUT": {
        "label": RegistryTexts.RIM_PAYOUT_L,
        "formula": r"Payout = \frac{Div}{EPS}",
        "unit": "%",
        "description": RegistryTexts.RIM_PAYOUT_D
    },
    "RIM_EPS_PROJ": {
        "label": RegistryTexts.RIM_EPS_PROJ_L,
        "formula": r"EPS_t = EPS_{t-1} \times (1+g)",
        "unit": "currency",
        "description": RegistryTexts.RIM_EPS_PROJ_D
    },

    # ==========================================================================
    # 4. GRAHAM — VALUE INVESTING
    # ==========================================================================

    "GRAHAM_EPS_BASE": {
        "label": RegistryTexts.GRAHAM_EPS_L,
        "formula": r"EPS",
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_EPS_D
    },
    "GRAHAM_MULTIPLIER": {
        "label": RegistryTexts.GRAHAM_MULT_L,
        "formula": r"M = 8.5 + 2g",
        "unit": "x",
        "description": RegistryTexts.GRAHAM_MULT_D
    },
    "GRAHAM_FINAL": {
        "label": RegistryTexts.GRAHAM_IV_L,
        "formula": r"IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}",
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_IV_D
    },

    # ==========================================================================
    # 5. MONTE CARLO — ANALYSE STOCHASTIQUE
    # ==========================================================================

    "MC_CONFIG": {
        "label": RegistryTexts.MC_INIT_L,
        "formula": r"\sigma_{\beta}, \sigma_g, \sigma_{g_n}, \rho",
        "unit": "params",
        "description": RegistryTexts.MC_INIT_D
    },
    "MC_SAMPLING": {
        "label": RegistryTexts.MC_SAMP_L,
        "formula": r"f(\beta, g, g_n) \to N_{sims}",
        "unit": "iter",
        "description": RegistryTexts.MC_SAMP_D
    },
    "MC_FILTERING": {
        "label": RegistryTexts.MC_FILT_L,
        "formula": r"\frac{N_{valid}}{N_{total}}",
        "unit": "ratio",
        "description": RegistryTexts.MC_FILT_D
    },
    "MC_MEDIAN": {
        "label": RegistryTexts.MC_MED_L,
        "formula": r"Median(IV_i)",
        "unit": "currency",
        "description": RegistryTexts.MC_MED_D
    },
    "MC_SENSITIVITY": {
        "label": RegistryTexts.MC_SENS_L,
        "formula": r"\frac{\partial P50}{\partial \rho}",
        "unit": "currency",
        "description": RegistryTexts.MC_SENS_D
    },
    "MC_STRESS_TEST": {
        "label": RegistryTexts.MC_STRESS_L,
        "formula": r"f(g \to 0, \beta \to 1.5)",
        "unit": "currency",
        "description": RegistryTexts.MC_STRESS_D
    },

    # ==========================================================================
    # 6. AUDIT — DATA CONFIDENCE
    # ==========================================================================

    "AUDIT_BETA_COHERENCE": {
        "label": RegistryTexts.AUDIT_BETA_L,
        "formula": r"0.4 < \beta < 3.0",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_BETA_D
    },
    "AUDIT_SOLVENCY_ICR": {
        "label": RegistryTexts.AUDIT_ICR_L,
        "formula": r"\frac{\text{EBIT}}{\text{Intérêts}} > 1.5",
        "unit": "x",
        "description": RegistryTexts.AUDIT_ICR_D
    },
    "AUDIT_CASH_MCAP": {
        "label": RegistryTexts.AUDIT_CASH_L,
        "formula": r"\frac{\text{Trésorerie}}{\text{Market Cap}} < 1.0",
        "unit": "%",
        "description": RegistryTexts.AUDIT_CASH_D
    },
    "AUDIT_LIQUIDITY": {
        "label": RegistryTexts.AUDIT_LIQ_L,
        "formula": r"MCap > 250M",
        "unit": "currency",
        "description": RegistryTexts.AUDIT_LIQ_D
    },
    "AUDIT_LEVERAGE": {
        "label": RegistryTexts.AUDIT_LEV_L,
        "formula": r"\frac{\text{Dette}}{\text{EBIT}} < 4x",
        "unit": "x",
        "description": RegistryTexts.AUDIT_LEV_D
    },

    # ==========================================================================
    # 7. AUDIT — ASSUMPTION RISK
    # ==========================================================================

    "AUDIT_G_RF_CONVERGENCE": {
        "label": RegistryTexts.AUDIT_MACRO_L,
        "formula": r"g_{perp} < R_f",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_MACRO_D
    },
    "AUDIT_RF_FLOOR": {
        "label": RegistryTexts.AUDIT_RF_L,
        "formula": r"R_f > 1\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_RF_D
    },
    "AUDIT_CAPEX_DA": {
        "label": RegistryTexts.AUDIT_REINV_L,
        "formula": r"\frac{|\text{Capex}|}{\text{D\&A}} > 0.8",
        "unit": "%",
        "description": RegistryTexts.AUDIT_REINV_D
    },
    "AUDIT_GROWTH_LIMIT": {
        "label": RegistryTexts.AUDIT_GLIM_L,
        "formula": r"g < 20\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_GLIM_D
    },
    "AUDIT_PAYOUT_STABILITY": {
        "label": RegistryTexts.AUDIT_PAY_L,
        "formula": r"\frac{\text{Dividendes}}{\text{Résultat Net}} < 1.0",
        "unit": "%",
        "description": RegistryTexts.AUDIT_PAY_D
    },

    # ==========================================================================
    # 8. AUDIT — MODEL RISK
    # ==========================================================================

    "AUDIT_WACC_FLOOR": {
        "label": RegistryTexts.AUDIT_WACC_L,
        "formula": r"WACC > 6\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_WACC_D
    },
    "AUDIT_TV_CONCENTRATION": {
        "label": RegistryTexts.AUDIT_TVC_L,
        "formula": r"\frac{TV}{EV} < 90\%",
        "unit": "%",
        "description": RegistryTexts.AUDIT_TVC_D
    },
    "AUDIT_G_WACC": {
        "label": RegistryTexts.AUDIT_G_WACC_L,
        "formula": r"g_n < WACC",
        "unit": "ratio",
        "description": RegistryTexts.AUDIT_G_WACC_D
    },

    # ==========================================================================
    # 9. AUDIT — METHOD FIT
    # ==========================================================================

    "AUDIT_ROE_KE_SPREAD": {
        "label": RegistryTexts.AUDIT_SPREAD_L,
        "formula": r"ROE - k_e \neq 0",
        "unit": "%",
        "description": RegistryTexts.AUDIT_SPREAD_D
    },
    "AUDIT_PB_RATIO": {
        "label": RegistryTexts.AUDIT_PB_L,
        "formula": r"\frac{\text{Prix}}{\text{Book Value}} < 8x",
        "unit": "x",
        "description": RegistryTexts.AUDIT_PB_D
    },

    # ==========================================================================
    # 10. AUDIT — UNKNOWN (FALLBACK)
    # ==========================================================================

    "AUDIT_UNKNOWN": {
        "label": RegistryTexts.AUDIT_UNK_L,
        "formula": r"\text{N/A}",
        "unit": "",
        "description": RegistryTexts.AUDIT_UNK_D
    },
}

def get_step_metadata(key: str) -> Dict[str, Any]:
    return STEP_METADATA.get(key, {})