"""
Modèles pour les scénarios et SOTP.

Ce module définit les structures de données pour les analyses
de sensibilité déterministes (scénarios) et la valorisation
par somme des parties (SOTP).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from .enums import SOTPMethod
from .glass_box import CalculationStep
from src.config.constants import ModelDefaults
from src.i18n import MODEL_VALIDATION_TEXTS


class ScenarioVariant(BaseModel):
    """Représente une variante spécifique (Bull, Base ou Bear).

    Définit les paramètres d'un scénario de sensibilité pour
    l'analyse déterministe des valorisations.

    Attributes
    ----------
    label : str
        Nom du scénario (Bull, Base, Bear).
    growth_rate : float, optional
        Taux de croissance spécifique au scénario.
    target_fcf_margin : float, optional
        Marge FCF cible pour le scénario.
    probability : float, default=ModelDefaults.DEFAULT_PROBABILITY
        Probabilité du scénario.
    """
    label: str
    growth_rate: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    probability: float = ModelDefaults.DEFAULT_PROBABILITY


class ScenarioResult(BaseModel):
    """Stocke le résultat individuel d'un scénario calculé.

    Résultat d'une valorisation sous un scénario spécifique,
    incluant la valeur intrinsèque et les paramètres utilisés.

    Attributes
    ----------
    label : str
        Nom du scénario appliqué.
    intrinsic_value : float
        Valeur intrinsèque calculée dans ce scénario.
    probability : float
        Probabilité associée au scénario.
    growth_used : float
        Taux de croissance effectivement utilisé.
    margin_used : float
        Marge FCF effectivement utilisée.
    """
    label: str
    intrinsic_value: float
    probability: float
    growth_used: float
    margin_used: float


class ScenarioSynthesis(BaseModel):
    """Conteneur final pour la restitution UI des scénarios.

    Synthèse agrégée des résultats de scénarios pour
    présentation à l'utilisateur.

    Attributes
    ----------
    variants : List[ScenarioResult], default=[]
        Liste des résultats par scénario.
    expected_value : float, default=ModelDefaults.DEFAULT_EXPECTED_VALUE
        Valeur attendue pondérée par les probabilités.
    max_upside : float, default=ModelDefaults.DEFAULT_MAX_UPSIDE
        Plus haut potentiel de valorisation.
    max_downside : float, default=ModelDefaults.DEFAULT_MAX_DOWNSIDE
        Plus bas potentiel de valorisation.
    """
    variants: List[ScenarioResult] = Field(default_factory=list)
    expected_value: float = ModelDefaults.DEFAULT_EXPECTED_VALUE
    max_upside: float = ModelDefaults.DEFAULT_MAX_UPSIDE
    max_downside: float = ModelDefaults.DEFAULT_MAX_DOWNSIDE


class ScenarioParameters(BaseModel):
    """Segment de pilotage des scénarios déterministes.

    Configuration des analyses de sensibilité déterministes
    avec scénarios Bull/Base/Bear.

    Attributes
    ----------
    enabled : bool, default=False
        Active l'analyse de scénarios.
    bull : ScenarioVariant
        Configuration du scénario haussier.
    base : ScenarioVariant
        Configuration du scénario central.
    bear : ScenarioVariant
        Configuration du scénario baissier.
    """
    enabled: bool = False
    bull: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bull", probability=0.25))
    base: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Base", probability=0.50))
    bear: ScenarioVariant = Field(default_factory=lambda: ScenarioVariant(label="Bear", probability=0.25))

    @model_validator(mode='after')
    def validate_probabilities(self) -> 'ScenarioParameters':
        """Valide que les probabilités des scénarios somment à 1."""
        if self.enabled:
            total = self.bull.probability + self.base.probability + self.bear.probability
            if not (0.98 <= total <= 1.02):
                raise ValueError(MODEL_VALIDATION_TEXTS.SCENARIO_PROBABILITIES_SUM_ERROR)
        return self


class BusinessUnit(BaseModel):
    """Représente un segment d'activité d'un conglomérat (SOTP).

    Segment opérationnel d'une entreprise valorisé
    indépendamment dans l'approche SOTP.

    Attributes
    ----------
    name : str
        Nom du segment d'activité.
    enterprise_value : float
        Valeur d'entreprise du segment.
    revenue : float, optional
        Chiffre d'affaires du segment.
    method : SOTPMethod, default=SOTPMethod.DCF
        Méthode de valorisation utilisée.
    contribution_pct : float, optional
        Contribution relative au conglomérat (%).
    calculation_trace : List[CalculationStep], default=[]
        Trace des calculs pour ce segment.
    """
    name: str
    enterprise_value: float
    revenue: Optional[float] = None
    method: SOTPMethod = SOTPMethod.DCF
    contribution_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)


class SOTPParameters(BaseModel):
    """Configuration de la valorisation par somme des parties (SOTP).

    Paramètres pour la valorisation d'entreprises multi-segment
    en sommant les valeurs de chaque activité.

    Attributes
    ----------
    enabled : bool, default=False
        Active la valorisation SOTP.
    segments : List[BusinessUnit], default=[]
        Liste des segments d'activité à valoriser.
    conglomerate_discount : float, default=ModelDefaults.DEFAULT_CONGLOMERATE_DISCOUNT
        Décote appliquée au conglomérat.
    """
    enabled: bool = False
    segments: List[BusinessUnit] = Field(default_factory=list)
    conglomerate_discount: float = ModelDefaults.DEFAULT_CONGLOMERATE_DISCOUNT
