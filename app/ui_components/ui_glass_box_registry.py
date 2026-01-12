"""
app/ui_components/ui_glass_box_registry.py

REGISTRE UNIFIÉ DES MÉTADONNÉES GLASS BOX — VERSION V8.2
Rôle : Source unique de vérité pour les labels, formules et descriptions d'audit.
Architecture : Namespaces unifiés (DCF, RIM, GRAHAM, MC, AUDIT).
"""

from __future__ import annotations

from typing import Any, Dict


# ==============================================================================
# REGISTRE UNIFIÉ DES MÉTADONNÉES
# ==============================================================================

STEP_METADATA:  Dict[str, Dict[str, Any]] = {

    # ==========================================================================
    # 1. DCF — FLUX DE TRÉSORERIE ACTUALISÉS
    # ==========================================================================

    "FCF_BASE_SELECTION": {
        "label": "Ancrage FCF₀",
        "formula": r"FCF_0",
        "unit": "currency",
        "description": "Flux de trésorerie disponible de départ pour la projection."
    },
    "FCF_NORM_SELECTION": {
        "label": "Ancrage FCF Normalisé",
        "formula": r"FCF_{norm}",
        "unit":  "currency",
        "description":  "Flux lissé sur un cycle complet pour neutraliser la volatilité."
    },
    "FCF_STABILITY_CHECK": {
        "label": "Contrôle de Viabilité Financière",
        "formula":  r"FCF_{norm} > 0",
        "unit": "bool",
        "description": "Validation de la capacité à générer des flux positifs."
    },
    "WACC_CALC": {
        "label": "Coût Moyen Pondéré du Capital",
        "formula": r"WACC = w_e \cdot [R_f + \beta \cdot MRP] + w_d \cdot [k_d \cdot (1-\tau)]",
        "unit": "%",
        "description": "Taux d'actualisation reflétant le coût du capital de l'entreprise."
    },
    "FCF_PROJ":  {
        "label": "Projection des Flux",
        "formula": r"FCF_t = FCF_{t-1} \times (1+g)",
        "unit": "currency",
        "description": "Projection des flux sur l'horizon explicite."
    },
    "TV_GORDON": {
        "label": "Valeur Terminale (Gordon)",
        "formula": r"TV = \frac{FCF_n \times (1+g_n)}{WACC - g_n}",
        "unit": "currency",
        "description": "Valeur de l'entreprise au-delà de la période explicite (modèle de Gordon)."
    },
    "TV_MULTIPLE": {
        "label": "Valeur Terminale (Multiple)",
        "formula": r"TV = EBITDA_n \times Multiple",
        "unit": "currency",
        "description": "Valeur terminale basée sur un multiple de sortie."
    },
    "NPV_CALC": {
        "label": "Valeur d'Entreprise (EV)",
        "formula": r"EV = \sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}",
        "unit": "currency",
        "description": "Somme actualisée des flux et de la valeur terminale."
    },
    "EQUITY_BRIDGE": {
        "label": "Pont de Valeur (Equity Bridge)",
        "formula": r"Equity = EV - Dette + Cash - Minoritaires - Provisions",
        "unit": "currency",
        "description": "Ajustement de la structure financière pour obtenir la valeur des fonds propres."
    },
    "VALUE_PER_SHARE": {
        "label": "Valeur Intrinsèque par Action",
        "formula": r"IV = \frac{Equity\_Value}{Actions}",
        "unit": "currency",
        "description": "Estimation de la valeur réelle d'une action."
    },

    # ==========================================================================
    # 2. DCF GROWTH — REVENUE-DRIVEN
    # ==========================================================================

    "GROWTH_REV_BASE":  {
        "label": "Chiffre d'Affaires de Base",
        "formula": r"Rev_0",
        "unit": "currency",
        "description": "Point de départ du modèle basé sur le chiffre d'affaires TTM."
    },
    "GROWTH_MARGIN_CONV": {
        "label": "Convergence des Marges",
        "formula": r"Margin_t \to Margin_{target}",
        "unit": "%",
        "description": "Modélisation de l'amélioration opérationnelle vers une marge FCF normative."
    },

    # ==========================================================================
    # 3. RIM — RESIDUAL INCOME MODEL
    # ==========================================================================

    "RIM_BV_INITIAL": {
        "label": "Actif Net Comptable Initial",
        "formula": r"BV_0",
        "unit": "currency",
        "description": "Valeur comptable par action au départ du modèle."
    },
    "RIM_KE_CALC": {
        "label": "Coût des Fonds Propres (Ke)",
        "formula":  r"k_e = R_f + \beta \times MRP",
        "unit":  "%",
        "description": "Coût des capitaux propres via le CAPM."
    },
    "RIM_RI_CALC": {
        "label": "Calcul des Surprofits (RI)",
        "formula": r"RI_t = NI_t - (k_e \times BV_{t-1})",
        "unit": "currency",
        "description": "Profit résiduel après rémunération des fonds propres."
    },
    "RIM_TV_OHLSON": {
        "label": "Valeur Terminale (Persistance ω)",
        "formula": r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}",
        "unit": "currency",
        "description": "Estimation de la persistance des surprofits selon le modèle d'Ohlson."
    },
    "RIM_FINAL_VALUE": {
        "label": "Valeur Intrinsèque RIM",
        "formula": r"IV = BV_0 + \sum PV(RI_t) + PV(TV)",
        "unit": "currency",
        "description": "Valeur totale issue du modèle Residual Income."
    },
    "RIM_PAYOUT":  {
        "label": "Politique de Distribution",
        "formula": r"Payout = \frac{Div}{EPS}",
        "unit": "%",
        "description": "Ratio de distribution des dividendes."
    },
    "RIM_EPS_PROJ": {
        "label": "Projection des Bénéfices",
        "formula": r"EPS_t = EPS_{t-1} \times (1+g)",
        "unit": "currency",
        "description": "Projection des bénéfices par action."
    },

    # ==========================================================================
    # 4. GRAHAM — VALUE INVESTING
    # ==========================================================================

    "GRAHAM_EPS_BASE": {
        "label": "BPA Normalisé (EPS)",
        "formula":  r"EPS",
        "unit": "currency",
        "description": "Bénéfice par action utilisé comme socle de rentabilité."
    },
    "GRAHAM_MULTIPLIER": {
        "label":  "Multiplicateur de Croissance",
        "formula": r"M = 8. 5 + 2g",
        "unit": "x",
        "description": "Prime de croissance appliquée selon le barème révisé de Graham."
    },
    "GRAHAM_FINAL":  {
        "label": "Valeur Graham 1974",
        "formula": r"IV = \frac{EPS \times (8.5 + 2g) \times 4. 4}{Y}",
        "unit": "currency",
        "description": "Estimation de la valeur intrinsèque ajustée par le rendement AAA."
    },

    # ==========================================================================
    # 5. MONTE CARLO — ANALYSE STOCHASTIQUE
    # ==========================================================================

    "MC_CONFIG": {
        "label": "Initialisation du Moteur Stochastique",
        "formula": r"\sigma_{\beta}, \sigma_g, \sigma_{g_n}, \rho",
        "unit": "params",
        "description": "Calibration des lois normales multivariées."
    },
    "MC_SAMPLING": {
        "label": "Simulation Multivariée",
        "formula":  r"f(\beta, g, g_n) \to N_{sims}",
        "unit": "iter",
        "description": "Génération des vecteurs d'inputs via décomposition de Cholesky."
    },
    "MC_FILTERING": {
        "label": "Contrôle de Convergence",
        "formula": r"\frac{N_{valid}}{N_{total}}",
        "unit": "ratio",
        "description": "Élimination des scénarios de divergence."
    },
    "MC_MEDIAN": {
        "label": "Valeur Probabiliste Centrale (P50)",
        "formula": r"Median(IV_i)",
        "unit": "currency",
        "description": "Valeur intrinsèque centrale de la distribution stochastique."
    },
    "MC_SENSITIVITY": {
        "label": "Sensibilité à la Corrélation (ρ)",
        "formula": r"\frac{\partial P50}{\partial \rho}",
        "unit": "currency",
        "description": "Impact de la corrélation sur la stabilité de la valeur médiane."
    },
    "MC_STRESS_TEST": {
        "label":  "Stress Test (Bear Case)",
        "formula":  r"f(g \to 0, \beta \to 1.5)",
        "unit": "currency",
        "description": "Scénario de stress avec croissance nulle et risque élevé."
    },

    # ==========================================================================
    # 6. AUDIT — DATA CONFIDENCE
    # ==========================================================================

    "AUDIT_BETA_COHERENCE": {
        "label": "Cohérence du Beta",
        "formula": r"0. 4 < \beta < 3.0",
        "unit":  "ratio",
        "description": "Vérifie que le beta est dans une plage économiquement réaliste."
    },
    "AUDIT_SOLVENCY_ICR": {
        "label":  "Solvabilité (ICR)",
        "formula":  r"\frac{\text{EBIT}}{\text{Intérêts}} > 1.5",
        "unit": "x",
        "description": "Évalue la capacité à honorer la charge de la dette."
    },
    "AUDIT_CASH_MCAP": {
        "label": "Position Net-Net",
        "formula": r"\frac{\text{Trésorerie}}{\text{Market Cap}} < 1.0",
        "unit":  "%",
        "description": "Vérifie si la trésorerie excède la valorisation boursière."
    },
    "AUDIT_LIQUIDITY":  {
        "label": "Taille de Marché",
        "formula": r"MCap > 250M",
        "unit": "currency",
        "description": "Identifie les risques de liquidité sur les small-caps."
    },
    "AUDIT_LEVERAGE": {
        "label": "Levier Financier",
        "formula": r"\frac{\text{Dette}}{\text{EBIT}} < 4x",
        "unit": "x",
        "description": "Mesure l'endettement relatif à la capacité bénéficiaire."
    },

    # ==========================================================================
    # 7. AUDIT — ASSUMPTION RISK
    # ==========================================================================

    "AUDIT_G_RF_CONVERGENCE": {
        "label":  "Convergence Macro",
        "formula": r"g_{perp} < R_f",
        "unit": "ratio",
        "description": "Vérifie la cohérence entre croissance perpétuelle et taux sans risque."
    },
    "AUDIT_RF_FLOOR": {
        "label": "Plancher du Taux Sans Risque",
        "formula": r"R_f > 1\%",
        "unit": "%",
        "description": "Alerte si le Rf est anormalement bas."
    },
    "AUDIT_CAPEX_DA": {
        "label": "Taux de Renouvellement Industriel",
        "formula": r"\frac{|\text{Capex}|}{\text{D\&A}} > 0.8",
        "unit": "%",
        "description": "Mesure la capacité à maintenir l'outil de production."
    },
    "AUDIT_GROWTH_LIMIT": {
        "label": "Borne de Croissance",
        "formula": r"g < 20\%",
        "unit": "%",
        "description": "Alerte si le taux de croissance est hors normes."
    },
    "AUDIT_PAYOUT_STABILITY": {
        "label": "Soutenabilité de la Distribution",
        "formula": r"\frac{\text{Dividendes}}{\text{Résultat Net}} < 1.0",
        "unit": "%",
        "description": "Vérifie que la politique de dividende ne décapitalise pas l'entreprise."
    },

    # ==========================================================================
    # 8. AUDIT — MODEL RISK
    # ==========================================================================

    "AUDIT_WACC_FLOOR": {
        "label": "Plancher du WACC",
        "formula":  r"WACC > 6\%",
        "unit":  "%",
        "description": "Alerte si le taux d'actualisation est excessivement bas."
    },
    "AUDIT_TV_CONCENTRATION": {
        "label": "Concentration Valeur Terminale",
        "formula": r"\frac{TV}{EV} < 90\%",
        "unit": "%",
        "description": "Mesure la dépendance du modèle à la valeur terminale."
    },
    "AUDIT_G_WACC": {
        "label": "Stabilité de Convergence Gordon",
        "formula": r"g_n < WACC",
        "unit":  "ratio",
        "description": "Assure la convergence mathématique du modèle de Gordon."
    },

    # ==========================================================================
    # 9. AUDIT — METHOD FIT
    # ==========================================================================

    "AUDIT_ROE_KE_SPREAD": {
        "label": "Spread de Création de Valeur",
        "formula": r"ROE - k_e \neq 0",
        "unit": "%",
        "description":  "Mesure la création de richesse additionnelle."
    },
    "AUDIT_PB_RATIO": {
        "label": "Pertinence RIM (P/B)",
        "formula":  r"\frac{\text{Prix}}{\text{Book Value}} < 8x",
        "unit": "x",
        "description": "Indicateur de pertinence pour le modèle Residual Income."
    },

    # ==========================================================================
    # 10. AUDIT — UNKNOWN (FALLBACK)
    # ==========================================================================

    "AUDIT_UNKNOWN": {
        "label": "Test Spécifique",
        "formula": r"\text{N/A}",
        "unit": "",
        "description": "Test non référencé dans le registre."
    },
}


def get_step_metadata(key: str) -> Dict[str, Any]:
    """
    Récupère les métadonnées d'une clé.

    Args:
        key:  Clé de l'étape

    Returns:
        Dictionnaire des métadonnées ou dict vide si non trouvé
    """
    return STEP_METADATA.get(key, {})