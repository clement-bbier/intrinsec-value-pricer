"""
core/models/glass_box.py
Modeles de tracabilite Glass Box.

Ces modeles permettent de documenter chaque etape de calcul
pour une transparence totale envers l'utilisateur.
"""

from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field

from core.models.enums import AuditSeverity


class TraceHypothesis(BaseModel):
    """Hypothese utilisee dans un calcul."""
    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    """Etape de calcul documentee (Glass Box)."""
    step_id: int = 0
    step_key: str = ""
    label: str = ""
    theoretical_formula: str = ""
    hypotheses: List[TraceHypothesis] = Field(default_factory=list)
    numerical_substitution: str = ""
    result: float = 0.0
    unit: str = ""
    interpretation: str = ""


class AuditStep(BaseModel):
    """Etape d'audit avec verdict."""
    step_id: int = 0
    step_key: str = ""
    label: str = ""
    rule_formula: str = ""
    indicator_value: Union[float, str] = 0.0
    threshold_value: Union[float, str, None] = None
    severity: AuditSeverity = AuditSeverity.INFO
    verdict: bool = True
    evidence: str = ""
    description: str = ""
