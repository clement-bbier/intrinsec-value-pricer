"""
app/assets/style_system.py

DESIGN SYSTEM — INSTITUTIONAL HIGH-CONTRAST TERMINAL
=====================================================
Role: Centralized CSS and visual structure components.
Theme: Blue/Red high-contrast institutional design.
Style: NumPy docstrings.
"""

import streamlit as st

from src.i18n import CommonTexts, LegalTexts

# ==============================================================================
# 1. DESIGN SYSTEM (HIGH-CONTRAST BLUE/RED THEME)
# ==============================================================================

INSTITUTIONAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* --- BASE & TYPOGRAPHY --- */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Inter', sans-serif !important;
    color: #1e293b;
}
.stApp { background-color: #f8fafc; }

/* --- SIDEBAR : DEEP NAVY (HIGH CONTRAST) --- */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
}

/* Sidebar text contrast (Pure White on Dark Navy) */
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p {
    color: #ffffff !important;
}

/* Sidebar captions */
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] small {
    color: #cbd5e1 !important;
}

/* Sidebar dividers */
section[data-testid="stSidebar"] hr {
    border-top: 1.5px solid rgba(255, 255, 255, 0.25) !important;
    margin: 1.2rem 0 !important;
    opacity: 1 !important;
}

/* Sidebar widget inputs */
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stTextInput {
    background-color: rgba(255, 255, 255, 0.08) !important;
    border-radius: 6px !important;
}

section[data-testid="stSidebar"] .stSlider label div p {
    color: #ffffff !important;
}

/* --- PRIMARY ACTION BUTTON (INSTITUTIONAL RED) --- */
section[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #dc2626 !important;
    border-color: #dc2626 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-color: #b91c1c !important;
    border-color: #b91c1c !important;
}

/* --- SIDEBAR COLLAPSE BUTTON --- */
button[data-testid="collapsedControl"] {
    color: #dc2626 !important;
}

/* --- DATA COMPONENTS (METRIC CARDS — Slate borders, rounded) --- */
div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #94a3b8 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

/* --- FORM SUBMIT BUTTON (Confirm Ticker) --- */
section[data-testid="stSidebar"] .stFormSubmitButton button {
    background-color: #0f172a !important;
    color: #ffffff !important;
    border: 2px solid #94a3b8 !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
    border-color: #dc2626 !important;
}

/* --- PROJECT BADGE --- */
.project-badge {
    background-color: #f1f5f9;
    color: #475569;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-left: 15px;
    display: inline-block;
    border: 1px solid #94a3b8;
}
</style>
"""


def inject_institutional_design():
    """
    Injects the institutional CSS design system into the Streamlit application.

    Must be called at the start of the main application entrypoint.
    """
    st.markdown(INSTITUTIONAL_CSS, unsafe_allow_html=True)


def render_terminal_header():
    """
    Renders the application header with project badge and compliance note.

    Uses centralized i18n constants from CommonTexts and LegalTexts.
    """
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <h1 style="margin: 0; font-weight: 700; color: #1e293b;">{CommonTexts.APP_TITLE}</h1>
            <span class="project-badge">{CommonTexts.PROJECT_BADGE}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

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
