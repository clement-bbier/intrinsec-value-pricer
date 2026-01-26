"""
Stratégie DCF Fundamental (Normalized Cash Flows).

Référence Académique : CFA Institute / Damodaran
Domaine Économique : Entreprises cycliques avec normalisation des flux
Invariants du Modèle : Utilisation de flux normalisés pour l'ancrage
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import (
    CompanyFinancials, DCFParameters, DCFValuationResult,
    TraceHypothesis, ValuationMode
)
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import SimpleFlowProjector

# Import centralisé i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    FCFF Normalisé.

    Cette stratégie utilise des flux lissés sur le cycle économique pour
    valoriser des entreprises industrielles ou cycliques.
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Cyclical / Industrial firms"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Exécute la valorisation fondamentale avec flux normalisés.
        """
        # 1. Sélection et validation du flux normalisé
        fcf_base, source = self._select_normalized_fcf(financials, params)

        if fcf_base <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FCF_NORM)

        self.add_step(
            step_key="FCF_NORM_SELECTION",
            label=RegistryTexts.DCF_FCF_NORM_L,
            theoretical_formula=StrategyFormulas.FCF_NORMALIZED,
            result=fcf_base,
            numerical_substitution=KPITexts.SUB_FCF_NORM.format(val=fcf_base, src=source),
            interpretation=StrategyInterpretations.FUND_NORM,
            source=source,
            hypotheses=[
                TraceHypothesis(
                    name=RegistryTexts.FCFF_NORM_L,
                    value=fcf_base,
                    unit=financials.currency,
                    source=source
                )
            ]
        )

        # 2. Orchestration via le Pipeline Unifié
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFF_NORMALIZED,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(base_value=fcf_base, financials=financials, params=params)

        # --- RÉSOLUTION DE L'ERREUR DE TYPAGE ---
        if not isinstance(raw_result, DCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFF_NORM_L,
                    issue=type(raw_result).__name__
                )
            )

        result: DCFValuationResult = raw_result

        # 3. Finalisation et Audit
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _select_normalized_fcf(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Sélectionne le flux normalisé (lissé) pour l'ancrage.
        """
        # Priorité 1 : Surcharge Manuelle
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Priorité 2 : Flux normalisé calculé (fcf_fundamental_smoothed)
        if financials.fcf_fundamental_smoothed is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_NORM)

        return financials.fcf_fundamental_smoothed, StrategySources.YAHOO_FUNDAMENTAL