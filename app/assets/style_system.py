"""
app/assets/style_system.py
DESIGN SYSTEM CENTRALISÉ — TERMINAL INSTITUTIONNEL
Rôle : Centraliser le CSS et les composants visuels de structure (Action 1.1).
"""

import streamlit as st
from core.i18n import CommonTexts, LegalTexts

# ==============================================================================
# 1. DESIGN SYSTEM (CSS COPIÉ MOT POUR MOT)
# ==============================================================================

INSTITUTIONAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* --- BASE & TYPOGRAPHIE --- */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Inter', sans-serif !important;
    color: #1e293b;
}
.stApp { background-color: #ECF0F8; }

/* --- SIDEBAR : BLEU NUIT INSTITUTIONNEL --- */
section[data-testid="stSidebar"] {
    background-color: #1F3056 !important;
}

/* Contraste des textes sidebar (Blanc Slate) */
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3, 
section[data-testid="stSidebar"] label p, 
section[data-testid="stSidebar"] .stMarkdown p {
    color: #f1f5f9 !important;
}

/* CORRECTIF : Visibilité des diviseurs dans la sidebar */
section[data-testid="stSidebar"] hr {
    border-top: 1.5px solid rgba(241, 245, 249, 0.3) !important;
    margin: 1.2rem 0 !important;
    opacity: 1 !important;
}

/* --- WIDGETS & ACTIONS --- */
button[data-testid="collapsedControl"] {
    color: #ef4444 !important;
}

section[data-testid="stSidebar"] .stSelectbox, 
section[data-testid="stSidebar"] .stTextInput {
    background-color: transparent !important;
}

/* --- COMPOSANTS DE DONNÉES --- */
div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px !important;
    padding: 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

.project-badge {
    background-color: #f1f5f9;
    color: #64748b;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-left: 15px;
    display: inline-block;
    border: 1px solid #e2e8f0;
}
</style>
"""

def inject_institutional_design():
    st.markdown(INSTITUTIONAL_CSS, unsafe_allow_html=True)

def render_terminal_header():
    """Rendu HTML utilisant les constantes centralisées."""
    # Titre et Badge (Utilise CommonTexts)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <h1 style="margin: 0; font-weight: 700; color: #1e293b;">{CommonTexts.APP_TITLE}</h1>
            <span class="project-badge">{CommonTexts.PROJECT_BADGE}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Note de conformité (Utilise LegalTexts)
    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <p style="font-size: 0.85rem; color: #64748b; font-style: italic; line-height: 1.4; margin: 0;">
                <b>{LegalTexts.COMPLIANCE_TITLE}</b> : {LegalTexts.COMPLIANCE_BODY}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()