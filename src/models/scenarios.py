"""
src/models/scenarios.py

DETERMINISTIC SCENARIOS & SOTP MODELS
=====================================
Role: Data structures for sensitivity analysis and Sum-of-the-Parts valuation.
Scope: Bull/Base/Bear variants and multi-segment business unit definitions.
Architecture: Pydantic-based with post-load probability validation.

Style: Numpy docstrings.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from .enums import SOTPMethod
from .glass_box import CalculationStep
from src.config.constants import ModelDefaults
from src.i18n import MODEL_VALIDATION_TEXTS


class ScenarioVariant(BaseModel):
    """
    Represents a specific deterministic sensitivity variant.

    Defines the input parameters for a specific outcome case (e.g., Bull).

    Attributes
    ----------
    label : str
        Name of the scenario (Bull, Base, Bear).
    growth_rate : float, optional
        Scenario-specific Phase 1 growth rate.
    target_fcf_margin : float, optional
        Scenario-specific target FCF margin for convergence models.
    probability : float, default=ModelDefaults.DEFAULT_PROBABILITY
        The statistical weight assigned to this variant.
    """
    label: str
    growth_rate: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    probability: float = ModelDefaults.DEFAULT_PROBABILITY


class ScenarioResult(BaseModel):
    """
    Individual output of a calculated scenario.

    Stores the intrinsic value and effective inputs used for a single case.

    Attributes
    ----------
    label : str
        The applied scenario label.
    intrinsic_value : float
        The fair value per share calculated under this variant.
    probability : float
        The associated probability weight.
    growth_used : float
        The actual growth rate applied by the engine.
    margin_used : float
        The actual FCF margin applied by the engine.
    """
    label: str
    intrinsic_value: float
    probability: float
    growth_used: float
    margin_used: float


class ScenarioSynthesis(BaseModel):
    """
    Synthesis of all sensitivity variants for UI rendering.

    Aggregates results into a single "Expected Value" and identifies extreme bounds.

    Attributes
    ----------
    variants : List[ScenarioResult]
        The collection of results per scenario.
    expected_value : float
        The probability-weighted mean of all variants.
    max_upside : float
        The highest valuation outcome (usually Bull).
    max_downside : float
        The lowest valuation outcome (usually Bear).
    """
    variants: List[ScenarioResult] = Field(default_factory=list)
    expected_value: float = ModelDefaults.DEFAULT_EXPECTED_VALUE
    max_upside: float = ModelDefaults.DEFAULT_MAX_UPSIDE
    max_downside: float = ModelDefaults.DEFAULT_MAX_DOWNSIDE


class ScenarioParameters(BaseModel):
    """
    Deterministic scenario orchestration block.

    Governs the configuration of the Bull/Base/Bear sensitivity analysis.

    Attributes
    ----------
    enabled : bool
        Flag to activate scenario-based valuation.
    bull : ScenarioVariant
        Configuration for the optimistic case.
    base : ScenarioVariant
        Configuration for the central/expected case.
    bear : ScenarioVariant
        Configuration for the pessimistic case.
    """
    enabled: bool = False
    bull: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bull", probability=0.25))
    base: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Base", probability=0.50))
    bear: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bear", probability=0.25))

    @model_validator(mode='after')
    def validate_probabilities(self) -> 'ScenarioParameters':
        """
        Ensures that scenario weights sum to 100% when the engine is enabled.

        Raises
        ------
        ValueError
            If the sum of probabilities is outside the 0.98 - 1.02 range.
        """
        if self.enabled:
            total = self.bull.probability + self.base.probability + self.bear.probability
            if not (0.98 <= total <= 1.02):
                raise ValueError(MODEL_VALIDATION_TEXTS.SCENARIO_PROBABILITIES_SUM_ERROR)
        return self


class BusinessUnit(BaseModel):
    """
    Represents a conglomerate operational segment (SOTP).

    An independent operational unit valued using its own specific logic.

    Attributes
    ----------
    name : str
        The segment identifier (e.g., "Cloud Services").
    enterprise_value : float
        The calculated Enterprise Value for the segment.
    revenue : float, optional
        The segment's specific revenue for attribution checks.
    method : SOTPMethod
        Valuation logic applied (DCF, Multiples, etc.).
    contribution_pct : float, optional
        Relative percentage of the total conglomerate value.
    calculation_trace : List[CalculationStep]
        Granular traceability for the segment's valuation.
    """
    name: str
    enterprise_value: float
    revenue: Optional[float] = None
    method: SOTPMethod = SOTPMethod.DCF
    contribution_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)


class SOTPParameters(BaseModel):
    """
    Sum-of-the-Parts (SOTP) valuation configuration.

    Governs the breakdown of a diversified entity into its parts.

    Attributes
    ----------
    enabled : bool
        Flag to activate SOTP valuation.
    segments : List[BusinessUnit]
        The collection of business segments.
    conglomerate_discount : float
        Percentage discount applied to the sum-of-parts (Holding Discount).
    """
    enabled: bool = False
    segments: List[BusinessUnit] = Field(default_factory=list)
    conglomerate_discount: float = ModelDefaults.DEFAULT_CONGLOMERATE_DISCOUNT