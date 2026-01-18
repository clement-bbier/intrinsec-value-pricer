"""
app/ui/result_tabs/optional/peer_multiples.py

ONGLET — VALORISATION RELATIVE (MULTIPLES DE COMPARABLES)

Rôle : Affichage de la triangulation sectorielle par multiples
Pattern : ResultTabBase (Template Method)
Style : Numpy docstrings

Version : V1.1 — DT-018 Resolution (Correction peer_count)
Risques financiers : Affichage de valorisations relatives, pas de calculs

Dépendances critiques :
- streamlit >= 1.28.0
- core.models.ValuationResult.multiples_triangulation
- core.models.MultiplesData.peer_count

Visible uniquement si multiples_triangulation contient des peers.
Présente : médianes sectorielles, valeurs implicites, triangulation.
"""

from __future__ import annotations

from typing import Any

import streamlit as st
import pandas as pd

from core.models import ValuationResult
from core.i18n import KPITexts
from app.ui.base import ResultTabBase
from app.ui.result_tabs.components.kpi_cards import format_smart_number


class PeerMultiplesTab(ResultTabBase):
    """
    Onglet de valorisation relative par comparables.

    Affiche la triangulation sectorielle avec les multiples médians
    des sociétés comparables et les valeurs implicites calculées.

    Attributes
    ----------
    TAB_ID : str
        Identifiant unique "peer_multiples".
    LABEL : str
        Label affiché "Valorisation Relative".
    ICON : str
        Icône vide (style sobre).
    ORDER : int
        Position d'affichage (4ème onglet).
    IS_CORE : bool
        False - onglet optionnel (visible si triangulation disponible).

    Notes
    -----
    Utilise result.multiples_triangulation.multiples_data pour accéder aux données.
    Présente les médianes sectorielles et valeurs implicites.
    Calcule automatiquement les écarts avec la société cible.
    """

    TAB_ID = "peer_multiples"
    LABEL = "Valorisation Relative"
    ICON = ""
    ORDER = 4
    IS_CORE = False

    def is_visible(self, result: ValuationResult) -> bool:
        """
        Détermine si l'onglet doit être affiché.

        Vérifie la présence de données de triangulation avec peers.

        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation à analyser.

        Returns
        -------
        bool
            True si multiples_triangulation existe et contient des peers.
        """
        return (
            result.multiples_triangulation is not None
            and len(result.multiples_triangulation.multiples_data.peers) > 0
        )

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche la valorisation relative par comparables.

        Présente les multiples médians du secteur et les valeurs implicites
        de la société cible selon ces multiples.

        Parameters
        ----------
        result : ValuationResult
            Résultat contenant multiples_triangulation avec les données peers.
        **kwargs : Any
            Paramètres additionnels (non utilisés).

        Notes
        -----
        Compare les multiples de la société cible avec les médianes sectorielles.
        Calcule les valeurs implicites par action via différents multiples.
        Présente un tableau synthétique des écarts.
        """
        md = result.multiples_triangulation.multiples_data

        st.markdown("**VALORISATION PAR COMPARABLES**")
        st.caption(f"Panel de {len(md.peers)} sociétés comparables")

        # Tableau des multiples
        with st.container(border=True):
            st.markdown("**Multiples du Panel**")

            multiples_df = pd.DataFrame({
                "Multiple": ["EV/EBITDA", "EV/EBIT", "P/E", "P/B"],
                "Médiane": [
                    f"{md.median_ev_ebitda:.1f}x" if md.median_ev_ebitda else "—",
                    f"{md.median_ev_ebit:.1f}x" if md.median_ev_ebit else "—",
                    f"{md.median_pe:.1f}x" if md.median_pe else "—",
                    f"{md.median_pb:.1f}x" if md.median_pb else "—",
                ],
                "Cible": [
                    f"{result.financials.ev_ebitda:.1f}x" if hasattr(result.financials, 'ev_ebitda') and result.financials.ev_ebitda else "—",
                    "—",
                    f"{result.financials.pe_ratio:.1f}x" if result.financials.pe_ratio else "—",
                    f"{result.financials.pb_ratio:.1f}x" if result.financials.pb_ratio else "—",
                ],
            })

            # Forcer les colonnes formatées en string pour éviter les erreurs Arrow
            multiples_df = multiples_df.astype({"Médiane": "string", "Cible": "string"})

            st.dataframe(multiples_df, hide_index=True, width='stretch')

        # Valeurs implicites
        if md.implied_value_ev_ebitda or md.implied_value_pe:
            with st.container(border=True):
                st.markdown("**Valeurs Implicites par Action**")

                col1, col2 = st.columns(2)

                if md.implied_value_ev_ebitda:
                    col1.metric(
                        "Via EV/EBITDA",
                        format_smart_number(md.implied_value_ev_ebitda, result.financials.currency)
                    )

                if md.implied_value_pe:
                    col2.metric(
                        "Via P/E",
                        format_smart_number(md.implied_value_pe, result.financials.currency)
                    )

    def get_display_label(self) -> str:
        """
        Retourne le label d'affichage de l'onglet.

        Returns
        -------
        str
            Label "Valorisation Relative".
        """
        return self.LABEL