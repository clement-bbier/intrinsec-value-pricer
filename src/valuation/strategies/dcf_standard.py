"""
Stratégie DCF Standard (Free Cash Flow to Firm).

Référence Académique : Damodaran (Investment Valuation)
Domaine Économique : Entreprises matures avec flux stables
Invariants du Modèle : Projection two-stage avec terminal value
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters, DCFValuationResult, ValuationMode
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import SimpleFlowProjector

# Import centralisé i18n (Zéro texte brut autorisé)
from src.i18n import (
    RegistryTexts,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts, DiagnosticTexts
)

logger = logging.getLogger(__name__)


class StandardFCFFStrategy(ValuationStrategy):
    """
    FCFF Standard (Damodaran).

    Cette stratégie délègue le calcul lourd au pipeline unifié après avoir
    ancré le flux de trésorerie disponible (FCF) de départ.
    """

    academic_reference = "Damodaran"
    economic_domain = "Mature firms / Stable cash-flows"

    def execute(
            self,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> DCFValuationResult:
        """
        Exécute la stratégie DCF Standard avec validation stricte du contrat de type.
        """
        # 1. Sélection du flux de base
        fcf_base, source = self._select_base_fcf(financials, params)

        if params.growth.manual_fcf_base is None and fcf_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFF_STANDARD_L,
                    val=fcf_base
                )
            )

        self.add_step(
            step_key="FCF_BASE_SELECTION",
            label=RegistryTexts.DCF_FCF_BASE_L,
            theoretical_formula=StrategyFormulas.FCF_BASE,
            result=fcf_base,
            numerical_substitution=KPITexts.SUB_FCF_BASE.format(val=fcf_base, src=source),
            interpretation=RegistryTexts.DCF_FCF_BASE_D,
            source=source
        )

        # 2. Orchestration via le Pipeline
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFF_STANDARD,
            glass_box_enabled=self.glass_box_enabled
        )

        # Le pipeline retourne un ValuationResult (base)
        raw_result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # --- RÉSOLUTION DE L'ERREUR DE TYPAGE ---
        if not isinstance(raw_result, DCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFF_STANDARD_L,
                    issue=type(raw_result).__name__
                )
            )

        # Ici, l'IDE sait que 'result' est un DCFValuationResult
        result: DCFValuationResult = raw_result

        # 3. Finalisation et Audit
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _select_base_fcf(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Identifie le point d'ancrage FCF selon la hiérarchie de souveraineté.

        Parameters
        ----------
        financials : CompanyFinancials
            Données TTM.
        params : DCFParameters
            Surcharges analystes éventuelles.

        Returns
        -------
        Tuple[float, str]
            Valeur du flux et libellé i18n de la source.
        """
        # Priorité 1 : Surcharge Manuelle (Analyste)
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Priorité 2 : Flux TTM reporté (Deep Fetch)
        if financials.fcf_last is not None:
            return financials.fcf_last, StrategySources.YAHOO_TTM

        # Cas critique : Absence de données
        raise CalculationError(CalculationErrors.MISSING_FCF_STD)