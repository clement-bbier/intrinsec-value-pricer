"""
core/valuation/strategies/dcf_fundamental.py
MÉTHODE : FCFF NORMALIZED — VERSION V5.0 (Registry-Driven)
Rôle : Normalisation des flux cycliques et délégation au moteur mathématique.
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
    Utilise des flux lissés pour neutraliser la volatilité des cycles économiques.
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
        """
        Exécute la stratégie en normalisant le flux de départ.
        """

        logger.info(
            "[Strategy] FCFF Normalized | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. SÉLECTION DU FCF NORMALISÉ (ID: FCF_NORM_SELECTION)
        # ====================================================

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            source = "Manual override"
        else:
            fcf_base = financials.fcf_fundamental_smoothed
            source = "Fundamental smoothed FCF (Yahoo/Analyst)"

        if fcf_base is None:
            raise CalculationError(
                "FCF normalisé indisponible (fcf_fundamental_smoothed manquant)."
            )

        # --- Trace Glass Box (Découplage UI via ID) ---
        self.add_step(
            step_key="FCF_NORM_SELECTION",
            result=fcf_base,
            numerical_substitution=f"FCF_norm = {fcf_base:,.2f}",
            hypotheses=[
                TraceHypothesis(
                    name="Normalized FCF",
                    value=fcf_base,
                    unit=financials.currency,
                    source=source
                )
            ]
        )

        # ====================================================
        # 2. CONTRÔLE DE COHÉRENCE (ID: FCF_STABILITY_CHECK)
        # ====================================================

        self.add_step(
            step_key="FCF_STABILITY_CHECK",
            result=1.0 if fcf_base > 0 else 0.0,
            numerical_substitution=f"FCF_norm = {fcf_base:,.2f}"
        )

        if fcf_base <= 0:
            raise CalculationError(
                "FCF normalisé négatif : méthode inadaptée sans ajustement manuel."
            )

        # ====================================================
        # 3. EXÉCUTION DU DCF DÉTERMINISTE (DÉLÉGATION)
        # ====================================================
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )