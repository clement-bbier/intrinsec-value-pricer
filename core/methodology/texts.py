from typing import List, Dict, Any

SIMPLE_DCF_TITLE = "### Méthode 1 : DCF Simplifié"
SIMPLE_DCF_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### 1. Concept",
        "markdown_blocks": ["Valorisation basée sur la performance actuelle (12 derniers mois) projetée dans le futur.", "> Idéale pour entreprises matures et stables."],
    },
    {
        "subtitle": "#### 2. Calcul du Flux",
        "markdown_blocks": ["On utilise le Free Cash Flow to Firm (FCFF) brut."],
        "latex_blocks": [r"FCFF = CFO - |Capex|"]
    },
    {
        "subtitle": "#### 3. Actualisation",
        "markdown_blocks": ["Projection avec croissance décélérante, actualisée au WACC."],
        "latex_blocks": [r"WACC = (K_e \times \%E) + (K_d(1-t) \times \%D)"]
    }
]

FUNDAMENTAL_DCF_TITLE = "### Méthode 2 : DCF Analytique"
FUNDAMENTAL_DCF_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### 1. Concept",
        "markdown_blocks": ["Reconstruction de la rentabilité économique réelle (Standard M&A)."],
    },
    {
        "subtitle": "#### 2. Flux Normatif",
        "markdown_blocks": ["Reconstruction depuis l'EBIT :"],
        "latex_blocks": [r"FCFF = (EBIT \times (1 - Tax)) + D\&A - Capex - \Delta BFR"]
    },
    {
        "subtitle": "#### 3. Lissage",
        "markdown_blocks": ["Moyenne pondérée sur 5 ans pour gommer les cycles."]
    }
]

MONTE_CARLO_TITLE = "### Méthode 3 : DCF Probabiliste"
MONTE_CARLO_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### 1. Concept",
        "markdown_blocks": ["Valoriser l'incertitude en remplaçant les certitudes par des probabilités."],
    },
    {
        "subtitle": "#### 2. Simulation (5000 scénarios)",
        "markdown_blocks": [
            "- **Beta** : Varie selon volatilité historique.",
            "- **Croissance** : Varie selon volatilité sectorielle.",
            "- **Corrélation** : Lien inverse Risque/Croissance intégré."
        ]
    }
]

AUDIT_TITLE = "### Méthodologie du Score"
AUDIT_INTRO = "Le score évalue la fiabilité technique (0-100)."
AUDIT_AUTO_BLOCKS = [
    "**1. Qualité Données (35%)** : Pénalise les manques.",
    "**2. Spécificité (35%)** : Pénalise les données génériques.",
    "**3. Stabilité (15%)** : Vérifie la cohérence mathématique."
]
AUDIT_MANUAL_BLOCKS = [
    "**1. Cohérence (50%)** : Vérifie la logique interne.",
    "**2. Données (20%)** : Vérifie la base comptable.",
    "**3. Adéquation (10%)** : Vérifie l'adéquation au profil."
]