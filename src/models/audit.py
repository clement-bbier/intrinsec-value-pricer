"""
src/domain/models/audit.py

Modèles pour le système d'audit.

Version : V2.0 — ST-1.2 Type-Safe Resolution
Pattern : Pydantic Model (Audit Domain)
Style : Numpy Style docstrings

RISQUES FINANCIERS:
- L'audit guide la confiance dans les résultats
- Un score mal calculé peut masquer des risques critiques
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .enums import AuditPillar, InputSource
from .glass_box import AuditStep
from src.config.constants import ModelDefaults


class AuditPillarScore(BaseModel):
    """Score d'un pilier d'audit."""
    pillar: AuditPillar
    score: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR  # 0.0
    weight: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR  # 0.0
    contribution: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR  # 0.0
    diagnostics: List[str] = Field(default_factory=list)
    check_count: int = 0


class AuditScoreBreakdown(BaseModel):
    """Decomposition du score par pilier."""
    pillars: Dict[AuditPillar, AuditPillarScore]
    aggregation_formula: str
    total_score: float = 0.0


class AuditLog(BaseModel):
    """Entree de log d'audit."""
    category: str
    severity: str
    message: str
    penalty: float


class AuditReport(BaseModel):
    """Rapport d'audit complet."""
    global_score: float
    rating: str
    audit_mode: Union[InputSource, str]
    audit_depth: int = 0
    audit_coverage: float = 0.0
    audit_steps: List[AuditStep] = Field(default_factory=list)
    pillar_breakdown: Optional[AuditScoreBreakdown] = None
    logs: List[AuditLog] = Field(default_factory=list)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    block_monte_carlo: bool = False
    critical_warning: bool = False


class ValuationOutputContract(BaseModel):
    """Contrat de sortie pour validation."""
    model_config = ConfigDict(frozen=True)
    
    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_intrinsic_value: bool
    has_audit: bool

    def is_valid(self) -> bool:
        """Verifie si le contrat est satisfait."""
        return all([self.has_params, self.has_intrinsic_value, self.has_audit])
