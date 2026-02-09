"""
app/main.py

APPLICATION ENTRY POINT
=======================
Role: Router and Lifecycle Orchestrator.
Architecture: MVC (Model-View-Controller).
Logic:
  1. Initialize Session/State.
  2. Render Sidebar (Inputs).
  3. Route Content:
     IF results exist -> Show Results Dashboard.
     ELSE -> Show Input Form (Auto or Expert).
"""

import sys
from pathlib import Path

# Add project root to path ensuring src/ and infra/ are discoverable
_FILE_PATH = Path(__file__).resolve()
_ROOT_PATH = _FILE_PATH.parent.parent
if str(_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(_ROOT_PATH))

import streamlit as st

# MVC Imports
from app.state.session_manager import SessionManager
from app.state.store import get_state
from app.assets.style_system import inject_institutional_design
from app.views.common.sidebar import render_sidebar

# Views Imports
from app.views.results.orchestrator import ResultTabOrchestrator
from app.views.inputs.expert_form import render_expert_form
from app.views.inputs.auto_form import render_auto_form

# Configuration of the page must be the first Streamlit command
st.set_page_config(
    page_title="Intrinsic Value Pricer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # 1. Lifecycle & Assets
    SessionManager.initialize_session()
    inject_institutional_design()
    state = get_state()

    # 2. Global Components
    render_sidebar()

    # 3. Content Routing
    # Priority 1: Show Error if any
    if state.error_message:
        st.error(state.error_message)
        if st.button("Dismiss Error"):
            SessionManager.set_error(None)
            st.rerun()

    # Priority 2: Show Results if available
    elif state.last_result:
        # The Orchestrator handles the Tabs (Proof, Audit, etc.)
        orchestrator = ResultTabOrchestrator()
        orchestrator.render(state.last_result)

        # Optional: Add a "Back to Inputs" button logic if needed,
        # but usually modifying the sidebar is enough.

    # Priority 3: Show Input Form (Empty State)
    else:
        if state.is_expert_mode:
            render_expert_form()
        else:
            render_auto_form()

if __name__ == "__main__":
    main()