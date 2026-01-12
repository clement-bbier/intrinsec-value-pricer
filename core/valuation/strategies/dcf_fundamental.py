"""
core/valuation/strategies/dcf_fundamental.py

MÉTHODE :  FCFF NORMALIZED — VERSION V8.2
Rôle :  Normalisation des flux cycliques et délégation au moteur mathématique.
Architecture :  Audit-Grade avec alignement intégral sur le registre Glass Box.
"""

from __future__ import annotations

import logging

from core. exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters, DCFValuationResult, TraceHypothesis
from core.valuation.strategies.abstract import ValuationStrategy

logger = logging.getLogger(__name__)


class FundamentalFCFFStrategy(ValuationStrategy):
    """
    FCFF Normalisé (Cyclical / Fundamental).

    Utilise des flux lissés pour neutraliser la volatilité des cycles économiques.
    Adapté aux entreprises industrielles et cycliques.
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

        Args:
            financials: Données financières de l'entreprise
            params:  Paramètres de valorisation

        Returns:
            Résultat DCF complet
        """
        logger.info("[Strategy] FCFF Normalized | ticker=%s", financials.ticker)

        # =====================================================================
        # 1. SÉLECTION DU FCF NORMALISÉ
        # =====================================================================
        fcf_base, source = self._select_normalized_fcf(financials, params)

        self.add_step(
            step_key="FCF_NORM_SELECTION",
            label="Ancrage du Flux Normalisé (FCF_norm)",
            theoretical_formula=r"FCF_{norm}",
            result=fcf_base,
            numerical_substitution=f"FCF_norm = {fcf_base: ,.2f} ({source})",
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

        # =====================================================================
        # 2. CONTRÔLE DE VIABILITÉ DU MODÈLE
        # =====================================================================
        self._validate_fcf_positivity(fcf_base)

        self.add_step(
            step_key="FCF_STABILITY_CHECK",
            label="Contrôle de Viabilité Financière",
            theoretical_formula=r"FCF_{norm} > 0",
            result=1.0,
            numerical_substitution=f"{fcf_base:,.2f} > 0",
            interpretation="Validation de la capacité de l'entreprise à générer des flux de trésorerie positifs sur un cycle."
        )

        # =====================================================================
        # 3. EXÉCUTION DU DCF DÉTERMINISTE (DÉLÉGATION)
        # =====================================================================
        return self._run_dcf_math(
            base_flow=fcf_base,
            financials=financials,
            params=params
        )

    def _select_normalized_fcf(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> tuple[float, str]:
        """
        Sélectionne le FCF normalisé avec priorité aux paramètres manuels.

        Returns:
            Tuple (fcf_base, source_description)
        """
        if params.manual_fcf_base is not None:
            return params.manual_fcf_base, "Manual override (Expert)"

        if financials.fcf_fundamental_smoothed is None:
            raise CalculationError(
                "FCF normalisé indisponible (fcf_fundamental_smoothed manquant)."
            )

        return financials.fcf_fundamental_smoothed, "Fundamental smoothed FCF (Yahoo/Analyst)"

    def _validate_fcf_positivity(self, fcf_base: float) -> None:
        """
        Valide que le FCF normalisé est strictement positif.

        Un FCF négatif invalide l'usage d'un DCF standard pour l'auditeur.
        """
        if fcf_base <= 0:
            raise CalculationError(
                "Flux normalisé négatif : l'entreprise ne génère pas de valeur sur son cycle. "
                "La méthode DCF est mathématiquement inapplicable ici."
            )