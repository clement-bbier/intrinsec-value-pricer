"""
app/views/components/step_renderer.py
STEP RENDERER COMPONENT
=======================
Role: Visual component to render a single calculation step in the Glass Box.
Focus: Presentation logic only. Uses the rich CalculationStep object directly.
"""

import streamlit as st
from src.models import CalculationStep


def render_calculation_step(index: int, step: CalculationStep) -> None:
    """
    Renders a single atomic calculation step with institutional formatting.

    Layout:
    1. Header: Index - Label (Value)
    2. Body: Formula (LaTeX) + Interpretation + Variable Details

    Parameters
    ----------
    index : int
        The sequence number of the step (e.g., 1, 2, 3).
    step : CalculationStep
        The rich data object containing the result, formulas, and trace.
    """
    # 1. Container Styling (Presentation Layer)
    with st.container():
        # --- Header Row ---
        c1, c2 = st.columns([0.7, 0.3])

        with c1:
            # Use label directly from the backend model
            st.markdown(f"**{index}. {step.label}**")

            # Use interpretation (formerly description) if available
            if step.interpretation:
                st.caption(step.interpretation)

        with c2:
            # Value formatting based on dynamic unit from backend
            val_str = _format_value(step.result, step.unit)
            st.markdown(f"### {val_str}")

        # --- Formula Section ---
        # 1. Theoretical Formula (LaTeX)
        if step.theoretical_formula:
            st.latex(step.theoretical_formula)

        # 2. Variable Details (Inputs)
        # The model uses 'variables_map', not 'inputs'
        if step.variables_map:
            with st.expander("Détails & Variables"):
                # Show the substituted calculation if available
                if step.actual_calculation:
                    st.markdown(f"**Calcul :** `{step.actual_calculation}`")
                    st.divider()

                # List specific variables used in this step
                for symbol, var_info in step.variables_map.items():
                    # Format: "Risk Free Rate (Rf): 4.5%"
                    desc = var_info.description or "N/A"
                    val = var_info.formatted_value
                    st.markdown(f"- **{symbol}** ({desc}) : `{val}`")

        st.divider()


def _format_value(value: float | int | str, unit: str) -> str:
    """Helper to format numerical values based on metadata unit."""
    if not isinstance(value, (int, float)):
        return str(value)

    # Standardize unit strings
    u = unit.lower() if unit else ""

    if u in ["%", "pct", "percent"]:
        return f"{value:.2%}"
    elif u in ["currency", "usd", "eur", "currency/share"]:
        return f"{value:,.2f}"
    elif u in ["ratio", "x", "multiple"]:
        return f"{value:.2f}x"
    elif u in ["million", "m"]:
        return f"{value:,.1f} M"

    return f"{value:,.2f}"