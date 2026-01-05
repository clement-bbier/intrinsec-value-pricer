"""
core/valuation/strategies/dcf_standard.py
MÉTHODE : FCFF TWO-STAGE — VERSION V5.0 (Registry-Driven)
Rôle : Sélection du flux de départ et délégation au moteur mathématique commun.
Audit-Grade : Ajout de la substitution numérique explicite et labels normalisés.
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
            source = "Manual override (Expert)"
        else:
            fcf_base = financials.fcf_last
            source = "Last reported FCF (TTM) - Yahoo Deep Fetch"

        if fcf_base is None:
            raise CalculationError(
                "FCF de base indisponible (fcf_last manquant ou nul)."
            )

        # --- Trace Glass Box (Audit-Grade : Substitution Numérique) ---
        # On affiche clairement l'origine de la donnée pour l'auditeur
        self.add_step(
            step_key="FCF_BASE_SELECTION",
            label="Sélection du Flux de Trésorerie de Base (FCF_0)",
            theoretical_formula="FCF_0 = Initial_Cash_Flow",
            result=fcf_base,
            numerical_substitution=f"FCF_0 = {fcf_base:,.2f} ({source})",
            interpretation=f"Le modèle démarre avec un flux de {fcf_base:,.2f} {financials.currency}."
        )

        # ====================================================
        # 2. EXÉCUTION DU DCF DÉTERMINISTE (DÉLÉGATION)
        # ====================================================
        # L'intelligence des Multiples et de l'Audit de corrélation
        # est gérée par le moteur mathématique commun pour garantir
        # l'uniformité entre toutes les stratégies FCFF.
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )