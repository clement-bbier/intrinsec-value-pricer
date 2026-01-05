from typing import Dict, Any

STEP_METADATA: Dict[str, Dict[str, Any]] = {
    # --- Fondamentaux DCF (Standard & Fondamental) ---
    "FCF_BASE_SELECTION": {"label": "Ancrage FCF₀", "formula": r"FCF_0", "unit": "currency"},
    "FCF_NORM_SELECTION": {"label": "Ancrage FCF_normalisé", "formula": r"FCF_{norm}", "unit": "currency"},
    "WACC_CALC": {"label": "Coût Moyen Pondéré du Capital", "formula": r"w_e[R_f + \beta(MRP)] + w_d[k_d(1-\tau)]", "unit": "%"},
    "FCF_PROJ": {"label": "Projection des Flux", "formula": r"FCF_t = FCF_{t-1} \times (1+g)", "unit": "currency"},
    "TV_GORDON": {"label": "Valeur Terminale (Gordon)", "formula": r"\frac{FCF_n \times (1+g_n)}{WACC - g_n}", "unit": "currency"},
    "TV_MULTIPLE": {"label": "Valeur Terminale (Multiple)", "formula": r"EBITDA_n \times Multiple", "unit": "currency"},
    "NPV_CALC": {"label": "Valeur Actuelle Nette (NPV)", "formula": r"\sum \frac{FCF_t}{(1+r)^t} + \frac{TV}{(1+r)^n}", "unit": "currency"},
    "EQUITY_BRIDGE": {"label": "Ajustement Structure Financière", "formula": r"EV - Dette + Cash", "unit": "currency"},
    "VALUE_PER_SHARE": {"label": "Valeur Intrinsèque par action", "formula": r"\frac{Equity\ Value}{Actions}", "unit": "currency"},

    # --- Modèle Growth (Spécificités) ---
    "GROWTH_REV_BASE": {"label": "Chiffre d'Affaires de base", "formula": r"Rev_0", "unit": "currency"},
    "GROWTH_MARGIN_CONV": {"label": "Convergence des marges", "formula": r"Margin_t \to Margin_{target}", "unit": "%"},

    # --- Modèle RIM (Banques / Assurances) ---
    "RIM_BV_INITIAL": {"label": "Actif Net Comptable Initial", "formula": r"BV_0", "unit": "currency"},
    "RIM_KE_CALC": {"label": "Coût des Fonds Propres (k_e)", "formula": r"R_f + \beta \times MRP", "unit": "%"},
    "RIM_RI_CALC": {"label": "Calcul des Surprofits (RI)", "formula": r"NI_t - (k_e \times BV_{t-1})", "unit": "currency"},
    "RIM_FINAL_VALUE": {"label": "Valeur Intrinsèque RIM", "formula": r"BV_0 + \sum PV(RI_t)", "unit": "currency"},
    "RIM_PAYOUT": {"label": "Politique de distribution", "formula": r"Div / EPS", "unit": "%"},
    "RIM_EPS_PROJ": {"label": "Projection des bénéfices", "formula": r"EPS_t = EPS_{t-1} \times (1+g)", "unit": "currency"},

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