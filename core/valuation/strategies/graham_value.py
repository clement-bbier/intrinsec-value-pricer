"""
core/valuation/strategies/graham_value.py

MÉTHODE : GRAHAM INTRINSIC VALUE — VERSION V8.2
Rôle : Estimation "Value" (1974 Revised) avec transparence totale sur l'ajustement AAA.
Architecture : Audit-Grade avec traçabilité Glass Box complète.
"""

from __future__ import annotations

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, GrahamValuationResult
from core.valuation.strategies. abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class GrahamNumberStrategy(ValuationStrategy):
    """
    Estimation 'Value' (Graham 1974 Revised) avec audit mathématique complet.

    Formule : IV = (EPS × (8.5 + 2g) × 4.4) / Y
    Où Y est le rendement des obligations AAA.
    """

    academic_reference = "Benjamin Graham (1974)"
    economic_domain = "Value Investing / Defensive"
    financial_invariants = [
        "eps > 0",
        "aaa_yield > 0"
    ]

    def execute(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters
    ) -> GrahamValuationResult:
        """
        Exécute la stratégie Graham 1974 Revised.

        Args:
            financials: Données financières de l'entreprise
            params: Paramètres de valorisation

        Returns:
            Résultat Graham complet avec métriques d'audit
        """
        logger.info("[Strategy] Graham 1974 Revised | ticker=%s", financials.ticker)

        # =====================================================================
        # 1. ANCRAGE CAPACITÉ BÉNÉFICIAIRE
        # =====================================================================
        eps, source_eps = self._select_eps(financials, params)

        self. add_step(
            step_key="GRAHAM_EPS_BASE",
            label="BPA Normalisé (EPS)",
            theoretical_formula=r"EPS",
            result=eps,
            numerical_substitution=f"EPS = {eps:.2f} ({source_eps})",
            interpretation="Bénéfice par action utilisé comme socle de rentabilité."
        )

        # =====================================================================
        # 2. MULTIPLICATEUR DE CROISSANCE
        # =====================================================================
        growth_multiplier = self._compute_growth_multiplier(params. fcf_growth_rate)
        g_display = params.fcf_growth_rate * 100.0

        self.add_step(
            step_key="GRAHAM_MULTIPLIER",
            label="Multiplicateur de croissance",
            theoretical_formula=r"M = 8.5 + 2g",
            result=growth_multiplier,
            numerical_substitution=f"8.5 + 2 × {g_display:.2f}",
            interpretation="Prime de croissance appliquée selon le barème révisé de Graham."
        )

        # =====================================================================
        # 3. VALEUR INTRINSÈQUE FINALE
        # =====================================================================
        self._validate_aaa_yield(params. corporate_aaa_yield)

        intrinsic_value = self._compute_intrinsic_value(
            eps, growth_multiplier, params.corporate_aaa_yield
        )
        y_display = params.corporate_aaa_yield * 100.0

        self.add_step(
            step_key="GRAHAM_FINAL",
            label="Valeur Graham 1974",
            theoretical_formula=r"IV = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}",
            result=intrinsic_value,
            numerical_substitution=f"({eps:.2f} × {growth_multiplier:.2f} × 4.4) / {y_display:.2f}",
            interpretation="Estimation de la valeur intrinsèque ajustée par le rendement des obligations AAA."
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
            growth_rate_used=params.fcf_growth_rate,
            aaa_yield_used=params.corporate_aaa_yield,
            calculation_trace=self.calculation_trace,
            pe_observed=audit_metrics["pe"],
            graham_multiplier=growth_multiplier,
            payout_ratio_observed=audit_metrics["payout"]
        )

    # ==========================================================================
    # MÉTHODES PRIVÉES
    # ==========================================================================

    def _select_eps(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters
    ) -> tuple[float, str]:
        """
        Sélectionne l'EPS avec cascade de fallbacks.

        Priorité :
        1. Manual override (Expert)
        2. EPS TTM (Yahoo)
        3. Net Income / Shares (calculé)

        Returns:
            Tuple (eps, source_description)
        """
        # Priorité 1 : Override manuel
        if params.manual_fcf_base is not None:
            return params.manual_fcf_base, "Manual override (Expert)"

        # Priorité 2 : EPS TTM direct
        if financials.eps_ttm is not None and financials.eps_ttm > 0:
            return financials.eps_ttm, "Yahoo Finance (TTM)"

        # Priorité 3 :  Calcul depuis Net Income
        if financials.net_income_ttm and financials.shares_outstanding > 0:
            eps_calc = financials.net_income_ttm / financials.shares_outstanding
            if eps_calc > 0:
                return eps_calc, "Calculated (Net Income / Shares)"

        raise CalculationError("EPS strictement positif requis pour le modèle de Graham.")

    def _compute_growth_multiplier(self, growth_rate: float) -> float:
        """
        Calcule le multiplicateur de croissance Graham.

        Formule : M = 8.5 + 2g (où g est en pourcentage)
        """
        g_percent = growth_rate * 100.0
        return 8.5 + 2.0 * g_percent

    def _validate_aaa_yield(self, aaa_yield: float) -> None:
        """Valide que le rendement AAA est strictement positif."""
        if aaa_yield is None or aaa_yield <= 0:
            raise CalculationError("Le rendement obligataire AAA (Y) doit être > 0.")

    def _compute_intrinsic_value(
        self,
        eps:  float,
        multiplier: float,
        aaa_yield: float
    ) -> float:
        """
        Calcule la valeur intrinsèque Graham.

        Formule : IV = (EPS × Multiplier × 4.4) / Y
        Le 4.4 est le rendement AAA de référence en 1962.
        """
        y_percent = aaa_yield * 100.0
        return (eps * multiplier * 4.4) / y_percent

    def _compute_graham_audit_metrics(
            self,
            financials: CompanyFinancials,
            eps: float
    ) -> dict:
        """Calcule les métriques d'audit pour le résultat Graham."""
        # P/E observé
        pe = None
        if eps > 0:
            pe = financials.current_price / eps

        # Payout ratio
        payout = None
        if financials.net_income_ttm and financials.net_income_ttm > 0:
            payout = financials.dividends_total_calculated / financials.net_income_ttm

        return {
            "pe": pe,
            "payout": payout
        }