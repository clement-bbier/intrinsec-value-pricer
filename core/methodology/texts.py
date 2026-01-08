"""
core/methodology/texts.py
SOURCE DE VÉRITÉ — DOCUMENTATION MÉTHODOLOGIQUE CANONIQUE
Version : V3.1 — Hedge Fund Standard (Typed & Standardized)
"""

from typing import Dict, List, TypedDict, Optional

# ==============================================================================
# TYPES NORMATIFS
# ==============================================================================

class MethodologySection(TypedDict):
    """Structure de données pour une section de documentation."""
    subtitle: str
    markdown_blocks: List[str]
    latex_blocks: Optional[List[str]]  # Optionnel pour la flexibilité

# ==============================================================================
# TOOLTIPS — AIDES CONTEXTUELLES UI
# ==============================================================================

# Alignement strict avec la convention (0 = Auto Yahoo) validée au Jalon 1
TOOLTIPS: Dict[str, str] = {
    "ticker": "Symbole boursier (ex: AAPL, LVMH.PA). Saisissez 0 pour laisser le système chercher. ",
    "years": "Horizon explicite de projection des flux (DCF / RIM). ",

    # Croissance
    "growth_g": (
        "Taux de croissance annuel (décimal). Saisissez 0 pour activer l'Auto Yahoo. "
    ),
    "growth_perp": (
        "Taux de croissance à l'infini (gn). Saisissez 0 pour activer l'Auto Yahoo. "
    ),

    # Risque / taux
    "rf": "Taux sans risque (Rf). Saisissez 0 pour activer l'Auto Yahoo. ",
    "mrp": "Prime de risque marché (MRP). Saisissez 0 pour activer l'Auto Yahoo. ",
    "beta": "Coefficient Beta (β). Saisissez 0 pour activer l'Auto Yahoo. ",

    # Structure financière
    "cost_debt": "Coût de la dette (kd). Saisissez 0 pour activer l'Auto Yahoo. ",
    "tax_rate": "Taux d'imposition (τ). Saisissez 0 pour activer l'Auto Yahoo. ",
    "target_weights": "Structure cible Dette / Fonds propres. ",

    # Monte Carlo
    "volatility": (
        "Écart-type pour Monte Carlo. Saisissez 0 pour activer l'Auto Yahoo. "
    ),
}

# ==============================================================================
# MÉTHODES DE VALORISATION — DCF
# ==============================================================================

# ------------------------------------------------------------------------------
# DCF STANDARD — FCFF TWO-STAGE
# ------------------------------------------------------------------------------

DCF_STANDARD_TITLE: str = "### DCF Standard — FCFF Two-Stage "

DCF_STANDARD_SECTIONS: List[MethodologySection] = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode DCF reposant sur la projection directe du "
                "Free Cash Flow to the Firm (FCFF) sur un horizon explicite, "
                "suivie d’une valeur terminale. "
            ),
            (
                "> Adaptée aux entreprises matures avec flux stables. "
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
            "WACC strictement supérieur à la croissance terminale. ",
            "Flux de trésorerie économiquement cohérents. ",
        ],
    },
]

# ------------------------------------------------------------------------------
# DCF FONDAMENTAL — FCFF NORMALISÉ
# ------------------------------------------------------------------------------

DCF_FUNDAMENTAL_TITLE: str = "### DCF Fondamental — FCFF Normalisé "

DCF_FUNDAMENTAL_SECTIONS: List[MethodologySection] = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode DCF reposant sur un flux de trésorerie "
                "normalisé, représentatif d’un cycle économique moyen. "
            ),
            (
                "> Approche privilégiée pour les entreprises cycliques. "
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
            "FCFF normalisé strictement positif. ",
            "Normalisation économiquement justifiée. ",
        ],
    },
]

# ------------------------------------------------------------------------------
# DCF CROISSANCE — REVENUE-DRIVEN
# ------------------------------------------------------------------------------

DCF_GROWTH_TITLE: str = "### DCF Croissance — Revenue-Driven FCFF "

DCF_GROWTH_SECTIONS: List[MethodologySection] = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode DCF adaptée aux entreprises en forte croissance, "
                "reposant sur la projection du chiffre d’affaires "
                "et la convergence progressive des marges. "
            ),
            (
                "> Typiquement utilisée pour les sociétés tech / scale-up. "
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
            "Convergence des marges vers un niveau soutenable. ",
            "Croissance long terme inférieure à la croissance économique. ",
        ],
    },
]

# ==============================================================================
# MÉTHODES DE VALORISATION — NON DCF
# ==============================================================================

# ------------------------------------------------------------------------------
# RIM — RESIDUAL INCOME MODEL (BANQUES)
# ------------------------------------------------------------------------------

RIM_TITLE: str = "### Residual Income Model (RIM) — Institutions financières "

RIM_SECTIONS: List[MethodologySection] = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode de valorisation fondée sur les profits résiduels, "
                "particulièrement adaptée aux banques et assurances. "
            ),
            (
                "> Basée sur le clean surplus accounting. "
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
            "Book Value strictement positif. ",
            "Coût des fonds propres pertinent. ",
        ],
    },
]

# ------------------------------------------------------------------------------
# GRAHAM — MÉTHODE HEURISTIQUE
# ------------------------------------------------------------------------------

GRAHAM_TITLE: str = "### Graham Intrinsic Value — Formule révisée (1974) "

GRAHAM_SECTIONS: List[MethodologySection] = [
    {
        "subtitle": "#### Concept",
        "markdown_blocks": [
            (
                "Méthode heuristique proposée par Benjamin Graham "
                "pour estimer une valeur intrinsèque à partir du bénéfice. "
            ),
            (
                "> Usage comparatif uniquement, non DCF. "
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
            "Méthode sensible aux hypothèses. ",
            "Non adaptée à une décision d’investissement isolée. ",
        ],
    },
]

# ==============================================================================
# EXTENSIONS — INCERTITUDE
# ==============================================================================

# ------------------------------------------------------------------------------
# MONTE CARLO — EXTENSION PROBABILISTE
# ------------------------------------------------------------------------------

MONTE_CARLO_TITLE: str = "### Extension Monte Carlo — Analyse d’incertitude "

MONTE_CARLO_SECTIONS: List[MethodologySection] = [
    {
        "subtitle": "#### Principe",
        "markdown_blocks": [
            (
                "Monte Carlo est une extension probabiliste appliquée "
                "uniquement aux hypothèses d’entrée. "
            ),
            (
                "> Ce n’est PAS une méthode de valorisation autonome. "
            ),
        ],
    },
    {
        "subtitle": "#### Variables stochastiques",
        "markdown_blocks": [
            "Croissance. ",
            "Paramètres de risque (beta, composantes du WACC). ",
        ],
    },
    {
        "subtitle": "#### Sorties",
        "markdown_blocks": [
            "Distribution des valeurs intrinsèques. ",
            "Quantiles (P10, P50, P90). ",
            "Mesure de la dispersion et de l’incertitude. ",
        ],
    },
]

# ==============================================================================
# AUDIT & CONFIDENCE SCORE
# ==============================================================================

AUDIT_TITLE: str = "### Audit & Confidence Score — Méthode normalisée "

AUDIT_INTRO: str = (
    "Le Confidence Score mesure la robustesse et le niveau d’incertitude "
    "d’une valorisation financière. Il ne modifie jamais la valeur intrinsèque, "
    "mais en qualifie la fiabilité selon des critères normalisés. "
)