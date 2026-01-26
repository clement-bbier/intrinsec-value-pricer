"""
Stratégie Graham Intrinsic Value.

Référence Académique : Benjamin Graham (1974 Revised)
Domaine Économique : Value investing et entreprises défensives
Invariants du Modèle : Multiplicateur de croissance plafonné avec rendement AAA
"""

from __future__ import annotations

import logging
from typing import Tuple, Dict, Optional

from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters, GrahamValuationResult
from src.valuation.strategies.abstract import ValuationStrategy

# Import depuis core.i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    Estimation 'Value' basée sur la formule révisée de Benjamin Graham (1974).

    Formule théorique :
    $$IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}$$
    """

    academic_reference = "Benjamin Graham (1974)"
    economic_domain = "Value Investing / Defensive"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> GrahamValuationResult:
        """
        Exécute la séquence de valorisation Graham.

        Parameters
        ----------
        financials : CompanyFinancials
            Données financières de l'entreprise (EPS, prix, etc.).
        params : DCFParameters
            Paramètres de croissance et taux (g, rendement AAA).

        Returns
        -------
        GrahamValuationResult
            Résultat complet incluant la trace Glass Box pour l'audit.
        """
        r = params.rates
        g = params.growth

        # 1. Sélection de la base de profitabilité (EPS)
        eps, source_eps = self._select_eps(financials, params)

        self.add_step(
            step_key="GRAHAM_EPS_BASE",
            label=RegistryTexts.GRAHAM_EPS_L,
            theoretical_formula=StrategyFormulas.EPS_BASE,
            result=eps,
            numerical_substitution=KPITexts.SUB_EPS_GRAHAM.format(val=eps, src=source_eps),
            interpretation=StrategyInterpretations.GRAHAM_EPS,
            source=source_eps
        )

        # 2. Calcul du multiplicateur de croissance
        growth_rate = g.fcf_growth_rate or 0.0
        growth_multiplier = self._compute_growth_multiplier(growth_rate)

        self.add_step(
            step_key="GRAHAM_MULTIPLIER",
            label=RegistryTexts.GRAHAM_MULT_L,
            theoretical_formula=StrategyFormulas.GRAHAM_MULTIPLIER,
            result=growth_multiplier,
            numerical_substitution=KPITexts.SUB_GRAHAM_MULT.format(g=growth_rate * 100.0),
            interpretation=StrategyInterpretations.GRAHAM_MULT,
            source=StrategySources.ANALYST_OVERRIDE
        )

        # 3. Calcul de la valeur intrinsèque finale (ajustée AAA)
        aaa_yield = r.corporate_aaa_yield or 0.044
        self._validate_aaa_yield(aaa_yield)

        intrinsic_value = self._compute_intrinsic_value(eps, growth_multiplier, aaa_yield)

        self.add_step(
            step_key="GRAHAM_FINAL",
            label=RegistryTexts.GRAHAM_IV_L,
            theoretical_formula=StrategyFormulas.GRAHAM_VALUE,
            result=intrinsic_value,
            numerical_substitution=f"({eps:.2f} \times {growth_multiplier:.2f} \times 4.4) / {aaa_yield * 100.0:.2f}",
            interpretation=StrategyInterpretations.GRAHAM_IV,
            source=StrategySources.MACRO_MATRIX.format(ticker="AAA Corporate Yield")
        )

        # 4. Génération du résultat et Audit
        audit_metrics = self._compute_graham_audit_metrics(financials, eps)

        result = GrahamValuationResult(
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

        self.generate_audit_report(result)
        self.verify_output_contract(result)
        return result

    @staticmethod
    def _select_eps(financials: CompanyFinancials, params: DCFParameters) -> Tuple[float, str]:
        """Sélectionne l'EPS de référence selon la hiérarchie de souveraineté."""
        if params.growth.manual_fcf_base is not None:
            return params.growth.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.eps_ttm is not None and financials.eps_ttm > 0:
            return financials.eps_ttm, StrategySources.YAHOO_TTM_SIMPLE

        if financials.net_income_ttm and financials.shares_outstanding > 0:
            eps_calc = financials.net_income_ttm / financials.shares_outstanding
            if eps_calc > 0:
                return eps_calc, StrategySources.CALCULATED_NI

        raise CalculationError(CalculationErrors.MISSING_EPS_GRAHAM)

    @staticmethod
    def _compute_growth_multiplier(growth_rate: float) -> float:
        """Calcule le multiplicateur M = 8.5 + 2g."""
        return 8.5 + 2.0 * (growth_rate * 100.0)

    @staticmethod
    def _validate_aaa_yield(aaa_yield: float) -> None:
        """Valide que le rendement AAA est strictement positif."""
        if aaa_yield is None or aaa_yield <= 0:
            raise CalculationError(CalculationErrors.INVALID_AAA)

    @staticmethod
    def _compute_intrinsic_value(eps: float, multiplier: float, aaa_yield: float) -> float:
        """Applique la formule finale de Graham."""
        return (eps * multiplier * 4.4) / (aaa_yield * 100.0)

    @staticmethod
    def _compute_graham_audit_metrics(financials: CompanyFinancials, eps: float) -> Dict[str, Optional[float]]:
        """Calcule les ratios d'audit pour le score de fiabilité."""
        pe = financials.current_price / eps if eps > 0 else None
        payout = None
        if financials.net_income_ttm and financials.net_income_ttm > 0:
            payout = financials.dividends_total_calculated / financials.net_income_ttm

        return {"pe": pe, "payout": payout}