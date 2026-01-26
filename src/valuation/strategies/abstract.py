"""
Stratégie de valorisation abstraite.

Référence Académique : Pattern Strategy (Gang of Four)
Domaine Économique : Valorisation financière institutionnelle
Invariants du Modèle : Validation systématique des contrats de sortie
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from src.exceptions import CalculationError
from src.models import (
    CalculationStep, CompanyFinancials, DCFParameters,
    TraceHypothesis, ValuationResult
)
# Import depuis core.i18n
from src.i18n import CalculationErrors

logger = logging.getLogger(__name__)

class ValuationStrategy(ABC):
    """
    Classe de base pour toutes les stratégies de valorisation.
    Gère la validation du contrat de sortie et la traçabilité Glass Box.
    """

    def __init__(self, glass_box_enabled: bool = True):
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> ValuationResult:
        """
        Point d'entrée de la stratégie.
        Doit instancier un pipeline ou exécuter sa logique propre.
        """
        pass

    def add_step(
            self,
            step_key: str,
            result: float,
            numerical_substitution: str,
            label: str = "",
            theoretical_formula: str = "",
            interpretation: str = "",
            source: str = "",
            hypotheses: Optional[List[TraceHypothesis]] = None
    ) -> None:
        """
        Enregistre une étape de calcul dans la trace Glass Box pour l'auditabilité.

        Cette méthode permet aux stratégies de capturer les étapes intermédiaires,
        assurant une transparence totale pour le rapport d'audit final.

        Parameters
        ----------
        step_key : str
            Identifiant unique de l'étape (lié au registre Glass Box).
        result : float
            Résultat numérique brut du calcul.
        numerical_substitution : str
            Détail du calcul avec les valeurs réelles injectées (ex: "100 * 1.05").
        label : str, optional
            Libellé d'affichage. Si vide, `step_key` est utilisé par défaut.
        theoretical_formula : str, optional
            Expression LaTeX de la formule (StrategyFormulas).
        interpretation : str, optional
            Note pédagogique expliquant la logique (StrategyInterpretations).
        source : str, optional
            Origine de la donnée ou de la méthode (StrategySources).
        hypotheses : List[TraceHypothesis], optional
            Liste des hypothèses critiques associées à cette étape.

        Notes
        -----
        - Ne s'exécute que si `self.glass_box_enabled` est True.
        - L'identifiant séquentiel `step_id` est auto-généré.
        """
        if not self.glass_box_enabled:
            return

        step = CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            result=result,
            interpretation=interpretation,
            source=source
        )

        self.calculation_trace.append(step)

    @staticmethod
    def generate_audit_report(result: ValuationResult) -> None:
        """
        Génère le rapport d'audit institutionnel pour un résultat de valorisation.

        Cette méthode identifie l'auditeur approprié en fonction du mode de
        valorisation et délègue le calcul du score de fiabilité à l'AuditEngine.

        Parameters
        ----------
        result : ValuationResult
            L'objet résultat à auditer (DCF, RIM, Graham, Multiples).

        Notes
        -----
        Si la requête originale est absente du résultat, une requête de
        secours (fallback) est générée pour permettre l'exécution de l'audit.
        Les imports sont effectués localement pour éviter les dépendances circulaires.
        """
        from infra.auditing.audit_engine import AuditEngine, AuditorFactory
        from src.models import (
            ValuationRequest, InputSource, ValuationMode,
            DCFValuationResult, RIMValuationResult,
            GrahamValuationResult, MultiplesValuationResult
        )

        if result.request is None:
            # Détermination dynamique du mode de valorisation pour la requête de secours
            if isinstance(result, DCFValuationResult):
                mode = ValuationMode.FCFF_STANDARD
            elif isinstance(result, RIMValuationResult):
                mode = ValuationMode.RIM
            elif isinstance(result, GrahamValuationResult):
                mode = ValuationMode.GRAHAM
            else:
                mode = ValuationMode.FCFF_STANDARD  # Fallback par défaut

            result.request = ValuationRequest(
                ticker=result.financials.ticker,
                projection_years=result.params.growth.projection_years,
                mode=mode,
                input_source=InputSource.AUTO,
                options={}
            )

        # Sélection de l'auditeur spécialisé selon le type de résultat
        if isinstance(result, MultiplesValuationResult):
            from infra.auditing.auditors import MultiplesAuditor
            auditor = MultiplesAuditor()
        else:
            auditor = AuditorFactory.get_auditor(result.request.mode)

        result.audit_report = AuditEngine.compute_audit(result, auditor)

    def verify_output_contract(self, result: ValuationResult) -> None:
        """Vérifie que l'objet résultat respecte les invariants du modèle (SOLID)."""
        contract = result.build_output_contract()
        if not contract.is_valid():
            raise CalculationError(CalculationErrors.CONTRACT_VIOLATION.format(cls=self.__class__.__name__))

    def _merge_traces(self, result: ValuationResult) -> None:
        """
        Fusionne la trace de la stratégie avec celle du résultat (Pipeline).
        Garantit que les étapes spécifiques (ex: sélection du FCF) apparaissent
        au début de la preuve de calcul.
        """
        # On insère les étapes de la stratégie au début de la trace globale
        result.calculation_trace = self.calculation_trace + result.calculation_trace
