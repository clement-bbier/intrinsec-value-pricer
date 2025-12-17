"""
core/valuation/strategies/dcf_fundamental.py

Méthode : FCFF Normalized Discounted Cash Flow
Version : V1 Normative

Références académiques :
- CFA Institute – Equity Valuation
- Damodaran, A. – Normalized Earnings & Cash Flows

Usage :
- Entreprises cycliques
- Industries capitalistiques
- Activités soumises à des cycles macroéconomiques
"""

import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    FCFF Normalisé (Cyclical / Fundamental).

    Principe :
    - On ne valorise PAS le dernier FCF observé
    - On valorise un FCF normatif représentatif d’un cycle moyen

    Référence académique :
    - CFA Institute
    - Damodaran (Normalized Earnings)

    Domaine de validité :
    - Cycliques (commodities, industrie lourde, construction)
    - Entreprises avec forte volatilité conjoncturelle

    Invariants financiers :
    - FCF normalisé économiquement cohérent
    - WACC > g_terminal
    - Horizon de projection > 0
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
        Exécute un DCF basé sur un FCF normalisé.

        Étapes :
        - Sélection du FCF fondamental lissé
        - Validation de la cohérence économique
        - Délégation au moteur DCF déterministe partagé
        """

        logger.info(
            "[Strategy] FCFF Normalized | ticker=%s",
            financials.ticker
        )

        # ====================================================
        # 1. SÉLECTION DU FCF NORMALISÉ
        # ====================================================

        fcf_base = financials.fcf_fundamental_smoothed

        if params.manual_fcf_base is not None:
            fcf_base = params.manual_fcf_base
            logger.info(
                "[FCFF Normalized] FCF override manuel utilisé : %.2f",
                fcf_base
            )

        if fcf_base is None:
            raise CalculationError(
                "FCF normalisé indisponible "
                "(fcf_fundamental_smoothed manquant)."
            )

        # ====================================================
        # 2. CONTRÔLE DE COHÉRENCE ÉCONOMIQUE
        # ====================================================

        if fcf_base <= 0:
            logger.warning(
                "[FCFF Normalized] FCF normalisé négatif ou nul : %.2f",
                fcf_base
            )
            raise CalculationError(
                "FCF normalisé négatif : "
                "méthode inadaptée sans ajustement manuel."
            )

        # ====================================================
        # 3. EXÉCUTION DU DCF
        # ====================================================

        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )
