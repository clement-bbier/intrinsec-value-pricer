import streamlit as st
# Import des constantes du nouveau module core.docs
from core.docs.methodology_texts import (
    SIMPLE_DCF_TITLE,
    SIMPLE_DCF_SECTIONS,
)


def display_simple_dcf_formula() -> None:
    """
    Affiche la méthodologie et les formules utilisées pour la Méthode 1 – DCF Simple.
    Le contenu textuel et les formules viennent de core.docs.methodology_texts.
    """
    st.markdown(SIMPLE_DCF_TITLE)

    for section in SIMPLE_DCF_SECTIONS:
        # Sous-titre
        if "subtitle" in section:
            st.markdown(section["subtitle"])

        # Blocs de texte Markdown
        for md in section.get("markdown_blocks", []):
            st.markdown(md)

        # Blocs de formules LaTeX
        for latex in section.get("latex_blocks", []):
            st.latex(latex)