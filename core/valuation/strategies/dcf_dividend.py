"""
core/valuation/strategies/dcf_dividend.py
MÉTHODE : DIVIDEND DISCOUNT MODEL (DDM) — VERSION V10.0
Rôle : Valorisation actionnariale basée sur la distribution future des dividendes.
Architecture : Audit-Grade s'appuyant sur le Pipeline Unifié (Sprint 3).
Source : CFA Institute / Gordon & Shapiro.
"""

from __future__ import annotations
import logging

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    EquityDCFValuationResult,
    ValuationMode
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.pipelines import DCFCalculationPipeline
from core.computation.growth import SimpleFlowProjector

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class DividendDiscountStrategy(ValuationStrategy):
    """
    Stratégie DDM (Dividend Discount Model).
    Estime la valeur d'une action comme la valeur actuelle de tous les futurs
    dividendes distribués, actualisés au coût des fonds propres (Ke).
    """

    academic_reference = "Myron J. Gordon / Shapiro"
    economic_domain = "Dividend-paying Firms / Mature Utilities"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> EquityDCFValuationResult:
        """Exécute la valorisation DDM via le Pipeline Unifié."""
        logger.info("[Strategy] Dividend Discount Model | ticker=%s", financials.ticker)

        # =====================================================================
        # 1. DÉTERMINATION DU DIVIDENDE DE DÉPART (D_0)
        # =====================================================================
        d0_base, source = self._resolve_dividend_base(financials, params)

        # Validation de rigueur pour le DDM
        if d0_base <= 0:
            raise CalculationError(CalculationErrors.INVALID_DIVIDEND)

        self.add_step(
            step_key="DDM_BASE_SELECTION",
            label=RegistryTexts.DDM_BASE_L,
            theoretical_formula=r"D_0",
            result=d0_base,
            numerical_substitution=KPITexts.SUB_DDM_BASE.format(val=d0_base),
            interpretation=StrategyInterpretations.DDM_LOGIC
        )

        # =====================================================================
        # 2. CONFIGURATION ET EXÉCUTION DU PIPELINE (MODE DIRECT EQUITY)
        # =====================================================================
        # Rigueur : On passe ValuationMode.DDM_GORDON_GROWTH pour forcer Ke
        # et s'assurer qu'aucun bridge de dette n'est appliqué.
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.DDM_GORDON_GROWTH,
            glass_box_enabled=self.glass_box_enabled
        )

        # Le pipeline retourne un EquityDCFValuationResult (Contrat Sprint 3)
        result = pipeline.run(
            base_value=d0_base,
            financials=financials,
            params=params
        )

        # =====================================================================
        # 3. FINALISATION
        # =====================================================================
        self._merge_traces(result)

        return result

    def _resolve_dividend_base(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """
        Détermine le dividende par action de référence.
        Priorité : Surcharge manuelle > Donnée Yahoo (TTM).
        """
        g = params.growth

        # A. Surcharge Expert (manual_dividend_base ajouté en Phase 1)
        if g.manual_dividend_base is not None:
            return g.manual_dividend_base, StrategySources.MANUAL_OVERRIDE

        # B. Donnée extraite
        if financials.dividend_share is not None and financials.dividend_share > 0:
            return financials.dividend_share, StrategySources.YAHOO_TTM_SIMPLE

        # C. Cas critique : Pas de dividende
        return 0.0, "N/A"