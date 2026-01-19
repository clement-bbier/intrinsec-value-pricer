"""
core/models/scenarios.py
Modeles pour les scenarios et SOTP.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from .enums import SOTPMethod
from core.models.glass_box import CalculationStep
from core.config.constants import ModelDefaults


class ScenarioVariant(BaseModel):
    """Represente une variante specifique (Bull, Base ou Bear)."""
    label: str
    growth_rate: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    probability: float = ModelDefaults.DEFAULT_PROBABILITY


class ScenarioResult(BaseModel):
    """Stocke le resultat individuel d'un scenario calcule."""
    label: str
    intrinsic_value: float
    probability: float
    growth_used: float
    margin_used: float


class ScenarioSynthesis(BaseModel):
    """Conteneur final pour la restitution UI des scenarios."""
    variants: List[ScenarioResult] = Field(default_factory=list)
    expected_value: float = ModelDefaults.DEFAULT_EXPECTED_VALUE
    max_upside: float = ModelDefaults.DEFAULT_MAX_UPSIDE
    max_downside: float = ModelDefaults.DEFAULT_MAX_DOWNSIDE


class ScenarioParameters(BaseModel):
    """Segment de pilotage des scenarios deterministes."""
    enabled: bool = False
    bull: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bull", probability=0.25))
    base: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Base", probability=0.50))
    bear: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bear", probability=0.25))

    @model_validator(mode='after')
    def validate_probabilities(self) -> 'ScenarioParameters':
        if self.enabled:
            total = self.bull.probability + self.base.probability + self.bear.probability
            if not (0.98 <= total <= 1.02):
                raise ValueError("La somme des probabilites (Bull+Base+Bear) doit etre egale a 1.0.")
        return self


class BusinessUnit(BaseModel):
    """Represente un segment d'activite d'un conglomerat (SOTP)."""
    name: str
    enterprise_value: float
    revenue: Optional[float] = None
    method: SOTPMethod = SOTPMethod.DCF
    contribution_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)


class SOTPParameters(BaseModel):
    """Configuration de la valorisation par somme des parties (SOTP)."""
    enabled: bool = False
    segments: List[BusinessUnit] = Field(default_factory=list)
    conglomerate_discount: float = ModelDefaults.DEFAULT_CONGLOMERATE_DISCOUNT
