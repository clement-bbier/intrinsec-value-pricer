"""
src/models/valuation.py

VALUATION ENVELOPES — Clean-cut Request and Result containers.
==============================================================
Architecture: V16 (Zero-Redundancy).
Role: Actionable triggers for the Backend.
"""

from __future__ import annotations
from pydantic import BaseModel, Field

from src.models.enums import ValuationMethodology
from src.models.parameters.base_parameter import Parameters
from src.models.results.base_result import Results


class ValuationRequest(BaseModel):
    """
    The formal trigger sent to the Valuation Engine.

    Parameters already contains the Ticker (Pillar 1) and
    individual field sources. This envelope only adds the
    Instruction (Mode).
    """
    mode: ValuationMethodology = Field(..., description="Selected valuation model.")
    parameters: Parameters = Field(
        ...,
        description="The complete bundle containing Identity, Common, Strategy, and Extensions."
    )


class ValuationResult(BaseModel):
    """
    The final output envelope returned by the Engine.
    """
    request: ValuationRequest
    results: Results