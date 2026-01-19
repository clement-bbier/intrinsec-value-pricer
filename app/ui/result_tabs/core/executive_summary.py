"""
app/ui/result_tabs/core/executive_summary.py

ONGLET — RÉSUMÉ EXÉCUTIF (EXECUTIVE SUMMARY)

Rôle : Affichage de synthèse institutionnelle haute visibilité
Pattern : ResultTabBase (Template Method)
Style : Numpy docstrings
Ordre : 1 (toujours premier onglet affiché)

Version : V1.0 — ST-2.2
Risques financiers : Aucun calcul, affichage seulement

Dépendances critiques :
- streamlit >= 1.28.0
- core.models.ValuationResult
- core.i18n.KPITexts

Fonctionnalités :
- Prix de marché vs Valeur intrinsèque
- Football Field (triangulation multiples)
- Score de confiance audit
- Support scénarios probabilistes
"""

from typing import Any

import streamlit as st

from src.domain.models import ValuationResult
from core.i18n import KPITexts
from app.ui.base import ResultTabBase


class ExecutiveSummaryTab(ResultTabBase):
    """
    Onglet du résumé exécutif institutionnel.

    Affiche la synthèse décisionnelle haute visibilité avec les métriques
    essentielles : prix de marché, valeur intrinsèque, triangulation et
    score de confiance. Supporte les scénarios probabilistes.

    Attributes
    ----------
    TAB_ID : str
        Identifiant unique de l'onglet.
    LABEL : str
        Nom d'affichage dans l'interface.
    ICON : str
        Icône représentative.
    ORDER : int
        Ordre d'affichage (1 = premier).
    IS_CORE : bool
        Toujours visible (onglet core).

    Notes
    -----
    Hérite de ResultTabBase pour l'intégration dans l'orchestrateur
    d'onglets. Utilise le système i18n pour l'internationalisation.
    """

    TAB_ID = "executive_summary"
    LABEL = "Résumé Exécutif"
    ICON = "📊"
    ORDER = 1
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche le résumé exécutif institutionnel.

        Rend la synthèse haute visibilité avec métriques clés et triangulation.
        Supporte l'affichage conditionnel selon la présence de scénarios.

        Parameters
        ----------
        result : ValuationResult
            Résultat complet de la valorisation contenant financials,
            audit_report, scenario_synthesis, multiples_triangulation.
        **kwargs : Any
            Paramètres additionnels (non utilisés actuellement).

        Notes
        -----
        Structure l'affichage en deux sections :
        1. Métriques principales (prix, valeur, upside, confiance)
        2. Football Field (triangulation sectorielle)

        Le layout s'adapte selon la présence de scénarios probabilistes.
        """
        f = result.financials
        st.subheader(KPITexts.EXEC_TITLE.format(name=f.name, ticker=f.ticker).upper())

        # Métriques principales
        with st.container(border=True):
            if result.scenario_synthesis:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(KPITexts.LABEL_PRICE, f"{result.market_price:,.2f} {f.currency}")
                ev = result.scenario_synthesis.expected_value
                upside_ev = (ev / result.market_price) - 1
                c2.metric(KPITexts.LABEL_EXPECTED_VALUE, f"{ev:,.2f} {f.currency}", delta=f"{upside_ev:.1%}")
                c3.metric(KPITexts.LABEL_IV, f"{result.intrinsic_value_per_share:,.2f} {f.currency}")
                c4.metric(KPITexts.EXEC_CONFIDENCE, result.audit_report.rating if result.audit_report else "—")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric(KPITexts.LABEL_PRICE, f"{result.market_price:,.2f} {f.currency}")
                c2.metric(KPITexts.LABEL_IV, f"{result.intrinsic_value_per_share:,.2f} {f.currency}", delta=f"{result.upside_pct:.1%}")
                c3.metric(KPITexts.EXEC_CONFIDENCE, result.audit_report.rating if result.audit_report else "—")

        # Football Field (triangulation)
        st.markdown(f"#### {KPITexts.FOOTBALL_FIELD_TITLE}")
        if result.multiples_triangulation:
            rel = result.multiples_triangulation
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(KPITexts.LABEL_FOOTBALL_FIELD_IV, f"{result.intrinsic_value_per_share:,.1f}")
                c2.metric(KPITexts.LABEL_FOOTBALL_FIELD_PE, f"{rel.pe_based_price:,.1f}")
                c3.metric(KPITexts.LABEL_FOOTBALL_FIELD_EBITDA, f"{rel.ebitda_based_price:,.1f}")
                c4.metric(KPITexts.LABEL_FOOTBALL_FIELD_PRICE, f"{result.market_price:,.1f}")
        else:
            st.info(KPITexts.LABEL_MULTIPLES_UNAVAILABLE)

    def get_display_label(self) -> str:
        return self.LABEL
