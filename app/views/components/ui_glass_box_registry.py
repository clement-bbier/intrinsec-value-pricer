"""
app/views/components/ui_glass_box_registry.py
VALUATION METADATA REGISTRY
===========================
Role: Central definition for calculation labels, formulas, and tooltips.
Focus: Data storage only (SRP). No rendering logic here.
"""

from typing import Any, Dict
from src.i18n.fr.ui.results import RegistryTexts, StrategyFormulas

STEP_METADATA: Dict[str, Dict[str, Any]] = {

    # --- 1. CORE PIPELINE ---
    "WACC_CALC": {
        "label": RegistryTexts.DCF_WACC_L,
        "formula": StrategyFormulas.WACC,
        "unit": "%",
        "description": RegistryTexts.DCF_WACC_D
    },
    "KE_CALC": {
        "label": RegistryTexts.DCF_KE_L,
        "formula": StrategyFormulas.CAPM,
        "unit": "%",
        "description": RegistryTexts.DCF_KE_D
    },
    "FCF_BASE": {
        "label": RegistryTexts.DCF_FCF_BASE_L,
        "formula": StrategyFormulas.FCF_BASE,
        "unit": "currency",
        "description": RegistryTexts.DCF_FCF_BASE_D
    },
    "FCFE_BASE_SELECTION": {
        "label": RegistryTexts.FCFE_BASE_L,
        "formula": StrategyFormulas.FCFE_RECONSTRUCTION,
        "unit": "currency",
        "description": RegistryTexts.FCFE_BASE_D
    },
    "DDM_BASE_SELECTION": {
        "label": RegistryTexts.DDM_BASE_L,
        "formula": StrategyFormulas.DIVIDEND_BASE,
        "unit": "currency/share",
        "description": RegistryTexts.DDM_BASE_D
    },
    "FCF_PROJ": {
        "label": RegistryTexts.DCF_PROJ_L,
        "formula": StrategyFormulas.FCF_PROJECTION,
        "unit": "currency",
        "description": RegistryTexts.DCF_PROJ_D
    },
    "TV_GORDON": {
        "label": RegistryTexts.DCF_TV_GORDON_L,
        "formula": StrategyFormulas.GORDON,
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_GORDON_D
    },
    "TV_MULTIPLE": {
        "label": RegistryTexts.DCF_TV_MULT_L,
        "formula": StrategyFormulas.TERMINAL_EXIT_MULTIPLE,
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_MULT_D
    },
    "NPV_CALC": {
        "label": RegistryTexts.DCF_EV_L,
        "formula": StrategyFormulas.NPV,
        "unit": "currency",
        "description": RegistryTexts.DCF_EV_D
    },
    "EQUITY_BRIDGE": {
        "label": RegistryTexts.DCF_BRIDGE_L,
        "formula": StrategyFormulas.EQUITY_BRIDGE,
        "unit": "currency",
        "description": RegistryTexts.DCF_BRIDGE_D
    },
    "EQUITY_DIRECT": {
        "label": RegistryTexts.DCF_BRIDGE_L,
        "formula": StrategyFormulas.FCFE_EQUITY_VALUE,
        "unit": "currency",
        "description": RegistryTexts.EQUITY_DIRECT_D
    },
    "VALUE_PER_SHARE": {
        "label": RegistryTexts.DCF_IV_L,
        "formula": StrategyFormulas.VALUE_PER_SHARE,
        "unit": "currency/share",
        "description": RegistryTexts.DCF_IV_D
    },

    # --- 2. ALTERNATIVE MODELS ---
    "RIM_BV_INITIAL": {
        "label": RegistryTexts.RIM_BV_L,
        "formula": StrategyFormulas.BV_BASE,
        "unit": "currency",
        "description": RegistryTexts.RIM_BV_D
    },
    "RIM_KE_CALC": {
        "label": RegistryTexts.RIM_KE_L,
        "formula": StrategyFormulas.CAPM,
        "unit": "%",
        "description": RegistryTexts.RIM_KE_D
    },
    "RIM_PAYOUT": {
        "label": RegistryTexts.RIM_PAYOUT_L,
        "formula": StrategyFormulas.PAYOUT_RATIO,
        "unit": "%",
        "description": RegistryTexts.RIM_PAYOUT_D
    },
    "RIM_RI_SUM": {
        "label": RegistryTexts.RIM_RI_L,
        "formula": StrategyFormulas.RI_SUM,
        "unit": "currency",
        "description": RegistryTexts.RIM_RI_D
    },
    "RIM_TV_OHLSON": {
        "label": RegistryTexts.RIM_TV_L,
        "formula": StrategyFormulas.RIM_PERSISTENCE,
        "unit": "currency",
        "description": RegistryTexts.RIM_TV_D
    },
    "RIM_FINAL_IV": {
        "label": RegistryTexts.RIM_IV_L,
        "formula": StrategyFormulas.RIM_FINAL,
        "unit": "currency",
        "description": RegistryTexts.RIM_IV_D
    },
    "GRAHAM_EPS_BASE": {
        "label": RegistryTexts.GRAHAM_EPS_L,
        "formula": StrategyFormulas.EPS_BASE,
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_EPS_D
    },
    "GRAHAM_MULTIPLIER": {
        "label": RegistryTexts.GRAHAM_MULT_L,
        "formula": StrategyFormulas.GRAHAM_MULTIPLIER,
        "unit": "ratio",
        "description": RegistryTexts.GRAHAM_MULT_D
    },
    "GRAHAM_FINAL": {
        "label": RegistryTexts.GRAHAM_IV_L,
        "formula": StrategyFormulas.GRAHAM_VALUE,
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_IV_D
    },

    # Legacy/Internal
    "CORE_RIM_RI": {
        "label": RegistryTexts.RIM_RI_L,
        "formula": StrategyFormulas.RIM_RESIDUAL_INCOME,
        "unit": "currency",
        "description": RegistryTexts.RIM_RI_D
    },
    "CORE_GRAHAM_IV": {
        "label": RegistryTexts.GRAHAM_IV_L,
        "formula": StrategyFormulas.GRAHAM_VALUE,
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_IV_D
    },

    # --- 3. ADJUSTMENTS ---
    "BETA_HAMADA_ADJUSTMENT": {
        "label": RegistryTexts.HAMADA_L,
        "formula": StrategyFormulas.HAMADA,
        "unit": "ratio",
        "description": RegistryTexts.HAMADA_D
    },
    "SBC_DILUTION_ADJUSTMENT": {
        "label": RegistryTexts.SBC_L,
        "formula": StrategyFormulas.SBC_DILUTION,
        "unit": "currency",
        "description": RegistryTexts.SBC_D
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