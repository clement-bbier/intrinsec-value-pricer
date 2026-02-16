"""
app/views/inputs/auto_form.py

STANDARD MODE — ONBOARDING & LANDING VIEW
=========================================
Role: Educational landing page for the Standard Mode.
Responsibilities:
  - Explain the application's purpose.
  - Detail methodologies and analysis levels.
  - Preview expected results.
  - Provide a reactive summary of the current configuration.
"""

import streamlit as st

from src.i18n import OnboardingTexts


def render_auto_form():
    """
    Renders the comprehensive onboarding.
    """
    st.markdown(f"# {OnboardingTexts.APP_TITLE}")
    st.markdown(
        f"""
            <div style="margin-top: -15px; margin-bottom: 20px;">
                <p style="font-size: 0.8rem; color: #64748b; font-style: italic; line-height: 1.4;">
                    <strong>{OnboardingTexts.COMPLIANCE_TITLE}</strong> : {OnboardingTexts.COMPLIANCE_BODY}
                </p>
            </div>
            """,
        unsafe_allow_html=True
    )
    st.divider()

    # INTRO
    st.subheader(OnboardingTexts.TITLE_INTRO)
    st.markdown(OnboardingTexts.INTRO_ONBOARDING)
    st.divider()

    # MODELS DESCRIPTION
    st.subheader(OnboardingTexts.MODEL_SECTION_TITLE)
    st.markdown(OnboardingTexts.MODELS_EXPLORER)
    st.divider()

    # RESULTS DESCRIPTION
    st.subheader(OnboardingTexts.RESULTS_SECTION_TITLE)

    col1, col2 = st.columns(2)

    with col1:
        with st.expander(OnboardingTexts.PILLAR_1_TITLE, expanded=True):
            st.markdown(OnboardingTexts.PILLAR_1_DESC)

        with st.expander(OnboardingTexts.PILLAR_2_TITLE, expanded=True):
            st.markdown(OnboardingTexts.PILLAR_2_DESC)

    with col2:
        with st.expander(OnboardingTexts.PILLAR_3_TITLE, expanded=True):
            st.markdown(OnboardingTexts.PILLAR_3_DESC)

        with st.expander(OnboardingTexts.PILLAR_4_TITLE, expanded=False):
            st.markdown(OnboardingTexts.PILLAR_4_DESC)

        with st.expander(OnboardingTexts.PILLAR_5_TITLE, expanded=False):
            st.markdown(OnboardingTexts.PILLAR_5_DESC)
