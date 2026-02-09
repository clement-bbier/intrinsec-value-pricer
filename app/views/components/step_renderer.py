"""
app/views/components/step_renderer.py
STEP RENDERER COMPONENT
=======================
Role: Visual component to render a single calculation step in the Glass Box.
Focus: Presentation logic only. Uses Registry for data.
"""

import streamlit as st
from typing import Union
from src.models import CalculationStep
from app.views.components.ui_glass_box_registry import get_step_metadata


def render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Renders a single atomic calculation step with institutional formatting.

    Layout:
    1. Header: Index - Label (Value)
    2. Body: Formula (LaTeX) + Description + Intermediate Values

    Parameters
    ----------
    index : int
        The sequence number of the step (e.g., 1, 2, 3).
    step : CalculationStep
        The data object containing the value, key, and inputs.
    """
    # 1. Fetch Metadata (Data Layer)
    meta = get_step_metadata(step.step_key)

    # 2. Container Styling (Presentation Layer)
    with st.container():
        # --- Header Row ---
        c1, c2 = st.columns([0.7, 0.3])

        with c1:
            st.markdown(f"**{index}. {meta['label']}**")
            if meta['description']:
                st.caption(meta['description'])

        with c2:
            # Value formatting based on unit
            val_str = _format_value(step.value, meta['unit'])
            st.markdown(f"### {val_str}")

        # --- Formula & Details ---
        # Only show formula if valid latex exists and is not N/A
        if meta.get('formula') and meta['formula'] != "N/A":
            st.latex(meta['formula'])

        # Optional: Show input parameters that led to this result
        if hasattr(step, 'inputs') and step.inputs:
            with st.expander("Détails du calcul"):
                st.json(step.inputs)

        st.divider()


def _format_value(value: Union[float, int, str], unit: str) -> str:
    """Helper to format numerical values based on metadata unit."""
    if not isinstance(value, (int, float)):
        return str(value)

    if unit == "%":
        return f"{value:.2%}"
    elif unit == "currency" or unit == "currency/share":
        return f"{value:,.2f}"
    elif unit == "ratio":
        return f"{value:.2f}x"

    return f"{value:,.2f}"