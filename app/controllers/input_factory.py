"""
app/controllers/input_factory.py

INPUT FACTORY — UI TO BACKEND BRIDGE
====================================
Role: Assembles the 'ValuationRequest' object from the Session State.
Mechanism: Uses Pydantic introspection (UIKey) to map flat session keys
           to hierarchical backend parameters.
"""

import logging
from typing import Any, TypeVar, cast

import streamlit as st
from pydantic import BaseModel

from app.state.store import get_state
from src.models.company import Company
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.common import CapitalStructureParameters, CommonParameters, FinancialRatesParameters
from src.models.parameters.input_metadata import UIKey
from src.models.parameters.options import ExtensionBundleParameters
from src.models.parameters.strategies import (
    DDMParameters,
    FCFEParameters,
    FCFFGrowthParameters,
    FCFFNormalizedParameters,
    FCFFStandardParameters,
    GrahamParameters,
    RIMParameters,
    StrategyUnionParameters,
)
from src.models.valuation import ValuationMethodology, ValuationRequest

# Generic Type Variable bound to Pydantic Models
T = TypeVar("T", bound=BaseModel)


class InputFactory:
    """
    Static factory responsible for converting UI State into Backend Contracts.
    """

    @staticmethod
    def build_request() -> ValuationRequest:
        """
        Main entry point. Constructs the full valuation request from current state.

        Returns
        -------
        ValuationRequest
            The fully hydrated request object ready for the Orchestrator.
        """
        state = get_state()

        # 1. Identity (Static)
        # Note: In a real app, this might come from a CompanyProvider cache
        # Here we construct the basic identity from the Sidebar input
        structure = Company(
            ticker=state.ticker,
            current_price=0.0,  # Will be resolved by the Backend/Provider
        )

        # 2. Strategy Parameters (Polymorphic)
        strategy_params = InputFactory._build_strategy_params(state.selected_methodology)

        # 3. Common Parameters (WACC, Bridge)
        # Rates use the strategy prefix so that the UIKey suffix (e.g. "rf")
        # is combined to form the full session key (e.g. "FCFF_STANDARD_rf").
        # Capital structure uses the bridge prefix (e.g. "bridge_FCFF_STANDARD")
        # so the full key becomes "bridge_FCFF_STANDARD_debt", etc.
        mode_prefix = state.selected_methodology.value
        bridge_prefix = f"bridge_{state.selected_methodology.name}"

        rates = InputFactory._pull_model(FinancialRatesParameters, prefix=mode_prefix)
        capital = InputFactory._pull_model(CapitalStructureParameters, prefix=bridge_prefix)
        common_params = CommonParameters(rates=rates, capital=capital)

        # 4. Extensions (Monte Carlo, etc.)
        # Extensions use GLOBAL keys (no prefix) to be consistent across Auto/Expert modes.
        # Pre-process SOTP segments: convert data_editor output to BusinessUnit list
        InputFactory._preprocess_sotp_segments()

        extension_params = InputFactory._pull_model(ExtensionBundleParameters, prefix=None)

        # 5. Assembly
        full_params = Parameters(
            structure=structure, common=common_params, strategy=strategy_params, extensions=extension_params
        )

        return ValuationRequest(mode=state.selected_methodology, parameters=full_params)

    @staticmethod
    def _build_strategy_params(mode: ValuationMethodology) -> StrategyUnionParameters:
        """Route to the correct Parameter model based on the selected mode."""
        state = get_state()

        # Map Enum to Pydantic Class
        # Uses the exact mapping defined in src.valuation.registry but static here for simplicity
        mapping: dict[ValuationMethodology, type[BaseModel]] = {
            ValuationMethodology.FCFF_STANDARD: FCFFStandardParameters,
            ValuationMethodology.FCFF_NORMALIZED: FCFFNormalizedParameters,
            ValuationMethodology.FCFF_GROWTH: FCFFGrowthParameters,
            ValuationMethodology.FCFE: FCFEParameters,
            ValuationMethodology.DDM: DDMParameters,
            ValuationMethodology.RIM: RIMParameters,
            ValuationMethodology.GRAHAM: GrahamParameters,
        }

        model_cls = mapping.get(mode)
        if not model_cls:
            raise ValueError(f"No parameter model found for mode: {mode}")

        # The key prefix (e.g., 'FCFF_STANDARD_') ensures unique session keys
        # per strategy to avoid collisions.
        prefix = mode.value

        # We use 'cast' to tell the type checker: "Trust me, this BaseModel is actually a StrategyUnionParameters"
        strategy = cast(StrategyUnionParameters, InputFactory._pull_model(model_cls, prefix=prefix))

        # Inject global projection_years from Sidebar into projected strategies
        if hasattr(strategy, "projection_years"):
            strategy.projection_years = state.projection_years

        return strategy

    @staticmethod
    def _pull_model(model_cls: type[T], prefix: str | None = None) -> T:
        """
        Generic extractor: Inspects a Pydantic model for UIKey annotations
        and fetches corresponding values from Streamlit Session State.
        """
        extracted_data: dict[str, Any] = {}

        for name, field_info in model_cls.model_fields.items():
            # 1. Recursion for nested models (e.g. Common -> Rates)
            # Check if the field type is a Pydantic model class
            if isinstance(field_info.annotation, type) and issubclass(field_info.annotation, BaseModel):
                extracted_data[name] = InputFactory._pull_model(field_info.annotation, prefix)
                continue

            # 2. Check for UIKey metadata
            # Annotated stores metadata in the 'metadata' attribute of field_info
            ui_meta = next((m for m in field_info.metadata if isinstance(m, UIKey)), None)

            if ui_meta:
                # Construct the session key: {PREFIX}_{SUFFIX} or just {SUFFIX}
                key = f"{prefix}_{ui_meta.suffix}" if prefix else ui_meta.suffix

                if key in st.session_state:
                    raw_val = st.session_state[key]

                    # Ghost Pattern: Only include if value is not neutral
                    # None and 0 are treated as neutral — the Backend/Provider supplies real data
                    if raw_val is not None and raw_val != 0:
                        # Scaling logic is handled by the Model's validator (BaseNormalizedModel)
                        # We pass the raw UI value, Pydantic scales it.
                        extracted_data[name] = raw_val

        return model_cls(**extracted_data)

    @staticmethod
    def _preprocess_sotp_segments() -> None:
        """
        Adapter Pattern: Transforms SOTP data_editor output to BusinessUnit list.

        The UI stores segment data under 'sotp_editor' key (pd.DataFrame from st.data_editor).
        The model expects a list of BusinessUnit objects under 'sotp_segs' key.
        This method bridges the gap without data loss.
        """
        from src.config.constants import UIKeys
        from src.models.parameters.options import BusinessUnit

        editor_key = UIKeys.SOTP_EDITOR
        model_key = UIKeys.SOTP_SEGS

        # Check if SOTP editor data exists in session state
        if editor_key in st.session_state:
            editor_data = st.session_state[editor_key]

            # Convert DataFrame to list of BusinessUnit objects
            # data_editor returns a dict with 'edited_rows' and 'deleted_rows', or a DataFrame
            if editor_data is not None:
                import pandas as pd

                # Robust DataFrame construction handling incomplete/empty rows
                try:
                    if isinstance(editor_data, pd.DataFrame):
                        df = editor_data
                    elif isinstance(editor_data, dict):
                        # Handle both data_editor dict formats: with/without 'data' key
                        if "data" in editor_data:
                            df = pd.DataFrame(editor_data["data"])
                        else:
                            # Normalize dictionary columns to ensure equal lengths
                            # Extract columns and pad with None to match max length
                            if editor_data:
                                max_len = max(
                                    len(v) if isinstance(v, list) else 1 for v in editor_data.values()
                                )
                            else:
                                max_len = 0
                            normalized_data = {}
                            for key, value in editor_data.items():
                                if isinstance(value, list):
                                    # Pad list to max_len with None
                                    normalized_data[key] = value + [None] * (max_len - len(value))
                                else:
                                    # Single value: replicate to max_len
                                    normalized_data[key] = [value] * max_len if max_len > 0 else [value]
                            df = pd.DataFrame(normalized_data) if normalized_data else pd.DataFrame()
                    else:
                        # Fallback: try direct conversion
                        df = pd.DataFrame(editor_data)
                except (ValueError, TypeError, KeyError) as e:
                    # If conversion fails, log and skip gracefully
                    logging.warning(f"[InputFactory] SOTP data conversion failed: {e}. Skipping SOTP segments.")
                    return

                # Filter out empty rows and convert to BusinessUnit objects
                segments = []
                for _, row in df.iterrows():
                    name = row.get("name", "")
                    value = row.get("value")

                    # Only include segments with non-empty name
                    if name and str(name).strip():
                        segments.append(BusinessUnit(
                            name=str(name).strip(),
                            value=float(value) if value is not None else None
                        ))

                # Store the converted list in session state under the expected key
                if segments:
                    st.session_state[model_key] = segments
