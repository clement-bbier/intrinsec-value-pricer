"""
core/valuation/strategies/dcf_equity.py
MÉTHODE : FREE CASH FLOW TO EQUITY (FCFE) — VERSION V11.0
Rôle : Valorisation directe des fonds propres via le flux résiduel (Clean Walk).
Architecture : Audit-Grade s'appuyant sur le Pipeline Unifié et le moteur V11.0.
Source : Damodaran (Investment Valuation).
"""

from __future__ import annotations
import logging

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, EquityDCFValuationResult, ValuationMode
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.pipelines import DCFCalculationPipeline
from core.computation.growth import SimpleFlowProjector
from core.computation.financial_math import calculate_fcfe_reconstruction

# Import depuis core.i18n
from core.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts
)

logger = logging.getLogger(__name__)


class FCFEStrategy(ValuationStrategy):
    """
    Stratégie FCFE (Direct Equity).
    Calcule la valeur intrinsèque via la reconstruction rigoureuse des flux actionnaires.
    """

    academic_reference = "Damodaran"
    economic_domain = "Equity Valuation / Leveraged Firms"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> EquityDCFValuationResult:
        """Exécute la valorisation FCFE via le Pipeline Unifié (Sync V11.0)."""
        # =====================================================================
        # 1. RECONSTRUCTION DU FLUX ACTIONNAIRE (CLEAN WALK)
        # =====================================================================
        # On extrait les composants pour la trace Glass Box
        ni, adj, nb, fcfe_base, source = self._resolve_fcfe_components(financials, params)

        self.add_step(
            step_key="FCFE_BASE_SELECTION",
            label=RegistryTexts.FCFE_BASE_L,
            theoretical_formula=StrategyFormulas.FCFE_RECONSTRUCTION,
            result=fcfe_base,
            numerical_substitution=KPITexts.SUB_FCFE_WALK.format(
                ni=ni, adj=adj, nb=nb, total=fcfe_base
            ),
            interpretation=StrategyInterpretations.FCFE_LOGIC
        )

        # =====================================================================
        # 2. CONFIGURATION DU PIPELINE (MODE DIRECT EQUITY)
        # =====================================================================
        # Le mode FCFE_TWO_STAGE garantit l'usage du Ke et l'absence d'Equity Bridge
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFE,
            glass_box_enabled=self.glass_box_enabled
        )

        # Exécution (Le pipeline gère l'actualisation par le Ke)
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

    def _resolve_fcfe_components(self, financials: CompanyFinancials, params: DCFParameters) -> tuple:
        """
        Résout les composants du FCFE pour assurer une reconstruction propre.
        Retourne : (Net Income, Adjustments, Net Borrowing, Total FCFE, Source)
        """
        g = params.growth

        # Cas A : Surcharge Expert Directe
        if g.manual_fcf_base is not None:
            # En mode manuel, on considère que l'expert a déjà fait ses calculs
            return (0, 0, 0, g.manual_fcf_base, StrategySources.MANUAL_OVERRIDE)

        # Cas B : Reconstruction (Mode Auto ou Expert Partiel)
        # 1. Résultat Net (Net Income)
        ni = financials.net_income_ttm or 0.0

        # 2. Net Borrowing (Dette émise - Dette remboursée)
        nb = g.manual_net_borrowing if g.manual_net_borrowing is not None else (financials.net_borrowing_ttm or 0.0)

        # 3. Ajustements (Amortissements - CapEx - ΔBFR)
        # Note : En mode Auto, on peut déduire les ajustements si FCF est fourni
        if financials.fcf_last is not None:
            # On "nettoie" le FCF reporté pour isoler les ajustements hors endettement
            # FCF (Operating - Capex) est déjà Net Income + Adjustments
            adj = financials.fcf_last - ni
        else:
            adj = 0.0

        fcfe_calculated = calculate_fcfe_reconstruction(ni=ni, adjustments=adj, net_borrowing=nb)

        if fcfe_calculated <= 0:
            logger.warning("[Strategy] Negative reconstructed FCFE | ticker=%s", financials.ticker)

        return ni, adj, nb, fcfe_calculated, StrategySources.YAHOO_TTM_SIMPLE