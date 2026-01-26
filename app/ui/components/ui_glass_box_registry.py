"""
app/ui_components/ui_glass_box_registry.py
REGISTRE UNIFIÉ DES MÉTADONNÉES GLASS BOX (Audit-Grade)
Rôle : Source unique de vérité pour les labels, formules et descriptions.
Architecture : Alignement strict sur le Pipeline V1.1 et les Stratégies .
"""

from __future__ import annotations
from typing import Any, Dict
from src.i18n import RegistryTexts, StrategyFormulas

# ==============================================================================
# REGISTRE UNIFIÉ DES MÉTADONNÉES
# ==============================================================================

STEP_METADATA: Dict[str, Dict[str, Any]] = {

    # ==========================================================================
    # 1. CORE PIPELINE — CALCULS UNIFIÉS (Source: pipelines.py)
    # ==========================================================================

    # --- Taux d'actualisation ---
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

    # --- Flux de base (Ancrages) ---
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

    # --- Projection et Terminal Value ---
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

    # --- Synthèse de Valeur ---
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

    # ==========================================================================
    # 2. AUTRES MODÈLES (RIM, GRAHAM)
    # ==========================================================================

    # --- RIM Banking ---
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

    # --- Graham Number ---
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

    # ==========================================================================
    # 3. AUDIT & FAILSAFE
    # ==========================================================================
    "AUDIT_FCFE_BORROWING": {
        "label": RegistryTexts.FCFE_DEBT_ADJ_L,
        "formula": StrategyFormulas.AUDIT_BORROWING,
        "unit": "ratio",
        "description": RegistryTexts.FCFE_DEBT_ADJ_D
    },
    "AUDIT_MODEL_SGR": {
        "label": RegistryTexts.DDM_GROWTH_L,
        "formula": StrategyFormulas.AUDIT_SGR,
        "unit": "bool",
        "description": RegistryTexts.DDM_GROWTH_D
    },
    "AUDIT_UNKNOWN": {
        "label": RegistryTexts.AUDIT_UNK_L,
        "formula": StrategyFormulas.NA,
        "unit": "",
        "description": RegistryTexts.AUDIT_UNK_D
    },

    # ==========================================================================
    # 4. AJUSTEMENTS TECHNIQUES & PONTS
    # ==========================================================================
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
    Récupère les métadonnées d'une étape de calcul.
    Sécurité : Empêche le crash de l'app si une clé est manquante.
    """
    # 1. Tentative de récupération directe
    meta = STEP_METADATA.get(key)
    if meta:
        return meta

    # 2. Fallback sécurisé : On génère un objet minimal pour l'UI
    return {
        "label": str(key).replace("_", " ").title(),
        "formula": r"\text{Calcul Interne}",
        "unit": "",
        "description": "Détail technique du calcul spécifique au modèle."
    }
