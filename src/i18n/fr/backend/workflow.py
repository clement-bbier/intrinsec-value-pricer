"""
core/i18n/fr/backend/workflow.py
Messages d'etat du cycle de vie de l'analyse.
"""


class WorkflowTexts:
    """Messages d'etat du workflow."""

    STATUS_DEGRADED_LABEL = "Mode Dégradé : Multiples Sectoriels"
    STATUS_MAIN_LABEL = "Initialisation de l'analyse..."
    STATUS_DATA_ACQUISITION = "Acquisition des donnees de marche et macro-économiques..."
    STATUS_SMART_MERGE = "Conciliation des hypotheses (Smart Merge)..."
    STATUS_ENGINE_RUN = "Execution du moteur de calcul : {mode}..."
    STATUS_MC_RUN = "Simulation stochastique, tests de sensibilité et stress-testing en cours..."
    STATUS_AUDIT_GEN = "Generation du rapport d'audit et score de confiance..."
    STATUS_PEER_DISCOVERY = "Identification des pairs et concurrents sectoriels..."
    STATUS_PEER_FETCHING = r"Extraction des multiples de marche ({current}/{total})..."
    STATUS_COMPLETE = "Analyse finalisée avec succès"
    STATUS_INTERRUPTED = "Analyse interrompue"
    STATUS_CRITICAL_ERROR = "Erreur système critique"
    STATUS_SCENARIOS_RUN = "#### Orchestration des trajectoires Bull/Base/Bear..."
    STATUS_BACKTEST_RUN = "Simulation des valorisations historiques (Backtesting)..."
    STATUS_BACKTEST_COMPLETE = "Validation historique terminée."

    DIAG_EXPANDER_TITLE = "Details techniques et remediation"
    DIAG_ACTION_LABEL = "Action recommandée :"

    PREFIX_CRITICAL = "**ARRET CRITIQUE :**"
    PREFIX_WARNING = "**AVERTISSEMENT :**"
    PREFIX_INFO = "**INFORMATION :**"

    PEER_NOT_FOUND = "Multiples de marche indisponibles (Cohorte insuffisante)"
    PEER_SUCCESS = "Cohorte sectorielle finalisée avec succès."
