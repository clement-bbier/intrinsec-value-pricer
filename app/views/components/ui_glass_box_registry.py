"""
app/views/components/ui_glass_box_registry.py
VALUATION METADATA REGISTRY
===========================
Role: Central definition for calculation labels, formulas, and tooltips.
Focus: Data storage only (SRP). No rendering logic here.
"""

from typing import Any, Dict
from src.i18n import UIRegistryTexts, UIStrategyFormulas

STEP_METADATA: Dict[str, Dict[str, Any]] = {

    # --- 1. CORE PIPELINE ---
    "WACC_CALC": {
        "label": UIRegistryTexts.DCF_WACC_L,
        "formula": UIStrategyFormulas.WACC,
        "unit": "%",
        "description": UIRegistryTexts.DCF_WACC_D
    },
    "KE_CALC": {
        "label": UIRegistryTexts.DCF_KE_L,
        "formula": UIStrategyFormulas.CAPM,
        "unit": "%",
        "description": UIRegistryTexts.DCF_KE_D
    },
    "FCF_BASE": {
        "label": UIRegistryTexts.DCF_FCF_BASE_L,
        "formula": UIStrategyFormulas.FCF_BASE,
        "unit": "currency",
        "description": UIRegistryTexts.DCF_FCF_BASE_D
    },
    "FCFE_BASE_SELECTION": {
        "label": UIRegistryTexts.FCFE_BASE_L,
        "formula": UIStrategyFormulas.FCFE_RECONSTRUCTION,
        "unit": "currency",
        "description": UIRegistryTexts.FCFE_BASE_D
    },
    "DDM_BASE_SELECTION": {
        "label": UIRegistryTexts.DDM_BASE_L,
        "formula": UIStrategyFormulas.DIVIDEND_BASE,
        "unit": "currency/share",
        "description": UIRegistryTexts.DDM_BASE_D
    },
    "FCF_PROJ": {
        "label": UIRegistryTexts.DCF_PROJ_L,
        "formula": UIStrategyFormulas.FCF_PROJECTION,
        "unit": "currency",
        "description": UIRegistryTexts.DCF_PROJ_D
    },
    "TV_GORDON": {
        "label": UIRegistryTexts.DCF_TV_GORDON_L,
        "formula": UIStrategyFormulas.GORDON,
        "unit": "currency",
        "description": UIRegistryTexts.DCF_TV_GORDON_D
    },
    "TV_MULTIPLE": {
        "label": UIRegistryTexts.DCF_TV_MULT_L,
        "formula": UIStrategyFormulas.TERMINAL_EXIT_MULTIPLE,
        "unit": "currency",
        "description": UIRegistryTexts.DCF_TV_MULT_D
    },
    "NPV_CALC": {
        "label": UIRegistryTexts.DCF_EV_L,
        "formula": UIStrategyFormulas.NPV,
        "unit": "currency",
        "description": UIRegistryTexts.DCF_EV_D
    },
    "EQUITY_BRIDGE": {
        "label": UIRegistryTexts.DCF_BRIDGE_L,
        "formula": UIStrategyFormulas.EQUITY_BRIDGE,
        "unit": "currency",
        "description": UIRegistryTexts.DCF_BRIDGE_D
    },
    "EQUITY_DIRECT": {
        "label": UIRegistryTexts.DCF_BRIDGE_L,
        "formula": UIStrategyFormulas.FCFE_EQUITY_VALUE,
        "unit": "currency",
        "description": UIRegistryTexts.EQUITY_DIRECT_D
    },
    "VALUE_PER_SHARE": {
        "label": UIRegistryTexts.DCF_IV_L,
        "formula": UIStrategyFormulas.VALUE_PER_SHARE,
        "unit": "currency/share",
        "description": UIRegistryTexts.DCF_IV_D
    },

    # --- 2. ALTERNATIVE MODELS ---
    "RIM_BV_INITIAL": {
        "label": UIRegistryTexts.RIM_BV_L,
        "formula": UIStrategyFormulas.BV_BASE,
        "unit": "currency",
        "description": UIRegistryTexts.RIM_BV_D
    },
    "RIM_KE_CALC": {
        "label": UIRegistryTexts.RIM_KE_L,
        "formula": UIStrategyFormulas.CAPM,
        "unit": "%",
        "description": UIRegistryTexts.RIM_KE_D
    },
    "RIM_PAYOUT": {
        "label": UIRegistryTexts.RIM_PAYOUT_L,
        "formula": UIStrategyFormulas.PAYOUT_RATIO,
        "unit": "%",
        "description": UIRegistryTexts.RIM_PAYOUT_D
    },
    "RIM_RI_SUM": {
        "label": UIRegistryTexts.RIM_RI_L,
        "formula": UIStrategyFormulas.RI_SUM,
        "unit": "currency",
        "description": UIRegistryTexts.RIM_RI_D
    },
    "RIM_TV_OHLSON": {
        "label": UIRegistryTexts.RIM_TV_L,
        "formula": UIStrategyFormulas.RIM_PERSISTENCE,
        "unit": "currency",
        "description": UIRegistryTexts.RIM_TV_D
    },
    "RIM_FINAL_IV": {
        "label": UIRegistryTexts.RIM_IV_L,
        "formula": UIStrategyFormulas.RIM_FINAL,
        "unit": "currency",
        "description": UIRegistryTexts.RIM_IV_D
    },
    "GRAHAM_EPS_BASE": {
        "label": UIRegistryTexts.GRAHAM_EPS_L,
        "formula": UIStrategyFormulas.EPS_BASE,
        "unit": "currency",
        "description": UIRegistryTexts.GRAHAM_EPS_D
    },
    "GRAHAM_MULTIPLIER": {
        "label": UIRegistryTexts.GRAHAM_MULT_L,
        "formula": UIStrategyFormulas.GRAHAM_MULTIPLIER,
        "unit": "ratio",
        "description": UIRegistryTexts.GRAHAM_MULT_D
    },
    "GRAHAM_FINAL": {
        "label": UIRegistryTexts.GRAHAM_IV_L,
        "formula": UIStrategyFormulas.GRAHAM_VALUE,
        "unit": "currency",
        "description": UIRegistryTexts.GRAHAM_IV_D
    },

    # Legacy/Internal
    "CORE_RIM_RI": {
        "label": UIRegistryTexts.RIM_RI_L,
        "formula": UIStrategyFormulas.RIM_RESIDUAL_INCOME,
        "unit": "currency",
        "description": UIRegistryTexts.RIM_RI_D
    },
    "CORE_GRAHAM_IV": {
        "label": UIRegistryTexts.GRAHAM_IV_L,
        "formula": UIStrategyFormulas.GRAHAM_VALUE,
        "unit": "currency",
        "description": UIRegistryTexts.GRAHAM_IV_D
    },

    # --- 3. ADJUSTMENTS ---
    "BETA_HAMADA_ADJUSTMENT": {
        "label": UIRegistryTexts.HAMADA_L,
        "formula": UIStrategyFormulas.HAMADA,
        "unit": "ratio",
        "description": UIRegistryTexts.HAMADA_D
    },
    "SBC_DILUTION_ADJUSTMENT": {
        "label": UIRegistryTexts.SBC_L,
        "formula": UIStrategyFormulas.SBC_DILUTION,
        "unit": "currency",
        "description": UIRegistryTexts.SBC_D
    }
}

def get_step_metadata(key: str) -> Dict[str, Any]:
    """
    Retrieves metadata for a specific calculation step.
    Provides a safe fallback for UI rendering.
    """
    meta = STEP_METADATA.get(key)
    if meta:
        return meta

    return {
        "label": str(key).replace("_", " ").title(),
        "formula": "N/A",
        "unit": "",
        "description": "Information non disponible."
    }