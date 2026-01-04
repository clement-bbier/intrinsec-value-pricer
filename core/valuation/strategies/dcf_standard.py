"""
core/valuation/strategies/dcf_standard.py
MÉTHODE : FCFF TWO-STAGE — VERSION V5.0 (Registry-Driven)
Rôle : Sélection du flux de départ et délégation au moteur mathématique commun.
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


class StandardFCFFStrategy(ValuationStrategy):
    """
    FCFF Two-Stage Discounted Cash Flow (Standard).
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
        Exécute la stratégie en identifiant le flux de départ.
        """

        logger.info(
            "[Strategy] FCFF Two-Stage | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. SÉLECTION DU FCF DE BASE (ID: FCF_BASE_SELECTION)
        # ====================================================

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            source = "Manual override"
        else:
            fcf_base = financials.fcf_last
            source = "Last reported FCF (TTM)"

        if fcf_base is None:
            raise CalculationError(
                "FCF de base indisponible (fcf_last manquant)."
            )

        # --- Trace Glass Box (Découplage UI via ID) ---
        self.add_step(
            step_key="FCF_BASE_SELECTION",
            result=fcf_base,
            numerical_substitution=f"FCF_0 = {fcf_base:,.2f}"
        )

        # ====================================================
        # 2. EXÉCUTION DU DCF DÉTERMINISTE (DÉLÉGATION)
        # ====================================================
        # On délègue à _run_dcf_math (dans abstract.py) qui gère
        # déjà les IDs WACC_CALC, FCF_PROJ, NPV_CALC, etc.
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )