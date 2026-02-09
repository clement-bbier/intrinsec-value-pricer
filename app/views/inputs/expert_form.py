"""
app/views/inputs/expert_form.py
EXPERT FORM ROUTER
==================
Role: Switches between the different valuation input forms based on the selected methodology.
"""

import streamlit as st
from app.state.store import get_state
from src.models.enums import ValuationMethodology

from app.views.inputs.strategies.fcff_standard_view import FCFFStandardTerminalExpert
from app.views.inputs.strategies.fcff_normalized_view import FCFFNormalizedTerminalExpert
from app.views.inputs.strategies.fcff_growth_view import FCFFGrowthTerminalExpert
from app.views.inputs.strategies.fcfe_view import FCFETerminalExpert
from app.views.inputs.strategies.ddm_view import DDMTerminalExpert
from app.views.inputs.strategies.rim_bank_view import RIMBankTerminalExpert
from app.views.inputs.strategies.graham_value_view import GrahamValueTerminalExpert

def render_expert_form():
    """
    Instantiates and renders the correct Strategy View based on AppState.
    """
    state = get_state()
    ticker = state.ticker
    method = state.selected_methodology

    # Factory Logic (Simple Dispatch)
    if method == ValuationMethodology.FCFF_STANDARD:
        view = FCFFStandardTerminalExpert(ticker=ticker)
    elif method == ValuationMethodology.FCFF_NORMALIZED:
        view = FCFFNormalizedTerminalExpert(ticker=ticker)
    elif method == ValuationMethodology.FCFF_GROWTH:
        view = FCFFGrowthTerminalExpert(ticker=ticker)
    elif method == ValuationMethodology.FCFE:
        view = FCFETerminalExpert(ticker=ticker)
    elif method == ValuationMethodology.DDM:
        view = DDMTerminalExpert(ticker=ticker)
    elif method == ValuationMethodology.RIM:
        view = RIMBankTerminalExpert(ticker=ticker)
    elif method == ValuationMethodology.GRAHAM:
        view = GrahamValueTerminalExpert(ticker=ticker)
    else:
        st.error(f"View not implemented for: {method}")
        return

    # Render the view (inputs widgets)
    view.render()