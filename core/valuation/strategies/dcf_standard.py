"""
core/valuation/strategies/dcf_standard.py

MÉTHODE : FCFF TWO-STAGE — VERSION V8.2
Rôle : Sélection du flux de départ et délégation au moteur mathématique commun.
Architecture : Registry-Driven avec substitution numérique explicite.
"""

from __future__ import annotations

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies. abstract import ValuationStrategy

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources
)

logger = logging.getLogger(__name__)


class StandardFCFFStrategy(ValuationStrategy):
    """
    FCFF Two-Stage Discounted Cash Flow (Standard).

    Adapté aux entreprises matures avec des flux de trésorerie stables.
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

        Args:
            financials: Données financières de l'entreprise
            params:  Paramètres de valorisation

        Returns:
            Résultat DCF complet
        """
        logger.info("[Strategy] FCFF Two-Stage | ticker=%s", financials. ticker)

        # =====================================================================
        # 1. SÉLECTION DU FCF DE BASE
        # =====================================================================
        fcf_base, source = self._select_base_fcf(financials, params)

        self.add_step(
            step_key="FCF_BASE_SELECTION",
            label=RegistryTexts.DCF_FCF_BASE_L,
            theoretical_formula=r"FCF_0",
            result=fcf_base,
            numerical_substitution=f"FCF_0 = {fcf_base:,.2f} ({source})",
            interpretation=RegistryTexts.DCF_FCF_BASE_D
        )

        # =====================================================================
        # 2. EXÉCUTION DU DCF DÉTERMINISTE (DÉLÉGATION)
        # =====================================================================
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )

    def _select_base_fcf(
        self,
        financials:  CompanyFinancials,
        params: DCFParameters
    ) -> tuple[float, str]:
        """
        Sélectionne le FCF de base avec priorité aux paramètres manuels.

        Returns:
            Tuple (fcf_base, source_description)
        """
        if params.manual_fcf_base is not None:
            return params.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        if financials.fcf_last is None:
            raise CalculationError(CalculationErrors.MISSING_FCF_STD)

        return financials.fcf_last, StrategySources.YAHOO_TTM