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
    "EQUITY_BRIDGE": {"label": "Ajustement Structure Financière", "formula": r"EV - Dette + Cash - Minoritaires - Provisions", "unit": "currency"},
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
    "MC_CONFIG": {"label": "Initialisation du Moteur Stochastique", "formula": r"\sigma_{\beta, g, g_n}, \rho", "unit": "params"},
    "MC_SAMPLING": {"label": "Simulation Multivariée (Tirages)", "formula": r"f(\beta, g, g_n) \to N_{sims}", "unit": "iter"},
    "MC_FILTERING": {"label": "Contrôle de Convergence & Rejet", "formula": r"N_{valid} / N_{total}", "unit": "ratio"},
    "MC_MEDIAN": {"label": "Valeur Probabiliste Centrale (P50)", "formula": r"Median(IV_i)", "unit": "currency"},
    "MC_SENSITIVITY": {"label": "Sensibilité à la Corrélation (ρ)", "formula": r"\frac{\partial P50}{\partial \rho}", "unit": "currency"},
    "MC_STRESS_TEST": {"label": "Stress Test : Scénario de Rupture", "formula": r"f(g \to 0, \beta \to 1.5)", "unit": "currency"},

    # --- Registre des Contrôles d'Audit (Reliability & Risk) ---
    "AUDIT_CASH_MCAP": {"label": "Exposition Relative de la Trésorerie", "formula": r"\frac{\text{Trésorerie}}{\text{Market Cap}} < 1.0", "unit": "%", "description": "Vérifie si la valeur liquide excède la valorisation boursière (Situation Net-Net)."},
    "AUDIT_CAPEX_DA": {"label": "Taux de Renouvellement Industriel", "formula": r"\frac{|\text{Capex}|}{\text{D\&A}} > 0.8", "unit": "%", "description": "Mesure la capacité de l'entreprise à maintenir son outil de production."},
    "AUDIT_G_WACC": {"label": "Stabilité de la Convergence Gordon", "formula": r"g_{n} < WACC", "unit": "ratio", "description": "Assure la convergence mathématique du modèle de croissance perpétuelle."},
    "AUDIT_SOLVENCY_ICR": {"label": "Couverture des Charges Financières", "formula": r"\frac{\text{EBIT}}{\text{Intérêts}} > 1.5", "unit": "x", "description": "Évalue la capacité à honorer la charge de la dette via le résultat opérationnel."},
    "AUDIT_PAYOUT_STABILITY": {"label": "Soutenabilité de la Distribution", "formula": r"\frac{\text{Dividendes}}{\text{Résultat Net}} < 1.0", "unit": "%", "description": "Vérifie que la politique de dividende ne décapitalise pas l'entreprise."},
    "AUDIT_PB_RATIO": {"label": "Ancrage sur l'Actif Net (P/B)", "formula": r"\frac{\text{Prix}}{\text{Book Value}}", "unit": "x", "description": "Indicateur de pertinence pour le modèle Residual Income (RIM)."},

    # --- DATA CONFIDENCE ---
    "beta": {"label": "Cohérence du Beta", "formula": r"0.4 < \beta < 3.0"},
    "icr": {"label": "Solvabilité (ICR)", "formula": r"\frac{EBIT}{Intérêts} > 1.5"},
    "cash_mcap": {"label": "Position Net-Net", "formula": r"Trésorerie < MCap"},
    "liquidity": {"label": "Taille de Marché", "formula": r"MCap > 250M"},
    "leverage": {"label": "Levier Financier", "formula": r"\frac{Dette}{EBIT} < 4x"},

    # --- ASSUMPTION RISK ---
    "g_rf": {"label": "Convergence Macro", "formula": r"g_{perp} < R_f"},
    "rf_min": {"label": "Plancher de Risque", "formula": r"R_f > 1\%"},
    "capex_da": {"label": "Taux de Renouvellement", "formula": r"\frac{Capex}{D\&A} > 0.8"},
    "growth_limit": {"label": "Borne de Croissance", "formula": r"g < 20\%"},
    "payout": {"label": "Soutenabilité Dividende", "formula": r"Payout < 100\%"},

    # --- MODEL & METHOD ---
    "wacc_min": {"label": "Actualisation (WACC)", "formula": r"WACC > 6\%"},
    "tv_weight": {"label": "Poids Valeur Terminale", "formula": r"\frac{TV}{EV} < 90\%"},
    "gordon_instability": {"label": "Stabilité Gordon", "formula": r"g < WACC"},
    "roe_ke": {"label": "Spread de Création", "formula": r"ROE - K_e \neq 0"},
    "pb_ratio": {"label": "Pertinence RIM", "formula": r"P/B < 8x"}
}