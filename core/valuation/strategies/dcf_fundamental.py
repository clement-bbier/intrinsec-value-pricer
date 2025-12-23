"""
core/valuation/strategies/dcf_fundamental.py

Méthode : FCFF Normalized Discounted Cash Flow
Version : V1.1 — Chapitre 4 conforme (Glass Box)
"""

import logging

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    TraceHypothesis
)
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    FCFF Normalisé (Cyclical / Fundamental).
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Cyclical / Industrial firms"
    financial_invariants = [
        "normalized_fcf > 0",
        "WACC > g_terminal",
        "projection_years > 0"
    ]

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:

        logger.info(
            "[Strategy] FCFF Normalized | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. SÉLECTION DU FCF NORMALISÉ (GLASS BOX)
        # ====================================================

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            source = "Manual override"
        else:
            fcf_base = financials.fcf_fundamental_smoothed
            source = "Fundamental smoothed FCF"

        if fcf_base is None:
            raise CalculationError(
                "FCF normalisé indisponible "
                "(fcf_fundamental_smoothed manquant)."
            )

        self.add_step(
            label="Sélection du flux de trésorerie normalisé",
            theoretical_formula="FCF₀ (normalisé)",
            hypotheses=[
                TraceHypothesis(
                    name="Normalized FCF",
                    value=fcf_base,
                    unit=financials.currency,
                    source=source
                )
            ],
            numerical_substitution=f"FCF₀ = {fcf_base:,.2f}",
            result=fcf_base,
            unit=financials.currency,
            interpretation=(
                "Flux de trésorerie libre représentatif d’un cycle économique "
                "normalisé, utilisé comme base de projection."
            )
        )

        # ====================================================
        # 2. CONTRÔLE DE COHÉRENCE ÉCONOMIQUE (GLASS BOX)
        # ====================================================

        self.add_step(
            label="Test de cohérence du FCF normalisé",
            theoretical_formula="FCF₀ > 0",
            hypotheses=[
                TraceHypothesis(
                    name="Normalized FCF",
                    value=fcf_base,
                    unit=financials.currency
                )
            ],
            numerical_substitution=f"{fcf_base:,.2f} > 0",
            result=1.0 if fcf_base > 0 else 0.0,
            unit="boolean",
            interpretation=(
                "Vérification que le FCF normalisé est économiquement cohérent "
                "pour une valorisation DCF."
            )
        )

        if fcf_base <= 0:
            raise CalculationError(
                "FCF normalisé négatif : "
                "méthode inadaptée sans ajustement manuel."
            )

        # ====================================================
        # 3. EXÉCUTION DU DCF DÉTERMINISTE
        # ====================================================

        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )