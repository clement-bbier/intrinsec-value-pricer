import streamlit as st

# Import des constantes du module core.docs
from core.docs.methodology_texts import (
    SIMPLE_DCF_TITLE,
    SIMPLE_DCF_SECTIONS,
    FUNDAMENTAL_DCF_TITLE,
    FUNDAMENTAL_DCF_SECTIONS,
    MONTE_CARLO_TITLE,
    MONTE_CARLO_SECTIONS,
)


def _render_sections(sections) -> None:
    """
    Helper interne pour afficher une liste de sections méthodologiques
    contenant des sous-titres, des blocs Markdown et des formules LaTeX.
    """
    for section in sections:
        # Sous-titre
        subtitle = section.get("subtitle")
        if subtitle:
            st.markdown(subtitle)

        # Blocs de texte Markdown
        for md in section.get("markdown_blocks", []):
            st.markdown(md)

        # Blocs de formules LaTeX
        for latex in section.get("latex_blocks", []):
            st.latex(latex)


def display_simple_dcf_formula() -> None:
    """
    Affiche la méthodologie et les formules utilisées pour la Méthode 1 – DCF Simple.
    Le contenu textuel et les formules viennent de core.docs.methodology_texts.
    """
    st.markdown(SIMPLE_DCF_TITLE)
    _render_sections(SIMPLE_DCF_SECTIONS)


def display_fundamental_dcf_formula() -> None:
    """
    Affiche la méthodologie et les formules utilisées pour la Méthode 2 – DCF Fondamental (3-Statement Light).
    Le contenu textuel et les formules viennent de core.docs.methodology_texts.
    """
    st.markdown(FUNDAMENTAL_DCF_TITLE)
    _render_sections(FUNDAMENTAL_DCF_SECTIONS)


def display_monte_carlo_formula() -> None:
    """
    Affiche la méthodologie et les formules utilisées pour la Méthode 3 – Simulation Monte Carlo.
    Le contenu textuel et les formules viennent de core.docs.methodology_texts.
    """
    st.markdown(MONTE_CARLO_TITLE)
    _render_sections(MONTE_CARLO_SECTIONS)