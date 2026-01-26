"""
Stratégie Dividend Discount Model (DDM).

Référence Académique : Gordon & Shapiro
Domaine Économique : Entreprises distributives matures et utilities
Invariants du Modèle : Valorisation par valeur actuelle des dividendes futurs
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import (
    CompanyFinancials,
    DCFParameters,
    EquityDCFValuationResult,
    ValuationMode
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


class DividendDiscountStrategy(ValuationStrategy):
    """
    Stratégie DDM (Dividend Discount Model).

    Estime la valeur intrinsèque comme la valeur actuelle des dividendes futurs.
    Standard rigoureux pour les banques, assurances et utilities matures.
    """

    academic_reference = "Gordon / Shapiro"
    economic_domain = "Dividend-paying Firms / Mature Utilities"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> EquityDCFValuationResult:
        """
        Exécute la valorisation DDM via le Pipeline Unifié avec typage sécurisé.
        """
        # 1. DÉTERMINATION DU DIVIDENDE DE DÉPART (D_0)
        d0_per_share, source_div = self._resolve_dividend_base(financials, params)

        # Sécurité financière : Dividendes négatifs ou nuls en mode Auto bloqués
        if params.growth.manual_dividend_base is None and d0_per_share <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.DDM_L,
                    val=d0_per_share
                )
            )

        # Conversion en masse totale pour assurer la cohérence du Pipeline (ST-7)
        total_dividend_mass = d0_per_share * financials.shares_outstanding

        self.add_step(
            step_key="DDM_BASE_SELECTION",
            label=RegistryTexts.DDM_BASE_L,
            theoretical_formula=StrategyFormulas.DIVIDEND_BASE,
            result=total_dividend_mass,
            numerical_substitution=KPITexts.SUB_DDM_BASE.format(
                d0=d0_per_share,
                shares=financials.shares_outstanding,
                total=total_dividend_mass
            ),
            interpretation=StrategyInterpretations.DDM_LOGIC,
            source=source_div
        )

        # 2. CONFIGURATION ET EXÉCUTION DU PIPELINE (MODE DIRECT EQUITY)
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.DDM,
            glass_box_enabled=self.glass_box_enabled
        )

        raw_result = pipeline.run(
            base_value=total_dividend_mass,
            financials=financials,
            params=params
        )

        # --- RÉSOLUTION DE L'ERREUR DE TYPAGE (DOWNCASTING) ---
        if not isinstance(raw_result, EquityDCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.DDM_L,
                    issue=type(raw_result).__name__
                )
            )

        result: EquityDCFValuationResult = raw_result

        # 3. FINALISATION ET AUDIT
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _resolve_dividend_base(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, str]:
        """
        Détermine le dividende par action de référence (D0).
        """
        g = params.growth

        # A. Surcharge Expert
        if g.manual_dividend_base is not None:
            return g.manual_dividend_base, StrategySources.MANUAL_OVERRIDE

        # B. Donnée extraite de Yahoo (TTM)
        if financials.dividend_share is not None and financials.dividend_share > 0:
            return financials.dividend_share, StrategySources.YAHOO_TTM_SIMPLE

        # C. Fallback i18n
        return 0.0, StrategySources.CALCULATED