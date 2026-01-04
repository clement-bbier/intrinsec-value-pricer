"""
core/valuation/strategies/dcf_fundamental.py
MÉTHODE : FCFF NORMALIZED — VERSION V6.0 (Audit-Grade)
Rôle : Normalisation des flux cycliques et délégation au moteur mathématique.
Audit-Grade : Alignement intégral sur le registre Glass Box et substitution numérique.
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
        Exécute la stratégie en identifiant et validant le flux normalisé de départ.
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
            source = "Manual override (Expert)"
        else:
            fcf_base = financials.fcf_fundamental_smoothed
            source = "Fundamental smoothed FCF (Yahoo/Analyst)"

        if fcf_base is None:
            raise CalculationError(
                "FCF normalisé indisponible (fcf_fundamental_smoothed manquant)."
            )

        # --- Trace Glass Box (Audit-Grade : Alignement Registre V6.1) ---
        self.add_step(
            step_key="FCF_NORM_SELECTION",
            label="Ancrage du Flux Normalisé (FCF_norm)",
            theoretical_formula=r"FCF_{norm} = Initial\_Smoothed\_Flow",
            result=fcf_base,
            numerical_substitution=f"FCF_norm = {fcf_base:,.2f} ({source})",
            interpretation=(
                "Le modèle utilise un flux lissé sur un cycle complet pour "
                "neutraliser la volatilité des bénéfices industriels ou cycliques."
            ),
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
        # 2. CONTRÔLE DE VIABILITÉ DU MODÈLE (ID: FCF_STABILITY_CHECK)
        # ====================================================

        if fcf_base <= 0:
            # Pour un auditeur, un FCF normalisé négatif invalide l'usage d'un DCF standard
            raise CalculationError(
                "Flux normalisé négatif : l'entreprise ne génère pas de valeur sur son cycle. "
                "La méthode DCF est mathématiquement inapplicable ici."
            )

        self.add_step(
            step_key="FCF_STABILITY_CHECK",
            label="Contrôle de Viabilité Financière",
            theoretical_formula=r"FCF_{norm} > 0",
            result=1.0,
            numerical_substitution=f"{fcf_base:,.2f} > 0",
            interpretation="Validation de la capacité de l'entreprise à générer des flux de trésorerie positifs sur un cycle."
        )

        # ====================================================
        # 3. EXÉCUTION DU DCF DÉTERMINISTE (DÉLÉGATION)
        # ====================================================
        # On délègue au moteur commun 'abstract.py' qui gère désormais :
        # - La triangulation Gordon vs Multiple.
        # - Le garde-fou Model Risk (g < WACC).
        # - La substitution numérique LaTeX pour le WACC et la NPV.
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )