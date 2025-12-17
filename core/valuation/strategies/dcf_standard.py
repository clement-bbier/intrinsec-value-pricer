"""
core/valuation/strategies/dcf_standard.py

Méthode : FCFF Two-Stage Discounted Cash Flow
Version : V1 Normative

Références académiques :
- Damodaran, A. – Investment Valuation
- CFA Institute – Equity Valuation

Usage :
- Entreprises matures
- Cash-flows prévisibles
- Structure financière relativement stable
"""

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class StandardFCFFStrategy(ValuationStrategy):
    """
    FCFF Two-Stage Discounted Cash Flow (Standard).

    Référence académique :
    - Aswath Damodaran

    Domaine de validité :
    - Entreprises établies
    - Modèle économique lisible
    - FCF positifs ou normalisables

    Invariants financiers :
    - WACC > g_terminal
    - Horizon de projection > 0
    - Nombre d’actions > 0
    """

    academic_reference = "Damodaran"
    economic_domain = "Mature firms / Stable cash-flows"
    financial_invariants = [
        "WACC > g_terminal",
        "projection_years > 0",
        "shares_outstanding > 0"
    ]

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Exécute un DCF FCFF Two-Stage standard.

        Étapes :
        - Sélection du FCF de base (TTM ou override)
        - Validation des préconditions
        - Délégation au moteur DCF déterministe partagé
        """

        logger.info(
            "[Strategy] FCFF Two-Stage | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. SÉLECTION DU FCF DE BASE
        # ====================================================

        fcf_base = financials.fcf_last

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info(
                "[FCFF Standard] FCF override manuel utilisé : %.2f",
                fcf_base
            )

        if fcf_base is None:
            raise CalculationError(
                "FCF de base indisponible (fcf_last manquant)."
            )

        # ====================================================
        # 2. EXÉCUTION DU DCF
        # ====================================================

        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )
