"""
app/ui/results/core/calculation_proof.py
Onglet — Preuve de Calcul (Glass Box) — Grade Institutionnel.

Rôle : Orchestrer le rendu séquentiel des étapes de calcul financier.
"""

from typing import Any
import streamlit as st

from src.models import ValuationResult
from src.i18n import KPITexts, UIMessages, PillarLabels
from src.config.constants import UIConstants  # Centralisation des seuils/logique
from app.ui.results.base_result import ResultTabBase
from app.ui.results.components.step_renderer import render_calculation_step


class CalculationProofTab(ResultTabBase):
    """
    Onglet de preuve de calcul Glass Box.
    Respecte la séparation entre le rendu et la logique de filtrage.
    """

    # Utilisation des constantes i18n pour éviter tout hardcoding
    TAB_ID = "calculation_proof"
    LABEL = KPITexts.TAB_CALC
    ORDER = 2
    IS_CORE = True

    def render(self, result: ValuationResult, **kwargs: Any) -> None:
        """
        Affiche la séquence de calcul de manière ordonnée.
        """

        # 1. Filtrage des étapes (Logique métier UI)
        # On exclut les étapes techniques (MC, SOTP, etc.) définies dans les constantes
        core_steps = [
            step for step in result.calculation_trace
            if not any(prefix in step.step_key for prefix in UIConstants.EXCLUDED_STEP_PREFIXES)
        ]

        # 2. Gestion de l'état vide
        if not core_steps:
            st.info(UIMessages.NO_CALCULATION_STEPS)
            return

        # 3. En-tête de l'onglet (Zéro hardcoding)
        st.markdown(f"### {KPITexts.TAB_CALC}")

        # Le texte explicatif provient désormais du registre i18n (KPITexts.SECTION_INPUTS_CAPTION ou similaire)
        st.caption(KPITexts.SECTION_INPUTS_CAPTION)
        st.divider()

        # 4. Rendu itératif via le composant atomique stabilisé
        # Chaque étape est rendue avec son propre container et rendu LaTeX
        for idx, step in enumerate(core_steps, start=1):
            render_calculation_step(idx, step)

            # Espacement institutionnel entre les blocs de calcul
            st.write("")