"""
core/valuation/strategies/dcf_equity.py
MÉTHODE : FREE CASH FLOW TO EQUITY (FCFE) — VERSION V10.0
Rôle : Valorisation directe des fonds propres via le flux résiduel post-dette.
Architecture : Audit-Grade s'appuyant sur le Pipeline Unifié (Sprint 3).
Source : Damodaran (Investment Valuation).
"""

from __future__ import annotations
import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, EquityDCFValuationResult, ValuationMode
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.pipelines import DCFCalculationPipeline
from core.computation.growth import SimpleFlowProjector
from core.computation.financial_math import calculate_fcfe_base

# Import des constantes de texte pour i18n
from app.ui_components.ui_texts import (
    RegistryTexts,
    StrategyInterpretations,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class FCFEStrategy(ValuationStrategy):
    """
    Stratégie FCFE (Direct Equity).
    Calcule la valeur intrinsèque de l'action en actualisant le flux résiduel
    après paiement des intérêts et variation de la dette nette.
    """

    academic_reference = "Damodaran"
    economic_domain = "Equity Valuation / Leveraged Firms"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> EquityDCFValuationResult:
        """Exécute la valorisation FCFE via le Pipeline Unifié."""
        logger.info("[Strategy] FCFE Direct Equity | ticker=%s", financials.ticker)

        # =====================================================================
        # 1. DÉTERMINATION DU FLUX ACTIONNAIRE DE DÉPART (FCFE_0)
        # =====================================================================
        fcfe_base, source = self._resolve_fcfe_base(financials, params)

        self.add_step(
            step_key="FCFE_BASE_SELECTION",
            label=RegistryTexts.FCFE_BASE_L,
            theoretical_formula=r"FCFE = FCFF - Int(1-\tau) + Net Borrowing",
            result=fcfe_base,
            numerical_substitution=KPITexts.SUB_FCFE_CALC.format(val=fcfe_base),
            interpretation=StrategyInterpretations.FCFE_LOGIC
        )

        # =====================================================================
        # 2. CONFIGURATION ET EXÉCUTION DU PIPELINE (MODE DIRECT EQUITY)
        # =====================================================================
        # Rigueur : On passe ValuationMode.FCFE_TWO_STAGE pour activer Ke et sauter le Bridge
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFE_TWO_STAGE,
            glass_box_enabled=self.glass_box_enabled
        )

        # Le résultat est un EquityDCFValuationResult (Contrat Direct Equity)
        result = pipeline.run(
            base_value=fcfe_base,
            financials=financials,
            params=params
        )

        # =====================================================================
        # 3. FINALISATION
        # =====================================================================
        self._merge_traces(result)

        return result

    def _resolve_fcfe_base(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """
        Détermine le FCFE de base.
        Priorité : Surcharge manuelle > Calcul rigoureux TTM.
        """
        g = params.growth
        r = params.rates

        # A. Surcharge Expert
        if g.manual_fcf_base is not None:
            return g.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # B. Calcul rigoureux (Source : Damodaran)
        # FCFE = FCFF - Interest(1-tax) + NetBorrowing
        fcff = financials.fcf_last if financials.fcf_last is not None else 0.0

        # Sécurisation des inputs
        interest = financials.interest_expense
        tax_rate = r.tax_rate if r.tax_rate is not None else 0.25
        net_borrowing = g.manual_net_borrowing if g.manual_net_borrowing is not None else (
                    financials.net_borrowing_ttm or 0.0)

        fcfe_calculated = calculate_fcfe_base(
            fcff=fcff,
            interest=interest,
            tax_rate=tax_rate,
            net_borrowing=net_borrowing
        )

        if fcfe_calculated <= 0 and financials.fcf_last is not None:
            logger.warning("[Strategy] FCFE calculé négatif pour %s", financials.ticker)
            # On ne lève pas d'erreur ici, le pipeline ou l'audit s'en chargera

        return fcfe_calculated, StrategySources.YAHOO_TTM_SIMPLE