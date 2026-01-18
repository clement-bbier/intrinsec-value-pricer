"""
core/valuation/strategies/graham_value.py

MÉTHODE : GRAHAM INTRINSIC VALUE — VERSION V9.0 (Segmenté & i18n Secured)
Rôle : Estimation "Value" (1974 Revised) avec transparence totale.
Architecture : Audit-Grade utilisant les segments Rates & Growth.
"""

from __future__ import annotations

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, GrahamValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

# DT-001/002: Import depuis core.i18n
from core.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    Estimation 'Value' (Graham 1974 Revised).
    Formule : IV = (EPS × (8.5 + 2g) × 4.4) / Y
    """

    academic_reference = "Benjamin Graham (1974)"
    economic_domain = "Value Investing / Defensive"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> GrahamValuationResult:
        """Exécute la stratégie via les segments Rates et Growth."""

        r = params.rates
        g = params.growth

        # =====================================================================
        # 1. ANCRAGE CAPACITÉ BÉNÉFICIAIRE
        # =====================================================================
        eps, source_eps = self._select_eps(financials, params)

        # CORRECTION i18n : Utilisation de SUB_EPS_GRAHAM
        self.add_step(
            step_key="GRAHAM_EPS_BASE",
            label=RegistryTexts.GRAHAM_EPS_L,
            theoretical_formula=r"EPS",
            result=eps,
            numerical_substitution=KPITexts.SUB_EPS_GRAHAM.format(val=eps, src=source_eps),
            interpretation=StrategyInterpretations.GRAHAM_EPS
        )

        # =====================================================================
        # 2. MULTIPLICATEUR DE CROISSANCE (Via segment growth)
        # =====================================================================
        growth_rate = g.fcf_growth_rate or 0.0
        growth_multiplier = self._compute_growth_multiplier(growth_rate)
        g_display = growth_rate * 100.0

        # CORRECTION i18n : Utilisation de SUB_GRAHAM_MULT
        self.add_step(
            step_key="GRAHAM_MULTIPLIER",
            label=RegistryTexts.GRAHAM_MULT_L,
            theoretical_formula=r"M = 8.5 + 2g",
            result=growth_multiplier,
            numerical_substitution=KPITexts.SUB_GRAHAM_MULT.format(g=g_display),
            interpretation=StrategyInterpretations.GRAHAM_MULT
        )

        # =====================================================================
        # 3. VALEUR INTRINSÈQUE FINALE (Via segment rates)
        # =====================================================================
        aaa_yield = r.corporate_aaa_yield or 0.044
        self._validate_aaa_yield(aaa_yield)

        intrinsic_value = self._compute_intrinsic_value(eps, growth_multiplier, aaa_yield)
        y_display = aaa_yield * 100.0

        self.add_step(
            step_key="GRAHAM_FINAL",
            label=RegistryTexts.GRAHAM_IV_L,
            theoretical_formula=r"IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}",
            result=intrinsic_value,
            numerical_substitution=f"({eps:.2f} × {growth_multiplier:.2f} × 4.4) / {y_display:.2f}",
            interpretation=StrategyInterpretations.GRAHAM_IV
        )

        # =====================================================================
        # 4. MÉTRIQUES D'AUDIT
        # =====================================================================
        audit_metrics = self._compute_graham_audit_metrics(financials, eps)

        return GrahamValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            eps_used=eps,
            growth_rate_used=growth_rate,
            aaa_yield_used=aaa_yield,
            calculation_trace=self.calculation_trace,
            pe_observed=audit_metrics["pe"],
            graham_multiplier=growth_multiplier,
            payout_ratio_observed=audit_metrics["payout"]
        )

    def _select_eps(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """Souveraineté via segment growth."""
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.eps_ttm is not None and financials.eps_ttm > 0:
            return financials.eps_ttm, StrategySources.YAHOO_TTM_SIMPLE

        if financials.net_income_ttm and financials.shares_outstanding > 0:
            eps_calc = financials.net_income_ttm / financials.shares_outstanding
            if eps_calc > 0: return eps_calc, StrategySources.CALCULATED_NI

        raise CalculationError(CalculationErrors.MISSING_EPS_GRAHAM)

    def _compute_growth_multiplier(self, growth_rate: float) -> float:
        return 8.5 + 2.0 * (growth_rate * 100.0)

    def _validate_aaa_yield(self, aaa_yield: float) -> None:
        if aaa_yield is None or aaa_yield <= 0:
            raise CalculationError(CalculationErrors.INVALID_AAA)

    def _compute_intrinsic_value(self, eps: float, multiplier: float, aaa_yield: float) -> float:
        return (eps * multiplier * 4.4) / (aaa_yield * 100.0)

    def _compute_graham_audit_metrics(self, financials: CompanyFinancials, eps: float) -> dict:
        pe = financials.current_price / eps if eps > 0 else None
        payout = financials.dividends_total_calculated / financials.net_income_ttm if financials.net_income_ttm and financials.net_income_ttm > 0 else None
        return {"pe": pe, "payout": payout}