"""
Stratégie FCFE (Free Cash Flow to Equity).

Référence Académique : Damodaran (Investment Valuation)
Domaine Économique : Entreprises endettées avec valorisation actionnariale directe
Invariants du Modèle : Reconstruction rigoureuse du flux actionnaire (Clean Walk)
"""

from __future__ import annotations
import logging
from typing import Tuple

from src.exceptions import CalculationError
from src.models import (
    CompanyFinancials, DCFParameters, EquityDCFValuationResult,
    ValuationMode
)
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import SimpleFlowProjector
from src.computation.financial_math import calculate_fcfe_reconstruction

# Import centralisé i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources,
    KPITexts,
    DiagnosticTexts
)

logger = logging.getLogger(__name__)


class FCFEStrategy(ValuationStrategy):
    """
    Stratégie FCFE (Direct Equity).

    Calcule la valeur intrinsèque via la reconstruction rigoureuse des flux actionnaires
    en tenant compte du coût des fonds propres (Ke) et de l'endettement net.
    """

    academic_reference = "Damodaran"
    economic_domain = "Equity Valuation / Leveraged Firms"

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> EquityDCFValuationResult:
        """
        Exécute la valorisation FCFE via le Pipeline Unifié avec validation de type.
        """
        # 1. RECONSTRUCTION DU FLUX ACTIONNAIRE (CLEAN WALK)
        ni, adj, nb, fcfe_base, source = self._resolve_fcfe_components(financials, params)

        # Sécurité financière : FCFE négatif en mode Auto bloqué (ST-1.4)
        if params.growth.manual_fcf_base is None and fcfe_base <= 0:
            raise CalculationError(
                CalculationErrors.NEGATIVE_FLUX_AUTO.format(
                    model=RegistryTexts.FCFE_L,
                    val=fcfe_base
                )
            )

        self.add_step(
            step_key="FCFE_BASE_SELECTION",
            label=RegistryTexts.FCFE_BASE_L,
            theoretical_formula=StrategyFormulas.FCFE_RECONSTRUCTION,
            result=fcfe_base,
            numerical_substitution=KPITexts.SUB_FCFE_WALK.format(
                ni=ni, adj=adj, nb=nb, total=fcfe_base
            ),
            interpretation=StrategyInterpretations.FCFE_LOGIC,
            source=source  # Injection de la source pour la Glass Box
        )

        # 2. CONFIGURATION DU PIPELINE (MODE DIRECT EQUITY)
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.FCFE,
            glass_box_enabled=self.glass_box_enabled
        )

        # Exécution (Le pipeline gère l'actualisation par le Ke)
        raw_result = pipeline.run(
            base_value=fcfe_base,
            financials=financials,
            params=params
        )

        # --- RÉSOLUTION DE L'ERREUR DE TYPAGE (DOWNCASTING) ---
        if not isinstance(raw_result, EquityDCFValuationResult):
            raise CalculationError(
                DiagnosticTexts.MODEL_LOGIC_MSG.format(
                    model=RegistryTexts.FCFE_L,
                    issue=type(raw_result).__name__
                )
            )

        result: EquityDCFValuationResult = raw_result

        # 3. FINALISATION ET AUDIT
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    @staticmethod
    def _resolve_fcfe_components(
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> Tuple[float, float, float, float, str]:
        """
        Résout les composants du FCFE pour assurer une reconstruction propre.
        Retourne : (Net Income, Adjustments, Net Borrowing, Total FCFE, Source)
        """
        g = params.growth

        # Cas A : Surcharge Expert Directe
        if g.manual_fcf_base is not None:
            return 0.0, 0.0, 0.0, g.manual_fcf_base, StrategySources.MANUAL_OVERRIDE

        # Cas B : Reconstruction
        ni = financials.net_income_ttm or 0.0
        nb = g.manual_net_borrowing if g.manual_net_borrowing is not None else (financials.net_borrowing_ttm or 0.0)

        # Ajustements (Amortissements - CapEx - ΔBFR) déduits du FCF reporté
        if financials.fcf_last is not None:
            adj = financials.fcf_last - ni
        else:
            adj = 0.0

        fcfe_calculated = calculate_fcfe_reconstruction(ni=ni, adjustments=adj, net_borrowing=nb)

        if fcfe_calculated <= 0:
            logger.warning("[Strategy] Negative reconstructed FCFE | ticker=%s", financials.ticker)

        return ni, adj, nb, fcfe_calculated, StrategySources.YAHOO_TTM_SIMPLE