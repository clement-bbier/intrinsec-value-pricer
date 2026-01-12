"""
core/valuation/strategies/rim_banks.py

MÉTHODE : RESIDUAL INCOME MODEL (RIM) — VERSION V8.2
Rôle : Valorisation des institutions financières via les profits résiduels.
Architecture :  Registry-Driven avec alignement numérique intégral (Penman/Ohlson).
"""

from __future__ import annotations

import logging
from typing import List

from core.computation.financial_math import (
    calculate_cost_of_equity_capm,
    calculate_discount_factors,
    calculate_npv,
    calculate_rim_vectors,
)
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, RIMValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class RIMBankingStrategy(ValuationStrategy):
    """
    Residual Income Model (Penman/Ohlson) pour institutions financières.

    Adapté aux banques et assurances où le DCF classique est inadapté.
    Formule : IV = BV₀ + Σ PV(RI) + PV(TV)
    """

    academic_reference = "Penman / Ohlson"
    economic_domain = "Banks / Insurance / Financials"
    financial_invariants = [
        "book_value > 0",
        "eps > 0",
        "cost_of_equity > 0"
    ]

    def execute(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters
    ) -> RIMValuationResult:
        """
        Exécute la stratégie Residual Income Model.

        Args:
            financials: Données financières de l'entreprise
            params:  Paramètres de valorisation

        Returns:
            Résultat RIM complet avec métriques d'audit
        """
        logger.info("[Strategy] Residual Income Model | ticker=%s", financials.ticker)

        # =====================================================================
        # 1. ANCRAGE COMPTABLE (BOOK VALUE)
        # =====================================================================
        bv_per_share = self._select_book_value(financials, params)

        self.add_step(
            step_key="RIM_BV_INITIAL",
            label="Actif Net Comptable Initial",
            theoretical_formula=r"BV_0",
            result=bv_per_share,
            numerical_substitution=f"BV_0 = {bv_per_share:,.2f}"
        )

        # =====================================================================
        # 2. COÛT DES FONDS PROPRES (Ke)
        # =====================================================================
        ke, sub_ke = self._compute_cost_of_equity(financials, params)

        self.add_step(
            step_key="RIM_KE_CALC",
            label="Coût des Fonds Propres (Ke)",
            theoretical_formula=r"k_e = R_f + \beta \times MRP",
            result=ke,
            numerical_substitution=sub_ke
        )

        # =====================================================================
        # 3. POLITIQUE DE DISTRIBUTION (PAYOUT)
        # =====================================================================
        eps_base = self._select_eps_base(financials)
        payout_ratio = self._compute_payout_ratio(financials, eps_base)

        self.add_step(
            step_key="RIM_PAYOUT",
            label="Politique de Distribution",
            theoretical_formula=r"Payout = \frac{Div}{EPS}",
            result=payout_ratio,
            numerical_substitution=f"{financials.last_dividend or 0.0:,.2f} / {eps_base:,.2f}"
        )

        # =====================================================================
        # 4. PROJECTION DES BÉNÉFICES
        # =====================================================================
        years = params.projection_years
        projected_eps = self._project_eps(eps_base, params.fcf_growth_rate, years)

        self.add_step(
            step_key="RIM_EPS_PROJ",
            label="Projection des Bénéfices",
            theoretical_formula=r"EPS_t = EPS_{t-1} \times (1+g)",
            result=projected_eps[-1],
            numerical_substitution=f"{eps_base:,.2f} × (1 + {params.fcf_growth_rate:.3f})^{years}"
        )

        # =====================================================================
        # 5. CALCUL DES PROFITS RÉSIDUELS
        # =====================================================================
        residual_incomes, projected_bvs = calculate_rim_vectors(
            bv_per_share, ke, projected_eps, payout_ratio
        )

        self.add_step(
            step_key="RIM_RI_CALC",
            label="Calcul des Surprofits (RI)",
            theoretical_formula=r"RI_t = NI_t - (k_e \times BV_{t-1})",
            result=sum(residual_incomes),
            numerical_substitution=f"{projected_eps[0]:,.2f} - ({ke:.4f} × {bv_per_share:,.2f})"
        )

        # =====================================================================
        # 6. ACTUALISATION DES PROFITS RÉSIDUELS
        # =====================================================================
        discount_factors = calculate_discount_factors(ke, years)
        discounted_ri_sum = calculate_npv(residual_incomes, ke)

        self.add_step(
            step_key="NPV_CALC",
            label="Valeur Actuelle des Surprofits",
            theoretical_formula=r"\sum \frac{RI_t}{(1+k_e)^t}",
            result=discounted_ri_sum,
            numerical_substitution=f"NPV(Residual Incomes, r={ke:.4f})"
        )

        # =====================================================================
        # 7. VALEUR TERMINALE (PERSISTANCE OHLSON)
        # =====================================================================
        tv_ri, discounted_tv = self._compute_rim_terminal_value(
            residual_incomes[-1], ke, discount_factors[-1], params
        )

        # =====================================================================
        # 8. VALEUR INTRINSÈQUE FINALE
        # =====================================================================
        intrinsic_value = bv_per_share + discounted_ri_sum + discounted_tv
        shares_to_use = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding

        self.add_step(
            step_key="RIM_FINAL_VALUE",
            label="Valeur Intrinsèque RIM",
            theoretical_formula=r"IV = BV_0 + \sum PV(RI_t) + PV(TV)",
            result=intrinsic_value,
            numerical_substitution=f"{bv_per_share:,.2f} + {discounted_ri_sum:,.2f} + {discounted_tv:,.2f}"
        )

        # =====================================================================
        # 9. MÉTRIQUES D'AUDIT
        # =====================================================================
        audit_metrics = self._compute_rim_audit_metrics(financials, eps_base, bv_per_share, ke)

        return RIMValuationResult(
            request=None,
            financials=financials,
            params=params,
            intrinsic_value_per_share=intrinsic_value,
            market_price=financials.current_price,
            cost_of_equity=ke,
            current_book_value=bv_per_share,
            projected_residual_incomes=residual_incomes,
            projected_book_values=projected_bvs,
            discount_factors=discount_factors,
            sum_discounted_ri=discounted_ri_sum,
            terminal_value_ri=tv_ri,
            discounted_terminal_value=discounted_tv,
            total_equity_value=intrinsic_value * shares_to_use,
            calculation_trace=self.calculation_trace,
            roe_observed=audit_metrics["roe"],
            payout_ratio_observed=payout_ratio,
            spread_roe_ke=audit_metrics["spread"],
            pb_ratio_observed=audit_metrics["pb_ratio"]
        )

    # ==========================================================================
    # MÉTHODES PRIVÉES
    # ==========================================================================

    def _select_book_value(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> float:
        """Sélectionne la Book Value avec priorité aux paramètres manuels."""
        bv = params.manual_book_value if params.manual_book_value is not None else financials.book_value_per_share

        if bv is None or bv <= 0:
            raise CalculationError("Book Value par action requise et > 0.")

        return bv

    def _compute_cost_of_equity(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters
    ) -> tuple[float, str]:
        """Calcule le coût des fonds propres via CAPM."""
        beta_used = params.manual_beta if params.manual_beta is not None else financials.beta

        if params.manual_cost_of_equity is not None:
            ke = params.manual_cost_of_equity
            sub_ke = f"k_e = {ke:.4f} (Surcharge Analyste)"
        else:
            ke = calculate_cost_of_equity_capm(
                params.risk_free_rate, beta_used, params.market_risk_premium
            )
            sub_ke = f"{params.risk_free_rate:.4f} + ({beta_used:.2f} × {params.market_risk_premium:.4f})"

        return ke, sub_ke

    def _select_eps_base(self, financials: CompanyFinancials) -> float:
        """Sélectionne l'EPS de base avec fallback."""
        eps_base = financials.eps_ttm

        if eps_base is None or eps_base <= 0:
            if financials.net_income_ttm and financials.shares_outstanding > 0:
                eps_base = financials.net_income_ttm / financials.shares_outstanding

        if eps_base is None or eps_base <= 0:
            raise CalculationError("EPS requis pour projeter les profits résiduels.")

        return eps_base

    def _compute_payout_ratio(
        self,
        financials:  CompanyFinancials,
        eps_base: float
    ) -> float:
        """Calcule le ratio de distribution avec bornes de sécurité."""
        dividend = financials.last_dividend or 0.0
        return max(0.0, min(0.90, dividend / eps_base))

    def _project_eps(
        self,
        eps_base: float,
        growth_rate: float,
        years: int
    ) -> List[float]:
        """Projette les EPS sur l'horizon de valorisation."""
        return [eps_base * ((1.0 + growth_rate) ** (t + 1)) for t in range(years)]

    def _compute_rim_terminal_value(
        self,
        terminal_ri: float,
        ke: float,
        last_discount_factor: float,
        params: DCFParameters
    ) -> tuple[float, float]:
        """Calcule la valeur terminale selon le modèle d'Ohlson."""
        omega = params.exit_multiple_value if params.exit_multiple_value is not None else 0.60
        tv_ri = (terminal_ri * omega) / (1 + ke - omega)
        discounted_tv = tv_ri * last_discount_factor

        sub_tv = f"({terminal_ri:,.2f} × {omega:.2f}) / (1 + {ke:.4f} - {omega:.2f})"

        self.add_step(
            step_key="RIM_TV_OHLSON",
            label="Valeur Terminale (Persistance ω)",
            theoretical_formula=r"TV_{RI} = \frac{RI_n \times \omega}{1 + k_e - \omega}",
            result=discounted_tv,
            numerical_substitution=f"{sub_tv} × {last_discount_factor:.4f}",
            interpretation="Estimation de la persistance des surprofits."
        )

        return tv_ri, discounted_tv

    def _compute_rim_audit_metrics(
        self,
        financials: CompanyFinancials,
        eps_base: float,
        bv_per_share: float,
        ke: float
    ) -> dict:
        """Calcule les métriques d'audit spécifiques au RIM."""
        roe = eps_base / bv_per_share if bv_per_share > 0 else 0.0
        pb_ratio = financials.current_price / bv_per_share if bv_per_share > 0 else 0.0
        spread = roe - ke

        return {
            "roe": roe,
            "pb_ratio": pb_ratio,
            "spread": spread
        }