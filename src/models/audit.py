"""
Modèles pour le système d'audit.

Ce module définit les structures de données pour l'audit et
la validation des valorisations financières, incluant les scores
par pilier et les rapports détaillés.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .enums import AuditPillar, InputSource
from .glass_box import AuditStep
from src.config.constants import ModelDefaults


class AuditPillarScore(BaseModel):
    """Score d'un pilier d'audit.

    Résultat d'évaluation d'un pilier spécifique de l'audit,
    incluant score, poids et diagnostics détaillés.

    Attributes
    ----------
    pillar : AuditPillar
        Pilier d'audit évalué.
    score : float, default=ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
        Score obtenu pour ce pilier (0.0 par défaut).
    weight : float, default=ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
        Poids du pilier dans le score global (0.0 par défaut).
    contribution : float, default=ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR
        Contribution pondérée au score global (0.0 par défaut).
    diagnostics : List[str], default=[]
        Liste des problèmes diagnostiqués.
    check_count : int, default=0
        Nombre de vérifications effectuées.
    """
    pillar: AuditPillar
    score: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR  # 0.0
    weight: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR  # 0.0
    contribution: float = ModelDefaults.DEFAULT_MEAN_ABSOLUTE_ERROR  # 0.0
    diagnostics: List[str] = Field(default_factory=list)
    check_count: int = 0


class AuditScoreBreakdown(BaseModel):
    """Décomposition du score par pilier.

    Ventilation détaillée du score d'audit global selon
    les différents piliers d'évaluation.

    Attributes
    ----------
    pillars : Dict[AuditPillar, AuditPillarScore]
        Scores détaillés par pilier.
    aggregation_formula : str
        Formule d'agrégation utilisée.
    total_score : float, default=0.0
        Score global agrégé.
    """
    pillars: Dict[AuditPillar, AuditPillarScore]
    aggregation_formula: str
    total_score: float = 0.0


class AuditLog(BaseModel):
    """Entrée de log d'audit.

    Enregistrement détaillé d'un événement d'audit,
    incluant sévérité et pénalité appliquée.

    Attributes
    ----------
    category : str
        Catégorie de l'événement.
    severity : str
        Niveau de sévérité.
    message : str
        Message descriptif.
    penalty : float
        Pénalité appliquée au score.
    """
    category: str
    severity: str
    message: str
    penalty: float


class AuditReport(BaseModel):
    """Rapport d'audit complet.

    Rapport d'audit exhaustif incluant score global,
    ventilation par pilier et logs détaillés.

    Attributes
    ----------
    global_score : float
        Score d'audit global (0-100).
    rating : str
        Notation qualitative (A+, A, B+, etc.).
    audit_mode : Union[InputSource, str]
        Mode d'audit utilisé.
    audit_depth : int, default=0
        Profondeur de l'audit effectué.
    audit_coverage : float, default=0.0
        Couverture des vérifications (%).
    audit_steps : List[AuditStep], default=[]
        Étapes détaillées de l'audit.
    pillar_breakdown : AuditScoreBreakdown, optional
        Ventilation par pilier d'audit.
    logs : List[AuditLog], default=[]
        Logs détaillés des vérifications.
    breakdown : Dict[str, float], default={}
        Décomposition par catégories.
    block_monte_carlo : bool, default=False
        Bloque l'utilisation de Monte Carlo si True.
    critical_warning : bool, default=False
        Présence d'avertissements critiques.
    """
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
    """Contrat de sortie pour validation.

    Spécification des éléments disponibles dans un résultat
    de valorisation, utilisée pour la validation et l'audit.

    Attributes
    ----------
    has_params : bool
        Paramètres de calcul disponibles.
    has_projection : bool
        Projections de flux disponibles.
    has_terminal_value : bool
        Valeur terminale calculée.
    has_intrinsic_value : bool
        Valeur intrinsèque disponible.
    has_audit : bool
        Rapport d'audit disponible.
    """
    model_config = ConfigDict(frozen=True)
    
    has_params: bool
    has_projection: bool
    has_terminal_value: bool
    has_intrinsic_value: bool
    has_audit: bool

    def is_valid(self) -> bool:
        """Vérifie si le contrat est satisfait.

        Returns
        -------
        bool
            True si les éléments minimum sont présents.
        """
        return all([self.has_params, self.has_intrinsic_value, self.has_audit])
