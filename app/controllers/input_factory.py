"""
app/controllers/input_factory.py

INPUT FACTORY — UI TO BACKEND BRIDGE
====================================
Role: Assembles the 'ValuationRequest' object from the Session State.
Mechanism: Uses Pydantic introspection (UIKey) to map flat session keys
           to hierarchical backend parameters.
"""

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
            current_price=0.0 # Will be resolved by the Backend/Provider
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
        extension_params = InputFactory._pull_model(ExtensionBundleParameters, prefix=None)

        # 5. Assembly
        full_params = Parameters(
            structure=structure,
            common=common_params,
            strategy=strategy_params,
            extensions=extension_params
        )

        return ValuationRequest(
            mode=state.selected_methodology,
            parameters=full_params
        )

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
