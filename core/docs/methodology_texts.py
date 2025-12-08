from typing import List, Dict, Any

# ===========================================================================
# 1. Méthode DCF Simple (Snapshot / TTM)
# ===========================================================================

SIMPLE_DCF_TITLE: str = "### 📘 Méthode 1 : DCF Simplifié 'Snapshot'"

SIMPLE_DCF_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### 💡 Le Concept en bref",
        "markdown_blocks": [
            (
                "Cette méthode est une **photographie instantanée** de la valeur de l'entreprise. "
                "Elle part du principe que les flux de trésorerie générés au cours des 12 derniers mois (TTM - Trailing Twelve Months) "
                "sont représentatifs de la capacité future de l'entreprise.\n\n"
                "👉 **C'est la méthode idéale pour une première estimation rapide.**"
            ),
        ],
    },
    {
        "subtitle": "#### 🧮 Étape 1 : Le Flux de Trésorerie (FCFF)",
        "markdown_blocks": [
            "Nous calculons le **Free Cash Flow to Firm (FCFF)**, c'est-à-dire l'argent liquide réellement généré par l'activité, avant le paiement de la dette."
        ],
        "latex_blocks": [
            r"FCFF_{\text{TTM}} = \text{Cash Flow Opérationnel} - |\text{Capex}|",
        ],
        "markdown_blocks": [
            (
                "**Détails :**\n"
                "* **Cash Flow Opérationnel (CFO) :** Argent généré par l'activité courante (vente de produits/services).\n"
                "* **Capex (Dépenses d'Investissement) :** Argent dépensé pour maintenir ou moderniser l'outil de production (usines, machines, R&D).\n"
            ),
        ],
    },
    {
        "subtitle": "#### 📉 Étape 2 : La Croissance 'Fade-Down'",
        "markdown_blocks": [
            (
                "Plutôt que de parier sur une croissance constante (irréaliste), nous utilisons un modèle de **décélération linéaire**.\n"
                "La croissance part d'un taux initial (ex: 5%) et ralentit doucement chaque année pour atterrir sur l'inflation (2%) à la fin de la projection."
            ),
        ],
    },
    {
        "subtitle": "#### ⚖️ Étape 3 : L'Actualisation (WACC)",
        "markdown_blocks": [
            "Les flux futurs valent moins que l'argent d'aujourd'hui. Nous les divisons (actualisons) par le **CMPC (Coût Moyen Pondéré du Capital)**, ou WACC en anglais.",
            "Le WACC représente le rendement minimum exigé par les investisseurs (Actionnaires + Banques) pour financer l'entreprise."
        ]
    }
]


# ===========================================================================
# 2. Méthode DCF Fondamental (Expert)
# ===========================================================================

FUNDAMENTAL_DCF_TITLE: str = "### 📙 Méthode 2 : DCF Fondamental & Normatif (Expert)"

FUNDAMENTAL_DCF_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### 💡 Le Concept : Gommer les accidents",
        "markdown_blocks": [
            (
                "Une entreprise peut avoir une mauvaise année (grève, pénurie) ou une année exceptionnelle. "
                "La Méthode 1 se tromperait dans ces cas-là.\n\n"
                "👉 **La Méthode 2 reconstruit un flux 'Normatif' (Normalisé)** en analysant la performance sur 5 ans et en donnant plus de poids aux années récentes."
            ),
        ],
    },
    {
        "subtitle": "#### 🏗️ Étape 1 : Reconstruction Comptable Précise",
        "markdown_blocks": [
            "Nous ne prenons pas le Cash Flow brut. Nous le reconstruisons composante par composante pour chaque année :"
        ],
        "latex_blocks": [
            r"FCFF = \underbrace{EBIT \times (1 - \text{Tax})}_{\text{NOPAT}} + \underbrace{D\&A}_{\text{Charges non-caissées}} - \underbrace{Capex}_{\text{Investissement}} - \underbrace{\Delta BFR}_{\text{Besoin en Fonds de Roulement}}",
        ],
        "markdown_blocks": [
            (
                "**Lexique :**\n"
                "* **EBIT :** Résultat d'Exploitation (Earnings Before Interest & Taxes).\n"
                "* **NOPAT :** Profit opérationnel net après impôts (Net Operating Profit After Tax).\n"
                "* **D&A :** Dépréciations & Amortissements (charges comptables sans sortie d'argent, donc on les rajoute).\n"
                "* **Δ BFR (Variation du BFR) :** Argent immobilisé dans les stocks et les créances clients. Si le BFR augmente, c'est du cash en moins."
            )
        ]
    },
    {
        "subtitle": "#### ⚖️ Étape 2 : La Moyenne Pondérée 'Time-Anchored'",
        "markdown_blocks": [
            (
                "Pour obtenir le flux de départ ($FCFF_0$), nous pondérons les années passées selon leur ancienneté. "
                "L'année la plus récente pèse 5x plus que l'année il y a 5 ans."
            ),
        ],
        "latex_blocks": [
            r"FCFF_{\text{Moyen}} = \frac{\sum_{k=0}^{n} (FCFF_{t-k} \times Poids_k)}{\sum Poids_k}",
            r"\text{où } Poids_0 = 5, Poids_1 = 4, ...",
        ],
        "markdown_blocks": [
            "**Sécurité 'Anti-Virus' :** Si une année contient une donnée manquante (ex: pas de BFR), elle est exclue du calcul sans fausser le poids des autres années."
        ]
    },
    {
        "subtitle": "#### 🛡️ Étape 3 : Le Coût de la Dette Synthétique (Approche Damodaran)",
        "markdown_blocks": [
            (
                "Au lieu de deviner le taux d'intérêt de l'entreprise, nous calculons sa solvabilité réelle via le **Ratio de Couverture des Intérêts (ICR)**."
            )
        ],
        "latex_blocks": [
            r"ICR = \frac{\text{EBIT}}{\text{Charges d'Intérêts}}",
        ],
        "markdown_blocks": [
            (
                "Nous utilisons ensuite les tables du Pr. Damodaran (NYU Stern) pour convertir ce ratio en **Spread de Crédit** (Prime de risque).\n"
                "* Ex: Une entreprise qui gagne 10x ses intérêts (ICR > 10) aura un spread minime (AAA).\n"
                "* Ex: Une entreprise qui peine à payer (ICR < 1.5) aura un spread punitif (Junk Bond)."
            )
        ]
    }
]


# ===========================================================================
# 3. Méthode Monte Carlo (Simulation)
# ===========================================================================

MONTE_CARLO_TITLE: str = "### 📕 Méthode 3 : Simulation Monte Carlo Multivariée"

MONTE_CARLO_SECTIONS: List[Dict[str, Any]] = [
    {
        "subtitle": "#### 💡 Le Concept : Explorer les Futurs Possibles",
        "markdown_blocks": [
            (
                "La valorisation n'est jamais une science exacte. Plutôt que de donner UN chiffre, cette méthode simule **2 000 scénarios différents** "
                "en faisant varier les paramètres clés (Croissance, Risque, Taux)."
            ),
        ],
    },
    {
        "subtitle": "#### 🎲 Moteur : La Matrice de Covariance",
        "markdown_blocks": [
            (
                "Contrairement aux simulateurs basiques qui tirent les dés au hasard, notre modèle utilise une approche **Multivariée**.\n"
                "Il comprend que les variables sont liées entre elles :"
            )
        ],
        "latex_blocks": [
            r"\text{Corrélation } (\rho) \approx -0.4 \text{ entre } \beta \text{ (Risque) et } g \text{ (Croissance)}",
        ],
        "markdown_blocks": [
            (
                "**Traduction financière :** Dans les scénarios où le risque explose (crise, taux hauts, Beta élevé), le modèle force mathématiquement la croissance à baisser.\n"
                "Cela élimine les scénarios absurdes du type *'Croissance record en pleine crise financière'*."
            )
        ]
    },
    {
        "subtitle": "#### 📊 Interprétation des Résultats",
        "markdown_blocks": [
            (
                "Le résultat n'est pas une ligne, c'est une **zone de probabilité** :\n"
                "* **P10 (Scénario Pessimiste) :** Il y a 90% de chances que l'entreprise vaille PLUS que cela.\n"
                "* **P50 (Médiane) :** Le scénario central le plus probable.\n"
                "* **P90 (Scénario Optimiste) :** Il y a seulement 10% de chances que l'entreprise vaille encore plus."
            )
        ]
    }
]