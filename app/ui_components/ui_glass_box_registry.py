"""
app/ui_components/ui_glass_box_registry.py
REGISTRE UNIFIÉ DES MÉTADONNÉES GLASS BOX — VERSION V11.0 (Audit-Grade)
Rôle : Source unique de vérité pour les labels, formules et descriptions.
Architecture : Alignement strict sur le Pipeline V1.1 et les Stratégies Sprint 3.
"""

from __future__ import annotations
from typing import Any, Dict
from core.i18n import RegistryTexts

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
        "formula": r"WACC = w_e \cdot k_e + w_d \cdot [k_d \cdot (1-\tau)]",
        "unit": "%",
        "description": RegistryTexts.DCF_WACC_D
    },
    "KE_CALC": {
        "label": RegistryTexts.DCF_KE_L,
        "formula": r"k_e = R_f + \beta \times MRP",
        "unit": "%",
        "description": RegistryTexts.DCF_KE_D
    },

    # --- Flux de base (Ancrages) ---
    "FCF_BASE": {
        "label": RegistryTexts.DCF_FCF_BASE_L,
        "formula": r"FCF_0",
        "unit": "currency",
        "description": RegistryTexts.DCF_FCF_BASE_D
    },
    "FCFE_BASE_SELECTION": {
        "label": RegistryTexts.FCFE_BASE_L,
        "formula": r"FCFE = FCFF - Int(1-\tau) + \Delta Debt",
        "unit": "currency",
        "description": RegistryTexts.FCFE_BASE_D
    },
    "DDM_BASE_SELECTION": {
        "label": RegistryTexts.DDM_BASE_L,
        "formula": r"D_0",
        "unit": "currency/share",
        "description": RegistryTexts.DDM_BASE_D
    },

    # --- Projection et Terminal Value ---
    "FCF_PROJ": {
        "label": RegistryTexts.DCF_PROJ_L,
        "formula": r"Flow_t = Flow_{t-1} \times (1+g)",
        "unit": "currency",
        "description": RegistryTexts.DCF_PROJ_D
    },
    "TV_GORDON": {
        "label": RegistryTexts.DCF_TV_GORDON_L,
        "formula": r"TV = \frac{Flow_n \times (1+g_n)}{r - g_n}",
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_GORDON_D
    },
    "TV_MULTIPLE": {
        "label": RegistryTexts.DCF_TV_MULT_L,
        "formula": r"TV = EBITDA_n \times Multiple",
        "unit": "currency",
        "description": RegistryTexts.DCF_TV_MULT_D
    },

    # --- Synthèse de Valeur ---
    "NPV_CALC": {
        "label": RegistryTexts.DCF_EV_L,
        "formula": r"PV = \sum \frac{Flow_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
        "unit": "currency",
        "description": RegistryTexts.DCF_EV_D
    },
    "EQUITY_BRIDGE": {
        "label": RegistryTexts.DCF_BRIDGE_L,
        "formula": r"P = V_0 - Debt + Cash - Min. - Prov.",
        "unit": "currency",
        "description": RegistryTexts.DCF_BRIDGE_D
    },
    "EQUITY_DIRECT": {
        "label": RegistryTexts.DCF_BRIDGE_L,
        "formula": r"\text{Equity Value}",
        "unit": "currency",
        "description": "Valeur directe des fonds propres issue de l'actualisation."
    },
    "VALUE_PER_SHARE": {
        "label": RegistryTexts.DCF_IV_L,
        "formula": r"IV = \frac{Equity\_Value}{Shares}",
        "unit": "currency/share",
        "description": RegistryTexts.DCF_IV_D
    },

    # ==========================================================================
    # 2. AUTRES MODÈLES (RIM, GRAHAM)
    # ==========================================================================
    "CORE_RIM_RI": {
        "label": RegistryTexts.RIM_RI_L,
        "formula": r"RI_t = NI_t - (k_e \times BV_{t-1})",
        "unit": "currency",
        "description": RegistryTexts.RIM_RI_D
    },
    "CORE_GRAHAM_IV": {
        "label": RegistryTexts.GRAHAM_IV_L,
        "formula": r"IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}",
        "unit": "currency",
        "description": RegistryTexts.GRAHAM_IV_D
    },

    # ==========================================================================
    # 3. AUDIT & FAILSAFE
    # ==========================================================================
    "AUDIT_FCFE_BORROWING": {
        "label": RegistryTexts.FCFE_DEBT_ADJ_L,
        "formula": r"Net Borrowing / NI < 0.5",
        "unit": "ratio",
        "description": RegistryTexts.FCFE_DEBT_ADJ_D
    },
    "AUDIT_MODEL_SGR": {
        "label": RegistryTexts.DDM_GROWTH_L,
        "formula": r"g \leq ROE \times (1 - Payout)",
        "unit": "bool",
        "description": RegistryTexts.DDM_GROWTH_D
    },
    "AUDIT_UNKNOWN": {
        "label": "Étape spécifique",
        "formula": r"\text{N/A}",
        "unit": "",
        "description": "Calcul technique détaillé."
    },
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