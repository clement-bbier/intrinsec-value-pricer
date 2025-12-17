"""
core/valuation/strategies/graham_value.py

Méthode : Graham Intrinsic Value (1974 Revised)
Version : V1 Normative

Référence académique :
- Graham, B. – The Intelligent Investor (1974, revised)

Principe :
- Méthode heuristique de valorisation
- Basée sur le bénéfice, la croissance attendue et le niveau des taux
- Non fondée sur l’actualisation des cash-flows

⚠️ Ce n’est PAS un DCF
⚠️ Méthode indicative, à usage comparatif
"""

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, GrahamValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.computation.financial_math import calculate_graham_1974_value

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    Graham Intrinsic Value — Formule révisée 1974.

    Référence académique :
    - Benjamin Graham

    Domaine de validité :
    - Entreprises value / matures
    - Earnings positifs et relativement stables

    Invariants financiers :
    - EPS > 0
    - Yield AAA > 0
    - Croissance modérée (raisonnable)
    """

    academic_reference = "Graham (1974)"
    economic_domain = "Value / Deep Value (Mature firms)"
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
        """
        Exécute la formule de Graham 1974 révisée.

        Formule :
        V = [EPS × (8.5 + 2g) × 4.4] / Y_AAA
        """

        logger.info(
            "[Strategy] Graham 1974 Revised | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. EPS (ANCRAGE BÉNÉFICIAIRE)
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

        if eps is None or eps <= 0:
            raise CalculationError(
                "EPS positif requis pour la méthode Graham."
            )

        self.add_step(
            "Bénéfice par Action (EPS)",
            "EPS",
            f"{eps:.2f}",
            eps,
            financials.currency,
            "Capacité bénéficiaire de référence."
        )

        # ====================================================
        # 2. TAUX DE RÉFÉRENCE (AAA)
        # ====================================================

        aaa_yield = params.corporate_aaa_yield

        if aaa_yield is None or aaa_yield <= 0:
            raise CalculationError(
                "Rendement obligataire AAA requis."
            )

        self.add_step(
            "Rendement Obligataire AAA",
            "Y_AAA",
            f"{aaa_yield:.2%}",
            aaa_yield,
            "%",
            "Taux d’actualisation implicite (coût d’opportunité)."
        )

        # ====================================================
        # 3. CROISSANCE (HEURISTIQUE)
        # ====================================================

        growth_rate = params.fcf_growth_rate

        if growth_rate < 0:
            logger.warning(
                "[Graham] Croissance négative utilisée : %.2f%%",
                growth_rate * 100
            )

        # ====================================================
        # 4. CALCUL GRAHAM (FORMULE RÉVISÉE)
        # ====================================================

        try:
            intrinsic_value = calculate_graham_1974_value(
                eps=eps,
                growth_rate=growth_rate,
                aaa_yield=aaa_yield
            )
        except Exception as e:
            raise CalculationError(
                f"Erreur dans la formule Graham : {e}"
            )

        growth_multiplier = 8.5 + 2.0 * (growth_rate * 100.0)
        rate_adjustment = 4.4 / (aaa_yield * 100.0)

        self.add_step(
            "Multiplicateur de Croissance",
            "8.5 + 2g",
            f"8.5 + 2×{growth_rate * 100:.1f}",
            growth_multiplier,
            "x",
            "Ajustement du P/E selon la croissance."
        )

        self.add_step(
            "Ajustement aux Taux",
            "4.4 / Y_AAA",
            f"4.4 / {aaa_yield * 100:.2f}",
            rate_adjustment,
            "facteur",
            "Ajustement relatif aux taux historiques."
        )

        self.add_step(
            "Valeur Intrinsèque (Graham 1974)",
            "EPS × (8.5 + 2g) × (4.4 / Y)",
            (
                f"{eps:.2f} × "
                f"{growth_multiplier:.2f} × "
                f"{rate_adjustment:.2f}"
            ),
            intrinsic_value,
            financials.currency,
            "Estimation heuristique de la valeur."
        )

        # ====================================================
        # 5. RÉSULTAT FINAL
        # ====================================================

        return GrahamValuationResult(
            request=None,  # injecté par le moteur
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            eps_used=eps,
            growth_rate_used=growth_rate,
            aaa_yield_used=aaa_yield,
            calculation_trace=self.trace
        )
