"""
Stratégie DCF Growth (Revenue-Driven).

Référence Académique : Damodaran / McKinsey
Domaine Économique : Entreprises en croissance avec convergence de marges
Invariants du Modèle : Projection avec fade-down linéaire des marges
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters, DCFValuationResult, ValuationMode
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import MarginConvergenceProjector

# Import centralisé i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    KPITexts,
    StrategySources,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class RevenueBasedStrategy(ValuationStrategy):
    """
    Revenue-Driven DCF (Modèle de convergence).

    Cette stratégie injecte le moteur de convergence des marges dans le pipeline,
    permettant de valoriser des entreprises dont les marges actuelles ne sont
    pas encore représentatives de leur état normatif futur.
    """

    academic_reference = "Damodaran / McKinsey"
    economic_domain = "Growth firms / Revenue-driven"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Exécute la valorisation par croissance des revenus avec downcast sécurisé.

        Parameters
        ----------
        financials : CompanyFinancials
            Données financières historiques (Revenus TTM).
        params : DCFParameters
            Paramètres de croissance et cibles de marges.

        Returns
        -------
        DCFValuationResult
            Résultat riche incluant la trace Glass Box.
        """
        # 1. Ancrage revenu et identification de la source
        rev_base, source_rev = self._select_revenue_base(financials, params)

        # Sécurité financière : Blocage des revenus négatifs en mode Auto
        if params.growth.manual_fcf_base is None and rev_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFF_GROWTH_L,
                    val=rev_base
                )
            )

        self.add_step(
            step_key="GROWTH_REV_BASE",
            label=RegistryTexts.GROWTH_REV_BASE_L,
            theoretical_formula=StrategyFormulas.REVENUE_BASE,
            result=rev_base,
            numerical_substitution=KPITexts.SUB_REV_BASE.format(val=rev_base),
            interpretation=StrategyInterpretations.GROWTH_REV,
            source=source_rev # Ajout de la source pour l'UI
        )

        # 2. Orchestration via le Pipeline Unifié (Projecteur spécifique Growth)
        pipeline = DCFCalculationPipeline(
            projector=MarginConvergenceProjector(),
            mode=ValuationMode.FCFF_GROWTH,
            glass_box_enabled=self.glass_box_enabled
        )

        # Le pipeline retourne un ValuationResult générique
        raw_result = pipeline.run(base_value=rev_base, financials=financials, params=params)

        # --- RÉSOLUTION DE L'ERREUR DE TYPAGE (DOWNCASTING) ---
        if not isinstance(raw_result, DCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFF_GROWTH_L,
                    issue=type(raw_result).__name__
                )
            )

        # Cast explicite pour satisfaire l'IDE (PyCharm)
        result: DCFValuationResult = raw_result

        # 3. Finalisation, Audit et Contrat
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _select_revenue_base(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Détermine le point d'ancrage du Chiffre d'Affaires.
        """
        # Priorité 1 : Surcharge Manuelle via segment growth
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Priorité 2 : Revenus TTM reportés
        if financials.revenue_ttm is None or financials.revenue_ttm <= 0:
            raise CalculationError(CalculationErrors.MISSING_REV)

        return financials.revenue_ttm, StrategySources.YAHOO_TTM_SIMPLE