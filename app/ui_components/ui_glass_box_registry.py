"""
app/ui_components/ui_glass_box_registry.py
REGISTRE D'AUDIT TECHNIQUE — VERSION V6.2 (Audit-Grade Aligned)
Rôle : Correspondance exacte pour l'audit CFA Ready et la levée d'ambiguïté temporelle.
"""

from typing import Dict, Any

STEP_METADATA: Dict[str, Dict[str, Any]] = {
    # --- Fondamentaux DCF (Standard & Fondamental) ---
    "FCF_BASE_SELECTION": {"label": "Ancrage FCF₀", "formula": r"FCF_0", "unit": "currency"},
    "FCF_NORM_SELECTION": {"label": "Ancrage FCF_normalisé", "formula": r"FCF_{norm}", "unit": "currency"},
    "WACC_CALC": {"label": "Coût Moyen Pondéré du Capital", "formula": r"w_e[R_f + \beta(MRP)] + w_d[k_d(1-\tau)]", "unit": "%"},

    # Correction Audit : Label plus précis pour éviter la confusion avec la somme
    "FCF_PROJ": {"label": "Flux Terminal Projeté (Année n)", "formula": r"FCF_n = FCF_0 \times (1+g)^n", "unit": "currency"},

    "TV_GORDON": {"label": "Valeur Terminale (Gordon)", "formula": r"\frac{FCF_n \times (1+g_n)}{r - g_n}", "unit": "currency"},
    "TV_MULTIPLE": {"label": "Valeur Terminale (Multiple)", "formula": r"FCF_n \times Multiple", "unit": "currency"},

    # Ajout Audit : Rigueur temporelle (Somme des flux actualisés séparée de la TV)
    "NPV_SUM_FLOWS": {"label": "Somme des Flux Actualisés (PV)", "formula": r"\sum_{t=1}^{n} \frac{FCF_t}{(1+r)^t}", "unit": "currency"},

    # Correction Audit : Formule de la NPV montrant l'agrégation des deux blocs
    "NPV_CALC": {"label": "Valeur Actuelle Nette (NPV)", "formula": r"PV(Flux) + PV(TV)", "unit": "currency"},

    "EQUITY_BRIDGE": {"label": "Ajustement Structure Financière", "formula": r"EV - Dette + Cash", "unit": "currency"},
    "VALUE_PER_SHARE": {"label": "Valeur Intrinsèque par action", "formula": r"\frac{Equity\ Value}{Actions}", "unit": "currency"},

    # --- Modèle Growth (Spécificités) ---
    "GROWTH_REV_BASE": {"label": "Chiffre d'Affaires de base", "formula": r"Rev_0", "unit": "currency"},
    "GROWTH_MARGIN_CONV": {"label": "Convergence des marges", "formula": r"Margin_t \to Margin_{target}", "unit": "%"},

    # --- Modèle RIM (Banques / Assurances) ---
    "RIM_BV_INITIAL": {"label": "Actif Net Comptable Initial", "formula": r"BV_0", "unit": "currency"},
    "RIM_KE_CALC": {"label": "Coût des Fonds Propres (k_e)", "formula": r"R_f + \beta \times MRP", "unit": "%"},
    "RIM_PAYOUT": {"label": "Politique de distribution", "formula": r"Div / EPS", "unit": "%"},
    "RIM_EPS_PROJ": {"label": "Bénéfice Terminal Projeté (Année n)", "formula": r"EPS_n = EPS_0 \times (1+g)^n", "unit": "currency"},

    # Correction Audit : Formule explicite pour RI_t pour valider la soustraction
    "RIM_RI_CALC": {"label": "Preuve du Surprofit (RI_1)", "formula": r"NI_t - (k_e \times BV_{t-1})", "unit": "currency"},

    "RIM_FINAL_VALUE": {"label": "Valeur Intrinsèque RIM", "formula": r"BV_0 + PV(RI) + PV(TV)", "unit": "currency"},

    # --- Modèle Graham (Value) ---
    "GRAHAM_EPS_BASE": {"label": "BPA Normalisé (EPS)", "formula": r"EPS", "unit": "currency"},
    "GRAHAM_MULTIPLIER": {"label": "Multiplicateur de croissance", "formula": r"8.5 + 2g", "unit": "x"},
    "GRAHAM_FINAL": {"label": "Valeur Graham 1974", "formula": r"\frac{EPS \times (8.5 + 2g) \times 4.4}{Y}", "unit": "currency"},

    # --- Traitement Statistique (Monte Carlo) ---
    "MC_CONFIG": {"label": "Configuration des Incertitudes", "formula": r"\sigma, \rho", "unit": "params"},
    "MC_SAMPLING": {"label": "Génération des Scénarios", "formula": r"Runs_{stochastiques}", "unit": "iter"},
    "MC_FILTERING": {"label": "Filtrage et Validation", "formula": r"N_{valid} / N_{total}", "unit": "ratio"},
    "MC_PIVOT": {"label": "Scénario de Référence (P50)", "formula": r"V_{deterministic}", "unit": "currency"},
    "MC_MEDIAN": {"label": "Synthèse de la Distribution", "formula": r"Median(simulations)", "unit": "currency"}
}