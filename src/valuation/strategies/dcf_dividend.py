"""
Stratégie Dividend Discount Model (DDM).

Référence Académique : Gordon & Shapiro
Domaine Économique : Entreprises distributives matures et utilities
Invariants du Modèle : Valorisation par valeur actuelle des dividendes futurs
"""

from __future__ import annotations
import logging

from src.exceptions import CalculationError
from src.models import (
    CompanyFinancials,
    DCFParameters,
    EquityDCFValuationResult,
    ValuationMode
)
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.pipelines import DCFCalculationPipeline
from src.computation.growth import SimpleFlowProjector

# Import depuis core.i18n
from src.i18n import (
    RegistryTexts,
    StrategyInterpretations,
    StrategyFormulas,
    CalculationErrors,
    StrategySources
)

logger = logging.getLogger(__name__)


class DividendDiscountStrategy(ValuationStrategy):
    """
    Stratégie DDM (Dividend Discount Model).
    Estime la valeur intrinsèque comme la valeur actuelle des dividendes futurs.
    Standard rigoureux pour les banques, assurances et utilities matures.
    """

    academic_reference = "Myron J. Gordon / Shapiro"
    economic_domain = "Dividend-paying Firms / Mature Utilities"

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> EquityDCFValuationResult:
        """
        Exécute la valorisation DDM via le Pipeline Unifié.
        Note : Utilise la masse totale des dividendes pour assurer la cohérence du calcul final par action.
        """

        # =====================================================================
        # 1. DÉTERMINATION DU DIVIDENDE DE DÉPART (D_0)
        # =====================================================================
        # On récupère d'abord le dividende par action (Expert ou Auto)
        d0_per_share, source = self._resolve_dividend_base(financials, params)

        # Sécurité financière : Dividendes négatifs en mode Auto uniquement
        if params.growth.manual_dividend_base is None and d0_per_share <= 0:
            raise CalculationError(CalculationErrors.NEGATIVE_FLUX_AUTO.format(model="DDM", val=d0_per_share))

        # CORRECTION ÉCHELLE : Conversion en masse totale pour le Pipeline
        # Cela évite que l'étape 7 du pipeline (IV = Value / Shares) ne produise 0.00
        total_dividend_mass = d0_per_share * financials.shares_outstanding

        self.add_step(
            step_key="DDM_BASE_SELECTION",
            label=RegistryTexts.DDM_BASE_L,
            # On clarifie dans la formule que l'on travaille sur la masse totale
            theoretical_formula=StrategyFormulas.DIVIDEND_BASE,
            result=total_dividend_mass,
            numerical_substitution=f"{d0_per_share:,.2f} \times {financials.shares_outstanding:,.0f} = {total_dividend_mass:,.0f}",
            interpretation=StrategyInterpretations.DDM_LOGIC
        )

        # =====================================================================
        # 2. CONFIGURATION ET EXÉCUTION DU PIPELINE (MODE DIRECT EQUITY)
        # =====================================================================
        # Le mode DDM_GORDON_GROWTH active le Ke (CAPM) et bypass l'Equity Bridge
        pipeline = DCFCalculationPipeline(
            projector=SimpleFlowProjector(),
            mode=ValuationMode.DDM,
            glass_box_enabled=self.glass_box_enabled
        )

        # Le pipeline reçoit la masse totale et rendra un résultat cohérent par action
        result = pipeline.run(
            base_value=total_dividend_mass,
            financials=financials,
            params=params
        )

        # =====================================================================
        # 3. FINALISATION
        # =====================================================================
        self._merge_traces(result)
        self.generate_audit_report(result)
        self.verify_output_contract(result)

        return result

    def _resolve_dividend_base(self, financials: CompanyFinancials, params: DCFParameters) -> tuple[float, str]:
        """
        Détermine le dividende par action de référence (D0).
        Priorité : Surcharge Expert > Donnée Yahoo TTM.
        """
        g = params.growth

        # A. Surcharge Expert (Standard de contrôle Analyste)
        if g.manual_dividend_base is not None:
            return g.manual_dividend_base, StrategySources.MANUAL_OVERRIDE

        # B. Donnée extraite de Yahoo (Lissage TTM)
        if financials.dividend_share is not None and financials.dividend_share > 0:
            return financials.dividend_share, StrategySources.YAHOO_TTM_SIMPLE

        # C. Cas critique : Si aucun dividende n'est trouvé
        return 0.0, "N/A"
