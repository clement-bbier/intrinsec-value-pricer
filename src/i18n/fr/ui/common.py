"""
core/i18n/fr/ui/common.py
Textes transverses et métadonnées de base du système.
Note : Version Institutionnelle - Zéro émoji - Terminologie Finance de Marché.
"""

from src.models import VariableSource


class CommonTexts:
    """Référentiel des textes génériques et statuts institutionnels."""

    # --- Métadonnées Application ---
    APP_TITLE = "Intrinsic Value Engine"
    APP_SUBTITLE = "Ingénierie Financière & Analyse de Risque"
    AUTHOR_NAME = "Clément Barbier"
    DEVELOPED_BY = "Developpé par"

    # --- Boutons et Actions ---
    RUN_BUTTON = "Exécuter l'analyse"
    VALIDATE_BUTTON = "Confirmer les hypothèses"
    DEFAULT_TICKER = "AAPL"

    # --- Valeurs par défaut et Fallbacks ---
    VALUE_NOT_AVAILABLE = "N/A"
    VALUE_AUTO = "MODÈLE"
    UNIT_YEARS = "ans"

    # --- En-têtes de Tableaux ---
    TABLE_HEADER_METRIC = "Indicateur"
    TABLE_HEADER_VALUE = "Valeur"

    # --- Statuts de Calcul (Glass Box) ---
    STATUS_CALCULATED = "Calculé"
    STATUS_AUDITED = "Audité"
    STATUS_ADJUSTED = "Ajusté"

    # --- Labels de Composants Glass Box ---
    STEP_GENERIC_LABEL = "Calcul spécifique"
    DATA_ORIGIN_LABEL = "Provenance des données"
    AUTO_VALUE_IGNORED = "Valeur auto ignorée"
    INTERPRETATION_LABEL = "Note d'analyse"

    CURRENCY = "Devise"

    SOURCE_LABELS = {
        VariableSource.YAHOO_FINANCE: "Yahoo Finance",
        VariableSource.MACRO_PROVIDER: "Données Macro",
        VariableSource.CALCULATED: "Moteur Interne",
        VariableSource.MANUAL_OVERRIDE: "Saisie Manuelle",
    }


class OnboardingTexts:
    """Contenu structurel de la page d'accueil et des piliers."""

    APP_TITLE = "Intrinsic Value Engine"

    COMPLIANCE_TITLE = "Avertissement Légal"
    COMPLIANCE_BODY = "Ce moteur de valorisation est un outil d'analyse quantitative fourni à titre purement informatif. Il ne constitue pas un conseil en investissement. L'utilisateur assume l'entière responsabilité des décisions financières découlant de l'utilisation de cet outil."
    TITLE_INTRO = "Introduction"
    INTRO_ONBOARDING = """
        Cette plateforme déploie un moteur d'orchestration financière capable de structurer des chaînes de calcul basées sur des modèles de valorisation académiques de référence.

        L'architecture propose deux parcours distincts :
        le mode **Standard**, qui automatise la récupération des données pour une restitution en 3 onglets, et le mode **Approfondi**, offre la liberté de modifier manuellement chaque variable d'entrée et permet d'enrichir l'analyse jusqu'à 5 onglets thématiques selon les extensions sélectionnées.

        La fiabilité de l'évaluation repose sur un flux de données hybride, associant Yahoo Finance à un module d'extraction propriétaire pour les métriques non standardisées (RTFM pour changer de provider).
        L'intégrité du moteur est garantie par des mécanismes de validation automatique et de substitution, sécurisant le calcul même en cas de données sources incomplètes ou incohérentes.

        Les six extensions analytiques disponibles incluent : la simulation de Monte Carlo, l'analyse de sensibilité, l'étude de scénarios, le backtest historique, la comparaison par multiples de pairs et la segmentation SOTP (Sum of the Parts).
        """
    MODEL_SECTION_TITLE = "Modèles Implémentés"
    MODELS_EXPLORER = """
    #### 1. Moteurs de Flux de Trésorerie
    * **DCF : Standard (FCFF)** : L'approche par l'entité. Le moteur calcule la Valeur d'Entreprise en actualisant les flux de trésorerie disponibles (FCFF) au **WACC**, avec une valeur terminale basée sur le taux de croissance perpétuelle ($g$).
    * **DCF : Fondamental (Normalisé)** : Logique Damodaran. Ce modèle projette la capacité bénéficiaire structurelle en utilisant le couple **ROIC** (Retour sur Capitaux Investis) et **Taux de Réinvestissement**.
    * **DCF : Croissance (Revenue-Driven)** : Une variante dynamique qui reconstruit l'**EBIT** et les flux futurs en corrélant la croissance du chiffre d'affaires à l'évolution des marges opérationnelles cibles.
    * **DCF : FCFE (Equity Value)** : Contrairement à l'approche entité, ce moteur calcule directement la valeur des capitaux propres en actualisant les flux de trésorerie résiduels après service de la dette au coût des fonds propres (**Ke**).

    #### 2. Moteurs par les Revenus
    * **Modèle DDM (Dividend Discount)** : Approche par le rendement pur. Il évalue la cible en actualisant uniquement les dividendes futurs attendus au coût des fonds propres (**Ke**).
    * **Modèle RIM (Residual Income)** : Dédié au secteur financier. Il valorise l'entreprise comme la somme de sa Valeur Comptable et de la valeur actuelle de ses bénéfices excédentaires (**Net Income - (Ke * BV)**).

    #### 3. Moteur Statique
    * **Formule de Graham** : Implémentation révisée de la logique "Intrinsèque". Elle calcule une valeur pivot basée sur l'**EPS** et la croissance attendue, ajustée par le rendement actuel des obligations AAA.
    """
    RESULTS_SECTION_TITLE = "Organisation des résultats"

    # PILLIER 1 (Permanent) : inputs_summary.py
    PILLAR_1_TITLE = "1. Synthèse des Hypothèses (Permanent)"
    PILLAR_1_DESC = """
        - **Audit des Données** : Récapitulatif exhaustif des variables extraites (Consensus, Risk-Free Rate, Bêta).
        - **Configuration** : Rappel des paramètres de session et des hypothèses de croissance court terme.
        """

    # PILLIER 2 (Permanent) : calculation_proof.py
    PILLAR_2_TITLE = "2. Preuve de Calcul (Permanent)"
    PILLAR_2_DESC = """
        - **Moteur Glass Box** : Accès transparent à la mécanique de calcul intermédiaire.
        - **Bridge de Flux** : Décomposition du passage de l'EBIT aux Flux de Trésorerie Disponibles (FCFF/FCFE) et à la Valeur d'Entreprise.
        """

    # PILLIER 3 (Permanent) : market_analysis.py / peer_multiples.py
    PILLAR_3_TITLE = "3. Analyse Comparative Sectorielle (Permanent)"
    PILLAR_3_DESC = """
        - **Multiples de Marché** : Positionnement de la cible face aux moyennes sectorielles (P/E, EV/EBITDA, P/B).
        - **Évaluation Relative** : Score de surévaluation ou sous-évaluation par rapport aux comparables théoriques.
        """

    # PILLIER 4 (Optionnel) : monte_carlo, sensitivity, scenarios, backtest
    PILLAR_4_TITLE = "4. Ingénierie du Risque (Extensions)"
    PILLAR_4_DESC = """
        - **Simulation de Monte Carlo** : Analyse stochastique sur 5 000 itérations pour modéliser la distribution de probabilité du prix.
        - **Matrice de Sensibilité** : Impact combiné des variations du WACC et du taux de croissance ($g$).
        - **Scénarios Discrets** : Simulation de trajectoires spécifiques (Bull / Bear Cases).
        - **Backtesting 10 ans** : Vérification de la fiabilité historique des prédictions du modèle sur la dernière décennie.
        """

    # PILLIER 5 (Optionnel) : peers, sotp
    PILLAR_5_TITLE = "5. Analyses Spécifiques (Extensions)"
    PILLAR_5_DESC = """
        - **Analyse par Comparables (Peers)** : Comparaison granulaire avec un panel personnalisé de concurrents directs.
        - **Somme des Parties (SOTP)** : Valorisation désagrégée par segment d'activité (Segmented Valuation).
        """


class FeedbackMessages:
    """Messages système et alertes de validation."""

    TICKER_REQUIRED_SIDEBAR = "Identifiant (Ticker) requis pour initialiser l'analyse."
    TICKER_INVALID = "Symbole boursier non identifié par le fournisseur de données."
    CALCULATION_SUCCESS = "Valorisation terminée avec succès."


class TooltipsTexts:
    """Aide contextuelle pour les concepts financiers (Indispensable pour corriger l'ImportError)."""

    MARKET_CAP_HELP = "Capitalisation boursière à la date d'analyse."
    WACC_HELP = "Coût Moyen Pondéré du Capital (WACC) utilisé pour actualiser les flux FCFF."
    KE_HELP = "Coût des fonds propres (Ke) utilisé pour actualiser les flux FCFE ou DDM."
    GROWTH_G = "Taux de croissance perpétuelle (g) utilisé pour la valeur terminale."
    SBC_HELP = "Stock-Based Compensation : ajustement de la dilution liée aux attributions d'actions au management."
    TERMINAL_VALUE = "Valeur de l'entreprise au-delà de l'horizon de prévision explicite (Modèle de Gordon-Shapiro)."
    MARGIN_SAFETY = "Décote appliquée entre la valeur intrinsèque et le cours actuel pour absorber l'incertitude."


class UIMessages:
    """Messages d'information et d'erreur de l'interface utilisateur."""

    BACKTEST_INSUFFICIENT_DATA = "Données historiques insuffisantes pour le backtesting."
    TECHNICAL_DETAILS = "Détails techniques"
    NO_VALID_PERIOD_DATA = "Historique financier insuffisant pour établir une tendance robuste."
    CHART_UNAVAILABLE = "Données insuffisantes pour la génération graphique."
    NO_CALCULATION_STEPS = "Aucune trace de calcul disponible pour ce modèle."
    NO_DETAILED_TESTS = "Aucun test d'intégrité supplémentaire requis."
    NO_TABS_TO_DISPLAY = "Initialisation de l'orchestrateur..."

    # Main app messages
    PAGE_TITLE = "Intrinsic Value Pricer"
    DISMISS_ERROR = "Dismiss Error"
    NO_RESULT_MODULES = "No result modules available to display."

    # Chart messages
    PRICE_HISTORY_UNAVAILABLE = "Données de prix historiques indisponibles."
    SENSITIVITY_MATRIX_ERROR = "Impossible de générer la matrice de sensibilité (Taux <= Croissance)."
    NO_MAJOR_CALC_STEPS = "Aucune étape majeure disponible pour ce calcul."

    # PDF / Export
    DOWNLOAD_PDF_BTN = "Générer le Rapport d'Analyse (PDF)"
    GENERATING_PDF = "Compilation du rapport institutionnel..."
    PDF_SUCCESS = "Le rapport est prêt pour l'archivage."
    PDF_UNAVAILABLE = "Module d'exportation non détecté sur l'instance courante."
    PDF_ERROR = "Erreur lors de la génération du flux PDF."


class LegalTexts:
    """
    Textes juridiques et de conformité (Disclaimers).
    """

    COMPLIANCE_TITLE = "AVERTISSEMENT LÉGAL"
    COMPLIANCE_BODY = (
        "Cet outil est une aide à la décision à usage strictement éducatif et informatif. "
        "Il ne constitue en aucun cas un conseil en investissement, une recommandation d'achat "
        "ou une sollicitation. Les modèles de valorisation (DCF, RIM, Graham) reposent sur des "
        "hypothèses qui peuvent ne pas se réaliser. L'utilisateur est seul responsable de ses "
        "choix d'investissement."
    )
