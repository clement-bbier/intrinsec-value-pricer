"""
core/valuation/strategies/dcf_fundamental.py

MÉTHODE : FCFF NORMALIZED — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Normalisation des flux cycliques et délégation au pipeline DCF.
Architecture : Audit-Grade avec alignement intégral sur le registre Glass Box.
"""

from __future__ import annotations

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult, TraceHypothesis
from core.valuation.strategies.abstract import ValuationStrategy

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    FCFF Normalisé (Cyclical / Fundamental).
    Utilise des flux lissés pour neutraliser la volatilité des cycles.
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Cyclical / Industrial firms"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """Exécute la stratégie via le segment 'growth'."""
        logger.info("[Strategy] FCFF Normalized | ticker=%s", financials.ticker)

        # =====================================================================
        # 1. SÉLECTION DU FCF NORMALISÉ
        # =====================================================================
        fcf_base, source = self._select_normalized_fcf(financials, params)

        # CORRECTION i18n : Utilisation de SUB_FCF_NORM
        self.add_step(
            step_key="FCF_NORM_SELECTION",
            label=RegistryTexts.DCF_FCF_NORM_L,
            theoretical_formula=r"FCF_{norm}",
            result=fcf_base,
            numerical_substitution=KPITexts.SUB_FCF_NORM.format(val=fcf_base, src=source),
            interpretation=StrategyInterpretations.FUND_NORM,
            hypotheses=[
                TraceHypothesis(
                    name="Normalized FCF",
                    value=fcf_base,
                    unit=financials.currency,
                    source=source
                )
            ]
        )

        # =====================================================================
        # 2. CONTRÔLE DE VIABILITÉ DU MODÈLE
        # =====================================================================
        self._validate_fcf_positivity(fcf_base)

        self.add_step(
            step_key="FCF_STABILITY_CHECK",
            label=RegistryTexts.DCF_STABILITY_L,
            theoretical_formula=r"FCF_{norm} > 0",
            result=1.0,
            numerical_substitution=f"{fcf_base:,.2f} > 0",
            interpretation=StrategyInterpretations.FUND_VIABILITY
        )

        # =====================================================================
        # 3. EXÉCUTION DU DCF MATH (V9 Segmented)
        # =====================================================================
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )

    def _select_normalized_fcf(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """Sélection via le segment growth."""
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.fcf_fundamental_smoothed is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_NORM)

        return financials.fcf_fundamental_smoothed, StrategySources.YAHOO_FUNDAMENTAL

    def _validate_fcf_positivity(self, fcf_base: float) -> None:
        """Lève une exception i18n si le flux est négatif."""
        if fcf_base <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FCF_NORM)