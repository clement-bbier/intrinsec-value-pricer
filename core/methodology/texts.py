"""
core/methodology/texts.py
Source de vérité unique pour les textes, tooltips et explications méthodologiques.
"""

# --- TOOLTIPS (Aides contextuelles) ---
TOOLTIPS = {
    "ticker": "Symbole boursier (ex: AAPL, LVMH.PA).",
    "years": "Horizon de projection explicite des flux de trésorerie (DCF).",
    "growth_g": "Taux de croissance annuel moyen du Free Cash Flow sur la période de projection.",
    "growth_perp": "Taux de croissance à l'infini (Terminal Value). Ne doit pas dépasser le PIB long terme (2-3%).",
    "rf": "Taux sans risque (Risk-Free Rate). Généralement le rendement des obligations d'État à 10 ans.",
    "mrp": "Prime de risque de marché (Market Risk Premium). Rendement espéré des actions au-delà du taux sans risque.",
    "beta": "Mesure de la volatilité systématique du titre par rapport au marché.",
    "cost_debt": "Coût de la dette avant impôt (Interest Rate).",
    "tax_rate": "Taux effectif ou marginal d'impôt sur les sociétés (IS).",
    "target_weights": "Structure du capital cible à long terme (Dette vs Equity).",
    "volatility": "Incertitude (écart-type) appliquée au paramètre pour la simulation Monte Carlo."
}

# --- METHODOLOGY SECTIONS ---

SIMPLE_DCF_TITLE = "### Méthode 1 : DCF Simplifié"
SIMPLE_DCF_SECTIONS = [
    {
        "subtitle": "#### 1. Concept",
        "markdown_blocks": ["Projection directe du dernier Free Cash Flow connu (TTM).", "> Idéal pour les entreprises matures à croissance stable."],
    },
    {
        "subtitle": "#### 2. Formule",
        "markdown_blocks": ["Le FCF est projeté avec un taux de croissance unique, puis actualisé au WACC."],
        "latex_blocks": [r"V = \sum_{t=1}^{n} \frac{FCF_0(1+g)^t}{(1+WACC)^t} + \frac{TV}{(1+WACC)^n}"]
    }
]

FUNDAMENTAL_DCF_TITLE = "### Méthode 2 : DCF Analytique"
FUNDAMENTAL_DCF_SECTIONS = [
    {
        "subtitle": "#### 1. Concept",
        "markdown_blocks": ["Reconstruction 'Bottom-Up' du flux normatif à partir de l'EBIT et du Bilan."],
    },
    {
        "subtitle": "#### 2. Calcul du Flux Normatif",
        "markdown_blocks": ["On lisse les cycles d'investissement (Capex) et de BFR."],
        "latex_blocks": [r"FCFF = EBIT(1-t) + D\&A - Capex_{norm} - \Delta BFR"]
    },
    {
        "subtitle": "#### 3. Croissance",
        "markdown_blocks": ["Intègre un cycle de croissance en 2 phases : Plateau (High Growth) -> Transition (Fade) -> Infini."]
    }
]

MONTE_CARLO_TITLE = "### Méthode 3 : DCF Probabiliste"
MONTE_CARLO_SECTIONS = [
    {
        "subtitle": "#### 1. Concept",
        "markdown_blocks": ["Simulation de milliers de scénarios pour valoriser l'incertitude."],
    },
    {
        "subtitle": "#### 2. Variables Aléatoires",
        "markdown_blocks": [
            "- **Beta** : Distribution Normale (autour du Beta historique).",
            "- **Croissance** : Distribution Normale (autour du consensus).",
            "- **Corrélation** : Lien négatif modélisé entre Risque (Beta) et Croissance."
        ]
    }
]

# --- AUDIT TEXTS ---
AUDIT_TITLE = "### Méthodologie du Trust Score"
AUDIT_INTRO = "Le score évalue la fiabilité technique et la cohérence des hypothèses (0-100)."