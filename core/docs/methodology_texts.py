from typing import List, Dict, Any

# Titre principal affiché
SIMPLE_DCF_TITLE: str = "### Formule de Valorisation – Méthode 1 (DCF Simple)"

# Séquence de dictionnaires structurant la méthodologie
SIMPLE_DCF_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### Étape 1 – Projection du Free Cash Flow to the Firm (FCFF)",
        "latex_blocks": [
            r"FCFF_0 = \text{Dernier FCFF (TTM)}",
            r"FCFF_t = FCFF_{t-1} \times (1 + g_{\text{FCFF}})"
            r"\quad\text{pour } t = 1,\dots,n",
        ],
        "markdown_blocks": [
            (
                "- `Dernier FCFF` provient du flux de trésorerie d'exploitation moins le CAPEX.\n"
                "- $g_{\\text{FCFF}}$ correspond à la **Croissance FCFF (phase 1)**.\n"
                "- $n$ correspond aux **Années de projection**."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 2 – Actualisation et calcul de la Valeur Terminale (TV)",
        "latex_blocks": [
            r"VE_{\text{phase 1}} = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + CMPC)^t}",
            r"VT = \frac{FCFF_{n+1}}{CMPC - g_{\infty}}",
            r"VE_{\text{totale}} = VE_{\text{phase 1}} + \frac{VT}{(1 + CMPC)^n}",
        ],
        "markdown_blocks": [
            (
                "- `CMPC` (Coût Moyen Pondéré du Capital) est calculé à partir du **Taux sans risque (Rf)**, "
                "la **Prime de risque du marché (MRP)**, le **Coût de la dette (Rd)** et le **Taux d'imposition**.\n"
                "- $g_{\\infty}$ correspond à la **Croissance perpétuelle**."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 3 – De la Valeur d'Entreprise (VE) à la Valeur des Capitaux Propres",
        "latex_blocks": [
            r"\text{Valeur Capitaux Propres} = VE - \text{Dette Totale} + \text{Liquidités et équivalents}",
        ],
        "markdown_blocks": [
            (
                "- On retranche la dette nette et on ajoute la trésorerie et équivalents.\n"
                "- On obtient ainsi la **valeur des capitaux propres**."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 4 – Valeur Intrinsèque par Action",
        "latex_blocks": [
            r"\text{VI par action} = "
            r"\frac{\text{Valeur Capitaux Propres}}{\text{Actions en circulation}}",
        ],
        "markdown_blocks": [
            (
                "La Valeur Intrinsèque utilisée dans la section KPI est le résultat de ces étapes "
                "appliquées aux paramètres affichés dans les tables ci-dessus."
            ),
        ],
    },
]