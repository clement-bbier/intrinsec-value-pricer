"""
core/methodology/texts.py

SOURCE DE VÉRITÉ — DOCUMENTATION MÉTHODOLOGIQUE CANONIQUE
Version : V3.0 — Chapitre 9 conforme

Rôle :
- Centraliser les textes méthodologiques courts
- Assurer la cohérence stricte UI ↔ moteur ↔ documentation
- Référencer TOUTES les stratégies réellement implémentées

Règles :
- Aucun texte sans stratégie existante
- Aucun doublon avec docs/methodology/*.md
- Textes courts, stables, auditables
"""

# ==============================================================================
# TOOLTIPS — AIDES CONTEXTUELLES UI
# ==============================================================================

TOOLTIPS = {
    "ticker": "Symbole boursier de l’entreprise cotée (ex: AAPL, MSFT, LVMH.PA).",
    "years": "Horizon explicite de projection des flux (DCF / RIM).",

    # Croissance
    "growth_g": (
        "Taux de croissance annuel appliqué aux flux ou résultats "
        "pendant la période explicite."
    ),
    "growth_perp": (
        "Taux de croissance de long terme utilisé pour la valeur terminale. "
        "Doit rester inférieur à la croissance nominale de l’économie."
    ),

    # Risque / taux
    "rf": "Taux sans risque (obligations souveraines long terme).",
    "mrp": "Prime de risque actions exigée par le marché.",
    "beta": "Mesure du risque systématique par rapport au marché.",

    # Structure financière
    "cost_debt": "Coût de la dette avant impôt.",
    "tax_rate": "Taux d’impôt utilisé pour le coût de la dette après impôt.",
    "target_weights": "Structure cible Dette / Fonds propres.",

    # Monte Carlo
    "volatility": (
        "Écart-type appliqué à une hypothèse dans une analyse Monte Carlo. "
        "Utilisé uniquement pour mesurer l’incertitude."
    ),
}

# ==============================================================================
# MÉTHODES DE VALORISATION — DCF
# ==============================================================================

# ------------------------------------------------------------------------------
# DCF STANDARD — FCFF TWO-STAGE
# ------------------------------------------------------------------------------

DCF_STANDARD_TITLE = "### DCF Standard — FCFF Two-Stage"

DCF_STANDARD_SECTIONS = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode DCF reposant sur la projection directe du "
                "Free Cash Flow to the Firm (FCFF) sur un horizon explicite, "
                "suivie d’une valeur terminale."
            ),
            (
                "> Adaptée aux entreprises matures avec flux stables."
            ),
        ],
    },
    {
        "subtitle": "#### Principe",
        "latex_blocks": [
            r"""
            V = \sum_{t=1}^{n} \frac{FCFF_t}{(1+WACC)^t}
            + \frac{FCFF_n (1+g)}{(WACC - g)} \times \frac{1}{(1+WACC)^n}
            """
        ],
    },
    {
        "subtitle": "#### Invariants",
        "markdown_blocks": [
            "WACC strictement supérieur à la croissance terminale.",
            "Flux de trésorerie économiquement cohérents.",
        ],
    },
]

# ------------------------------------------------------------------------------
# DCF FONDAMENTAL — FCFF NORMALISÉ
# ------------------------------------------------------------------------------

DCF_FUNDAMENTAL_TITLE = "### DCF Fondamental — FCFF Normalisé"

DCF_FUNDAMENTAL_SECTIONS = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode DCF reposant sur un flux de trésorerie "
                "normalisé, représentatif d’un cycle économique moyen."
            ),
            (
                "> Approche privilégiée pour les entreprises cycliques."
            ),
        ],
    },
    {
        "subtitle": "#### Construction du flux",
        "latex_blocks": [
            r"""
            FCFF = EBIT(1 - t)
            + D\&A
            - Capex_{normatif}
            - \Delta BFR
            """
        ],
    },
    {
        "subtitle": "#### Invariants",
        "markdown_blocks": [
            "FCFF normalisé strictement positif.",
            "Normalisation économiquement justifiée.",
        ],
    },
]

# ------------------------------------------------------------------------------
# DCF CROISSANCE — REVENUE-DRIVEN
# ------------------------------------------------------------------------------

DCF_GROWTH_TITLE = "### DCF Croissance — Revenue-Driven FCFF"

DCF_GROWTH_SECTIONS = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode DCF adaptée aux entreprises en forte croissance, "
                "reposant sur la projection du chiffre d’affaires "
                "et la convergence progressive des marges."
            ),
            (
                "> Typiquement utilisée pour les sociétés tech / scale-up."
            ),
        ],
    },
    {
        "subtitle": "#### Principe",
        "latex_blocks": [
            r"""
            FCFF_t = Revenue_t \times Margin_t
            """
        ],
    },
    {
        "subtitle": "#### Invariants",
        "markdown_blocks": [
            "Convergence des marges vers un niveau soutenable.",
            "Croissance long terme inférieure à la croissance économique.",
        ],
    },
]

# ==============================================================================
# MÉTHODES DE VALORISATION — NON DCF
# ==============================================================================

# ------------------------------------------------------------------------------
# RIM — RESIDUAL INCOME MODEL (BANQUES)
# ------------------------------------------------------------------------------

RIM_TITLE = "### Residual Income Model (RIM) — Institutions financières"

RIM_SECTIONS = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode de valorisation fondée sur les profits résiduels, "
                "particulièrement adaptée aux banques et assurances."
            ),
            (
                "> Basée sur le clean surplus accounting."
            ),
        ],
    },
    {
        "subtitle": "#### Principe",
        "latex_blocks": [
            r"""
            IV = BV_0 + \sum \frac{RI_t}{(1+Ke)^t}
            """
        ],
    },
    {
        "subtitle": "#### Invariants",
        "markdown_blocks": [
            "Book Value strictement positif.",
            "Coût des fonds propres pertinent.",
        ],
    },
]

# ------------------------------------------------------------------------------
# GRAHAM — MÉTHODE HEURISTIQUE
# ------------------------------------------------------------------------------

GRAHAM_TITLE = "### Graham Intrinsic Value — Formule révisée (1974)"

GRAHAM_SECTIONS = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode heuristique proposée par Benjamin Graham "
                "pour estimer une valeur intrinsèque à partir du bénéfice."
            ),
            (
                "> Usage comparatif uniquement, non DCF."
            ),
        ],
    },
    {
        "subtitle": "#### Formule",
        "latex_blocks": [
            r"""
            IV = EPS \times (8.5 + 2g) \times \frac{4.4}{Y_{AAA}}
            """
        ],
    },
    {
        "subtitle": "#### Limites",
        "markdown_blocks": [
            "Méthode sensible aux hypothèses.",
            "Non adaptée à une décision d’investissement isolée.",
        ],
    },
]

# ==============================================================================
# EXTENSIONS — INCERTITUDE
# ==============================================================================

# ------------------------------------------------------------------------------
# MONTE CARLO — EXTENSION PROBABILISTE
# ------------------------------------------------------------------------------

MONTE_CARLO_TITLE = "### Extension Monte Carlo — Analyse d’incertitude"

MONTE_CARLO_SECTIONS = [
    {
        "subtitle": "#### Principe",
        "markdown_blocks": [
            (
                "Monte Carlo est une extension probabiliste appliquée "
                "uniquement aux hypothèses d’entrée."
            ),
            (
                "> Ce n’est PAS une méthode de valorisation autonome."
            ),
        ],
    },
    {
        "subtitle": "#### Variables stochastiques",
        "markdown_blocks": [
            "Croissance.",
            "Paramètres de risque (beta, composantes du WACC).",
        ],
    },
    {
        "subtitle": "#### Sorties",
        "markdown_blocks": [
            "Distribution des valeurs intrinsèques.",
            "Quantiles (P10, P50, P90).",
            "Mesure de la dispersion et de l’incertitude.",
        ],
    },
]

# ==============================================================================
# AUDIT & CONFIDENCE SCORE
# ==============================================================================

AUDIT_TITLE = "### Audit & Confidence Score — Méthode normalisée"

AUDIT_INTRO = (
    "Le Confidence Score mesure la robustesse et le niveau d’incertitude "
    "d’une valorisation financière. Il ne modifie jamais la valeur intrinsèque, "
    "mais en qualifie la fiabilité selon des critères normalisés."
)
