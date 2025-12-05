from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Méthode 1 – DCF Simple (FCFF TTM)
# ---------------------------------------------------------------------------

SIMPLE_DCF_TITLE: str = "### Formule de Valorisation – Méthode 1 (DCF Simple)"

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

# ---------------------------------------------------------------------------
# Méthode 2 – DCF Fondamental (3-Statement Light)
# ---------------------------------------------------------------------------

FUNDAMENTAL_DCF_TITLE: str = "### Formule de Valorisation – Méthode 2 (DCF Fondamental, 3-Statement Light)"

FUNDAMENTAL_DCF_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### Étape 1 – Construction du NOPAT à partir de l'EBIT",
        "latex_blocks": [
            r"EBIT = \text{Résultat Opérationnel}",
            r"Taux_{\text{impôt effectif}} = \dfrac{\text{Tax Expense}}{\text{Pretax Income}}",
            r"NOPAT = EBIT \times (1 - Taux_{\text{impôt effectif}})",
        ],
        "markdown_blocks": [
            (
                "- Le **NOPAT** (Net Operating Profit After Tax) mesure le résultat opérationnel après impôt, "
                "en neutralisant la structure de capital.\n"
                "- Le **Taux d'impôt effectif** est calculé à partir des états financiers historiques "
                "(Tax Expense / Pretax Income) lorsque c'est possible.\n"
                "- À défaut, un taux d'impôt par défaut (ex: 25%) est utilisé."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 2 – Besoin en Fonds de Roulement (NWC) et ΔNWC",
        "latex_blocks": [
            r"NWC_t = \text{Accounts Receivable}_t + \text{Inventory}_t - \text{Accounts Payable}_t",
            r"\Delta NWC_t = NWC_t - NWC_{t-1}",
        ],
        "markdown_blocks": [
            (
                "- Le **Besoin en Fonds de Roulement (NWC)** reflète le capital immobilisé dans les opérations courantes "
                "(créances clients, stocks, dettes fournisseurs).\n"
                "- La **variation de NWC** ($\\Delta NWC$) représente la consommation (ou libération) de trésorerie "
                "liée à l'évolution du cycle d'exploitation."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 3 – FCFF Fondamental Annuel",
        "latex_blocks": [
            r"FCFF_t = NOPAT_t + D\&A_t - Capex_t - \Delta NWC_t",
        ],
        "markdown_blocks": [
            (
                "- $D\\&A$ correspond aux **dotations aux amortissements et dépréciations**.\n"
                "- `Capex` correspond aux **dépenses d'investissement** (généralement négatives dans les flux de trésorerie).\n"
                "- $\\Delta NWC$ capte l'impact du besoin en fonds de roulement sur la trésorerie disponible."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 4 – Lissage du FCFF₀ sur plusieurs années",
        "latex_blocks": [
            r"FCFF_0 = \dfrac{FCFF_{t} + FCFF_{t-1} + FCFF_{t-2}}{3}",
        ],
        "markdown_blocks": [
            (
                "- Le **FCFF₀ fondamental** utilisé dans le DCF est une moyenne sur plusieurs années (par exemple 3 ans) "
                "afin de lisser les effets de volatilité ou d'événements exceptionnels.\n"
                "- Ce $FCFF_0$ lissé est celui qui apparaît dans les hypothèses de la Méthode 2 dans l'interface."
            ),
        ],
    },
    {
        "subtitle": "#### Étape 5 – DCF sur la base du FCFF Fondamental",
        "latex_blocks": [
            r"FCFF_t = FCFF_{0} \times (1 + g_{\text{FCFF}})^{t} \quad \text{pour } t = 1,\dots,n",
            r"VE_{\text{phase 1}} = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + CMPC)^t}",
            r"FCFF_{n+1} = FCFF_n \times (1 + g_{\infty})",
            r"VT = \frac{FCFF_{n+1}}{CMPC - g_{\infty}}",
            r"VE_{\text{totale}} = VE_{\text{phase 1}} + \frac{VT}{(1 + CMPC)^n}",
            r"\text{Valeur Capitaux Propres} = VE_{\text{totale}} - \text{Dette Totale} + \text{Liquidités}",
            r"\text{VI par action} = \dfrac{\text{Valeur Capitaux Propres}}{\text{Actions en circulation}}",
        ],
        "markdown_blocks": [
            (
                "- La **structure du DCF** (actualisation des flux, valeur terminale, passage à la valeur des capitaux propres) "
                "reste identique à la Méthode 1.\n"
                "- La **différence clé** est la qualité de $FCFF_0$, qui est ici dérivé d'une analyse 3-états (Compte de Résultat, "
                "Bilan, Cash-Flow) et lissé sur plusieurs années."
            ),
        ],
    },
]
