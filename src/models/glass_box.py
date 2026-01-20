"""
Modèles de traçabilité Glass Box.

Ce module définit les structures de données pour la traçabilité
complète des calculs de valorisation, permettant l'audit
et la pédagogie des résultats financiers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union  # Any requis pour TraceHypothesis.value

from pydantic import BaseModel, Field

from .enums import AuditSeverity
from src.config.constants import ModelDefaults


class VariableSource(str, Enum):
    """Source d'une variable utilisée dans un calcul.

    Énumération des origines possibles pour une variable
    dans les calculs de valorisation.
    """

    YAHOO_FINANCE = "Yahoo Finance"
    MANUAL_OVERRIDE = "Surcharge Expert"
    CALCULATED = "Calculé"
    DEFAULT = "Défaut Système"
    MACRO_PROVIDER = "Données Macro"


class VariableInfo(BaseModel):
    """Information détaillée sur une variable utilisée dans un calcul.

    Permet la traçabilité complète de chaque composant d'une formule,
    incluant provenance, valeur et impact des surcharges utilisateur.

    Attributes
    ----------
    symbol : str
        Symbole mathématique de la variable (ex: "WACC", "g", "FCF₀").
    value : float
        Valeur numérique utilisée dans le calcul.
    formatted_value : str, default=""
        Valeur formatée pour affichage (ex: "8.5%", "150.5 M€").
    source : VariableSource, default=VariableSource.CALCULATED
        Provenance de la donnée (Yahoo, Expert, Calculé, etc.).
    description : str, default=""
        Description pédagogique de la variable.
    is_overridden : bool, default=False
        True si l'utilisateur a surchargé la valeur automatique.
    original_value : float, optional
        Valeur automatique originale si surchargée.
    """
    symbol: str
    value: float
    formatted_value: str = ""
    source: VariableSource = VariableSource.CALCULATED
    description: str = ""
    is_overridden: bool = False
    original_value: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        """Génère formatted_value si non fourni."""
        if not self.formatted_value:
            if abs(self.value) < 1:
                self.formatted_value = f"{self.value:.2%}"
            elif abs(self.value) >= 1e9:
                self.formatted_value = f"{self.value/1e9:,.2f} B"
            elif abs(self.value) >= 1e6:
                self.formatted_value = f"{self.value/1e6:,.2f} M"
            else:
                self.formatted_value = f"{self.value:,.2f}"


class TraceHypothesis(BaseModel):
    """Hypothèse utilisée dans un calcul.

    Représente une hypothèse spécifique appliquée lors
    d'une étape de calcul.

    Attributes
    ----------
    name : str
        Nom de l'hypothèse.
    value : Any
        Valeur de l'hypothèse.
    unit : str, default=""
        Unité de la valeur.
    source : str, default="auto"
        Source de l'hypothèse.
    comment : str, optional
        Commentaire additionnel.
    """
    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    """Étape de calcul documentée (Glass Box).

    Représente une formule mathématique appliquée dans le processus
    de valorisation, avec traçabilité complète pour audit et pédagogie.

    Attributes
    ----------
    step_id : int, default=ModelDefaults.DEFAULT_STEP_ID
        Numéro séquentiel de l'étape.
    step_key : str, default=""
        Clé unique pour le registre Glass Box.
    label : str, default=""
        Libellé d'affichage de l'étape.
    theoretical_formula : str, default=""
        Formule LaTeX théorique.
    actual_calculation : str, default=""
        Substitution numérique réelle avec les valeurs utilisées.
    variables_map : Dict[str, VariableInfo], default={}
        Dictionnaire des variables avec provenance et valeur.
    hypotheses : List[TraceHypothesis], default=[]
        Hypothèses associées à l'étape.
    numerical_substitution : str, default=""
        Substitution numérique formatée (legacy).
    result : float, default=ModelDefaults.DEFAULT_RESULT_VALUE
        Résultat numérique de l'étape.
    unit : str, default=""
        Unité du résultat (€, %, x, etc.).
    interpretation : str, default=""
        Interprétation pédagogique du résultat.
    """
    step_id: int = ModelDefaults.DEFAULT_STEP_ID
    step_key: str = ""
    label: str = ""
    theoretical_formula: str = ""
    actual_calculation: str = ""  # ST-2.1: Nouvelle substitution numérique explicite
    variables_map: Dict[str, VariableInfo] = Field(default_factory=dict)  # ST-2.1: Provenance des variables
    hypotheses: List[TraceHypothesis] = Field(default_factory=list)
    numerical_substitution: str = ""  # Legacy, utiliser actual_calculation
    result: float = ModelDefaults.DEFAULT_RESULT_VALUE
    unit: str = ""
    interpretation: str = ""

    def get_variable(self, symbol: str) -> Optional[VariableInfo]:
        """Récupère les informations d'une variable par son symbole.

        Parameters
        ----------
        symbol : str
            Symbole de la variable (ex: "WACC", "g").

        Returns
        -------
        Optional[VariableInfo]
            Information sur la variable ou None si non trouvée.
        """
        return self.variables_map.get(symbol)

    def has_overrides(self) -> bool:
        """Vérifie si des variables ont été surchargées par l'utilisateur.

        Returns
        -------
        bool
            True si au moins une variable a été surchargée.
        """
        return any(v.is_overridden for v in self.variables_map.values())


class AuditStep(BaseModel):
    """Étape d'audit avec verdict.

    Représente une vérification spécifique effectuée pendant
    l'audit d'une valorisation.

    Attributes
    ----------
    step_id : int, default=ModelDefaults.DEFAULT_STEP_ID
        Numéro séquentiel de l'étape d'audit.
    step_key : str, default=""
        Clé unique de l'étape d'audit.
    label : str, default=""
        Libellé d'affichage de l'étape.
    rule_formula : str, default=""
        Formule de la règle d'audit.
    indicator_value : Union[float, str], default=ModelDefaults.DEFAULT_INDICATOR_VALUE
        Valeur de l'indicateur testé.
    threshold_value : Union[float, str, None]
        Valeur seuil de référence.
    severity : AuditSeverity, default=AuditSeverity.INFO
        Niveau de sévérité du verdict.
    verdict : bool, default=True
        Résultat de la vérification (True = succès).
    evidence : str, default=""
        Preuve ou justification du verdict.
    description : str, default=""
        Description détaillée de l'étape.
    """
    step_id: int = ModelDefaults.DEFAULT_STEP_ID
    step_key: str = ""
    label: str = ""
    rule_formula: str = ""
    indicator_value: Union[float, str] = ModelDefaults.DEFAULT_INDICATOR_VALUE
    threshold_value: Union[float, str, None] = None
    severity: AuditSeverity = AuditSeverity.INFO
    verdict: bool = True
    evidence: str = ""
    description: str = ""
