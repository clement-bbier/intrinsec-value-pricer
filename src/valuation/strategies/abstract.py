"""
core/valuation/strategies/abstract.py

SOCLE ABSTRAIT — VERSION V10.0 (Architecture Unifiée Sprint 2)
Rôle : Définition des contrats et gestion de la traçabilité Glass Box.
Architecture : Délégation des calculs DCF au pipeline centralisé.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from src.exceptions import CalculationError
from src.domain.models import (
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

    def add_step(self, step_key: str, result: float, numerical_substitution: str,
                 label: str = "", theoretical_formula: str = "", interpretation: str = "",
                 hypotheses: Optional[List[TraceHypothesis]] = None) -> None:
        """
        Ajoute une étape de calcul à la trace Glass Box pour l'auditabilité complète.

        Cette méthode permet aux stratégies de valorisation d'enregistrer chaque étape
        intermédiaire de leur calcul, assurant une transparence totale du processus.

        Parameters
        ----------
        step_key : str
            Clé unique identifiant l'étape (doit être cohérente avec le registre Glass Box).
        result : float
            Résultat numérique de l'étape de calcul.
        numerical_substitution : str
            Substitution numérique détaillée montrant les vraies valeurs utilisées
            dans le calcul (formatées avec format_smart_number pour les montants).
        label : str, optional
            Libellé d'affichage de l'étape (par défaut step_key).
        theoretical_formula : str, optional
            Formule LaTeX théorique (provenant de StrategyFormulas).
        interpretation : str, optional
            Interprétation pédagogique de l'étape (provenant de StrategyInterpretations).
        hypotheses : Optional[List[TraceHypothesis]], optional
            Hypothèses associées à l'étape pour l'audit institutionnel.

        Notes
        -----
        Cette méthode ne fait rien si glass_box_enabled est False.
        Les étapes sont automatiquement numérotées séquentiellement.
        Utiliser exclusivement pour les étapes spécifiques à la stratégie (pas les calculs DCF standard).
        """
        if not self.glass_box_enabled:
            return

        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1,
            step_key=step_key,
            label=label or step_key,
            theoretical_formula=theoretical_formula,
            hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution,
            result=result,
            interpretation=interpretation
        ))

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
