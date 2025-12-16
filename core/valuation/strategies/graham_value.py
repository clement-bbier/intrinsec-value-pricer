import logging
from core.models import CompanyFinancials, DCFParameters, GrahamValuationResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError
from core.computation.financial_math import calculate_graham_1974_value

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    STRATÉGIE 6 : BENJAMIN GRAHAM INTRINSIC VALUE (1974 Revised).

    Remplace l'ancienne formule 'Graham Number' (Sqrt(22.5 * EPS * BV)).
    Nouvelle Formule : V = (EPS * (8.5 + 2g) * 4.4) / Y_aaa

    Cette approche prend en compte :
    - La croissance attendue (g)
    - Le contexte de taux d'intérêt actuel (Y_aaa)
    """

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> GrahamValuationResult:
        logger.info("[Strategy] Executing Graham 1974 Revised Strategy")

        # 1. Préparation des Inputs
        eps = financials.eps_ttm
        # Fallback si EPS non fourni mais Net Income dispo
        if (eps is None or eps == 0) and financials.net_income_ttm and financials.shares_outstanding:
            eps = financials.net_income_ttm / financials.shares_outstanding

        # Override manuel EPS
        if params.manual_fcf_base:
            eps = params.manual_fcf_base

        if eps is None:
            raise CalculationError("Donnée manquante : EPS (Bénéfice par action) requis.")

        # Le taux corporate AAA est fourni par le provider macro (injecté dans params)
        aaa_yield = params.corporate_aaa_yield
        if aaa_yield is None or aaa_yield <= 0:
            # Fallback de sécurité (ex: 4.5%)
            aaa_yield = 0.045
            logger.warning("Yield AAA manquant, utilisation fallback 4.5%")

        # Croissance : On utilise la croissance FCF comme proxy de la croissance Earnings
        g_rate = params.fcf_growth_rate

        # 2. Trace : Inputs
        self.add_step(
            "Bénéfice par Action (EPS)",
            "EPS_{ttm}",
            f"{eps:.2f}",
            eps,
            financials.currency,
            "Capacité bénéficiaire actuelle."
        )

        self.add_step(
            "Taux Obligataire de Référence (AAA)",
            "Y_{AAA}",
            f"{aaa_yield:.2%}",
            aaa_yield,
            "%",
            "Rendement actuel des obligations d'entreprise haute qualité (Coût d'opportunité)."
        )

        # 3. Calcul (via financial_math pour garantir la rigueur)
        try:
            intrinsic_value = calculate_graham_1974_value(
                eps=eps,
                growth_rate=g_rate,
                aaa_yield=aaa_yield
            )
        except Exception as e:
            raise CalculationError(f"Erreur mathématique Graham : {e}")

        # 4. Trace : Formule
        # Formule : V = EPS * (8.5 + 2g) * (4.4 / Y)
        pe_base = 8.5
        growth_multiplier = 8.5 + 2.0 * (g_rate * 100.0)
        rate_adjustment = 4.4 / (aaa_yield * 100.0)

        self.add_step(
            "Multiplicateur de Croissance",
            "8.5 + 2g",
            f"8.5 + 2*({g_rate * 100:.1f})",
            growth_multiplier,
            "x",
            "P/E ajusté pour la croissance (modèle Graham)."
        )

        self.add_step(
            "Ajustement aux Taux",
            "4.4 / Y_{AAA}",
            f"4.4 / {aaa_yield * 100:.2f}",
            rate_adjustment,
            "facteur",
            "Ajustement relatif aux taux historiques (4.4% époque Graham)."
        )

        self.add_step(
            "Valeur Intrinsèque (Graham 1974)",
            "EPS \\times (8.5 + 2g) \\times \\frac{4.4}{Y}",
            f"{eps:.2f} x {growth_multiplier:.2f} x {rate_adjustment:.2f}",
            intrinsic_value,
            financials.currency,
            "Valeur théorique selon la formule révisée."
        )

        # 5. Retour Résultat
        return GrahamValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            eps_used=eps,
            growth_rate_used=g_rate,
            aaa_yield_used=aaa_yield,
            calculation_trace=self.trace
        )