"""
app/main.py

APPLICATION ENTRY POINT
=======================
Role: Router and Lifecycle Orchestrator.
Architecture: MVC (Model-View-Controller).
"""

import sys
from pathlib import Path

# Add project root to path ensuring src/ and infra/ are discoverable
_FILE_PATH = Path(__file__).resolve()
_ROOT_PATH = _FILE_PATH.parent.parent
if str(_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(_ROOT_PATH))

import streamlit as st

from app.assets.style_system import inject_institutional_design

# MVC Imports
from app.state.session_manager import SessionManager
from app.state.store import get_state
from app.views.common.sidebar import render_sidebar
from app.views.inputs.auto_form import render_auto_form
from app.views.inputs.expert_form import render_expert_form

# Views Imports
from app.views.results.orchestrator import render_valuation_results

# Configuration of the page must be the first Streamlit command
st.set_page_config(
    page_title="Intrinsic Value Pricer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main() -> None:
    """
    Main application entry point coordinating the session lifecycle
    and high-level routing between input forms and results dashboard.
    """
    # 1. Lifecycle & Assets Initialization
    SessionManager.initialize_session()
    inject_institutional_design()
    state = get_state()

    # 2. Global UI Components
    render_sidebar()

    # 3. Content Routing Logic

    # Priority 1: Critical Error Handling
    if state.error_message:
        st.error(state.error_message)
        if st.button("Dismiss Error"):
            state.error_message = ""
            st.rerun()

    # Priority 2: Results Dashboard (Pillars 0 to 5)
    elif state.last_result:
        # Functional orchestrator renders the multi-pillar tabbed interface
        render_valuation_results(state.last_result)

    # Priority 3: Empty State / Input Forms
    else:
        if state.is_expert_mode:
            render_expert_form()
        else:
            render_auto_form()


if __name__ == "__main__":
    main()
