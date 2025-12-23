"""
core/valuation/strategies/graham_value.py

Méthode : Graham Intrinsic Value (1974 Revised)
Version : V1.3 — Pydantic Fix (Arguments nommés stricts)
"""

import logging

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    GrahamValuationResult,
    TraceHypothesis
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.computation.financial_math import calculate_graham_1974_value

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    Graham Intrinsic Value — Formule révisée 1974.
    """

    academic_reference = "Graham (1974)"
    economic_domain = "Value / Mature firms"
    financial_invariants = [
        "EPS > 0",
        "AAA_yield > 0",
        "growth_rate reasonable"
    ]

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> GrahamValuationResult:

        logger.info(
            "[Strategy] Graham 1974 Revised | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. EPS — ANCRAGE BÉNÉFICIAIRE
        # ====================================================

        eps = financials.eps_ttm

        if (eps is None or eps <= 0) and financials.net_income_ttm:
            if financials.shares_outstanding <= 0:
                raise CalculationError("Nombre d’actions invalide.")
            eps = (
                financials.net_income_ttm
                / financials.shares_outstanding
            )

        # Override manuel (expert)
        if params.manual_fcf_base is not None:
            eps = params.manual_fcf_base
            eps_source = "Manual override"
        else:
            eps_source = "Reported EPS / Derived EPS"

        if eps is None or eps <= 0:
            raise CalculationError(
                "EPS strictement positif requis pour la méthode Graham."
            )

        self.add_step(
            label="Bénéfice par action (EPS)",
            theoretical_formula="EPS",
            hypotheses=[
                TraceHypothesis(
                    name="EPS",
                    value=eps,
                    unit=financials.currency,
                    source=eps_source
                )
            ],
            numerical_substitution=f"EPS = {eps:.2f}",
            result=eps,
            unit=financials.currency,
            interpretation=(
                "Capacité bénéficiaire utilisée comme ancrage "
                "de la valorisation heuristique."
            )
        )

        # ====================================================
        # 2. TAUX DE RÉFÉRENCE — AAA
        # ====================================================

        aaa_yield = params.corporate_aaa_yield

        if aaa_yield is None or aaa_yield <= 0:
            raise CalculationError(
                "Rendement obligataire AAA requis pour la méthode Graham."
            )

        self.add_step(
            label="Rendement obligataire AAA",
            theoretical_formula="Y_AAA",
            hypotheses=[
                TraceHypothesis(
                    name="AAA yield",
                    value=aaa_yield,
                    unit="%",
                    source="Corporate bond market"
                )
            ],
            numerical_substitution=f"Y_AAA = {aaa_yield:.2%}",
            result=aaa_yield,
            unit="%",
            interpretation=(
                "Taux de référence servant d’ajustement macro-financier "
                "dans la formule de Graham."
            )
        )

        # ====================================================
        # 3. CROISSANCE — HYPOTHÈSE HEURISTIQUE
        # ====================================================

        growth_rate = params.fcf_growth_rate

        self.add_step(
            label="Hypothèse de croissance",
            theoretical_formula="g",
            hypotheses=[
                TraceHypothesis(
                    name="Growth rate",
                    value=growth_rate,
                    unit="%",
                    source="User input / Analyst assumption"
                )
            ],
            numerical_substitution=f"g = {growth_rate:.2%}",
            result=growth_rate,
            unit="%",
            interpretation=(
                "Hypothèse de croissance utilisée de manière heuristique "
                "dans la formule de Graham."
            )
        )

        # ====================================================
        # 4. COMPOSANTS DU MULTIPLICATEUR
        # ====================================================

        # NOTE : On multiplie par 100 ICI uniquement pour l'affichage de la trace.
        # Le calcul réel est délégué à financial_math.py qui gère sa propre conversion.
        g_for_display = growth_rate * 100.0
        y_for_display = aaa_yield * 100.0

        growth_multiplier = 8.5 + 2.0 * g_for_display
        rate_adjustment = 4.4 / y_for_display

        self.add_step(
            label="Multiplicateur de croissance",
            theoretical_formula="8.5 + 2g",
            hypotheses=[
                TraceHypothesis(
                    name="Growth rate (scaled)",
                    value=g_for_display,
                    unit="number"
                )
            ],
            numerical_substitution=f"8.5 + 2×{g_for_display:.2f}",
            result=growth_multiplier,
            unit="x",
            interpretation=(
                "Ajustement du multiple de bénéfice en fonction "
                "de la croissance attendue."
            )
        )

        self.add_step(
            label="Ajustement aux taux",
            theoretical_formula="4.4 / Y_AAA",
            hypotheses=[
                TraceHypothesis(
                    name="AAA yield (scaled)",
                    value=y_for_display,
                    unit="number"
                )
            ],
            numerical_substitution=f"4.4 / {y_for_display:.2f}",
            result=rate_adjustment,
            unit="factor",
            interpretation=(
                "Ajustement relatif aux conditions de taux d’intérêt "
                "historiques."
            )
        )

        # ====================================================
        # 5. VALEUR INTRINSÈQUE (GRAHAM)
        # ====================================================

        try:
            # Appel au moteur mathématique nettoyé (qui attend des décimales)
            intrinsic_value = calculate_graham_1974_value(
                eps=eps,
                growth_rate=growth_rate, # ex: 0.05
                aaa_yield=aaa_yield      # ex: 0.045
            )
        except Exception as e:
            raise CalculationError(
                f"Erreur dans la formule Graham : {e}"
            )

        # [CORRECTIF V1.3] Utilisation stricte des arguments nommés (name=, value=)
        self.add_step(
            label="Valeur intrinsèque (Graham 1974)",
            theoretical_formula="EPS × (8.5 + 2g) × (4.4 / Y)",
            hypotheses=[
                TraceHypothesis(name="EPS", value=eps, unit=financials.currency),
                TraceHypothesis(name="Growth multiplier", value=growth_multiplier, unit="x"),
                TraceHypothesis(name="Rate adjustment", value=rate_adjustment, unit="factor")
            ],
            numerical_substitution=(
                f"{eps:.2f} × {growth_multiplier:.2f} × {rate_adjustment:.2f}"
            ),
            result=intrinsic_value,
            unit=financials.currency,
            interpretation=(
                "Estimation heuristique de la valeur intrinsèque "
                "selon la formule révisée de Graham (1974)."
            )
        )

        return GrahamValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            eps_used=eps,
            growth_rate_used=growth_rate,
            aaa_yield_used=aaa_yield,
            calculation_trace=self.calculation_trace
        )