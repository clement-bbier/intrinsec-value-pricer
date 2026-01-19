"""
src/domain/models/glass_box.py

Modèles de traçabilité Glass Box.

Ces modèles permettent de documenter chaque étape de calcul
pour une transparence totale envers l'utilisateur.

Version : V3.0 — ST-2.1 Glass Box Enhancement
Pattern : Pydantic Model (Traceability Domain)
Style : Numpy Style docstrings

Historique:
- V2.0: ST-1.2 Type-Safe Resolution
- V3.0: ST-2.1 actual_calculation + variables_map

RISQUES FINANCIERS:
- La traçabilité garantit l'auditabilité des calculs
- Sans Glass Box, impossible de valider les résultats
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union  # Any requis pour TraceHypothesis.value

from pydantic import BaseModel, Field

from .enums import AuditSeverity
from src.config.constants import ModelDefaults


class VariableSource(str, Enum):
    """Source d'une variable utilisée dans un calcul."""
    YAHOO_FINANCE = "Yahoo Finance"
    MANUAL_OVERRIDE = "Surcharge Expert"
    CALCULATED = "Calculé"
    DEFAULT = "Défaut Système"
    MACRO_PROVIDER = "Données Macro"


class VariableInfo(BaseModel):
    """
    Information détaillée sur une variable utilisée dans un calcul Glass Box.
    
    Permet à l'utilisateur de tracer la provenance de chaque composant
    d'une formule et de comprendre l'impact de ses surcharges.

    Attributes
    ----------
    symbol : str
        Symbole mathématique de la variable (ex: "WACC", "g", "FCF₀").
    value : float
        Valeur numérique utilisée dans le calcul.
    formatted_value : str
        Valeur formatée pour affichage (ex: "8.5%", "150.5 M€").
    source : VariableSource
        Provenance de la donnée (Yahoo, Expert, Calculé, etc.).
    description : str
        Description pédagogique de la variable.
    is_overridden : bool
        True si l'utilisateur a surchargé la valeur automatique.
    original_value : Optional[float]
        Valeur automatique originale si surchargée.

    Financial Impact
    ----------------
    La traçabilité des variables permet à l'utilisateur de comprendre
    exactement quelles hypothèses impactent sa valorisation.
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
    """Hypothèse utilisée dans un calcul."""
    name: str
    value: Any
    unit: str = ""
    source: str = "auto"
    comment: Optional[str] = None


class CalculationStep(BaseModel):
    """
    Étape de calcul documentée (Glass Box).

    Chaque étape représente une formule appliquée dans le processus de valorisation,
    avec sa trace complète pour audit et pédagogie.

    Attributes
    ----------
    step_id : int
        Numéro séquentiel de l'étape.
    step_key : str
        Clé unique pour le registre Glass Box (ex: "WACC_CALC", "TV_GORDON").
    label : str
        Libellé d'affichage de l'étape.
    theoretical_formula : str
        Formule LaTeX théorique (ex: r"WACC = w_e \\times k_e + w_d \\times k_d(1-\\tau)").
    actual_calculation : str
        Substitution numérique réelle avec les valeurs du ticker.
        Ex: "0.75 × 8.5% + 0.25 × 4.2% × (1 - 25%)"
    variables_map : Dict[str, VariableInfo]
        Dictionnaire des variables avec leur provenance et valeur.
        Permet le drill-down sur chaque composant.
    hypotheses : List[TraceHypothesis]
        Hypothèses associées à l'étape (legacy, pour compatibilité).
    numerical_substitution : str
        Substitution numérique formatée (legacy, remplacé par actual_calculation).
    result : float
        Résultat numérique de l'étape.
    unit : str
        Unité du résultat (€, %, x, etc.).
    interpretation : str
        Interprétation pédagogique du résultat.

    Financial Impact
    ----------------
    Chaque CalculationStep est un point d'audit critique.
    La transparence totale permet de valider les hypothèses utilisées.

    Examples
    --------
    >>> step = CalculationStep(
    ...     step_id=1,
    ...     step_key="WACC_CALC",
    ...     label="Coût Moyen Pondéré du Capital",
    ...     theoretical_formula=r"WACC = w_e \\times k_e + w_d \\times k_d(1-\\tau)",
    ...     actual_calculation="0.75 × 8.5% + 0.25 × 4.2% × (1 - 25%)",
    ...     variables_map={
    ...         "w_e": VariableInfo(symbol="w_e", value=0.75, source=VariableSource.YAHOO_FINANCE),
    ...         "k_e": VariableInfo(symbol="k_e", value=0.085, source=VariableSource.CALCULATED),
    ...     },
    ...     result=0.0717,
    ...     unit="%"
    ... )
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
        """
        Récupère les informations d'une variable par son symbole.

        Args
        ----
        symbol : str
            Symbole de la variable (ex: "WACC", "g").

        Returns
        -------
        Optional[VariableInfo]
            Information sur la variable ou None si non trouvée.
        """
        return self.variables_map.get(symbol)

    def has_overrides(self) -> bool:
        """
        Vérifie si des variables ont été surchargées par l'utilisateur.

        Returns
        -------
        bool
            True si au moins une variable a été surchargée.
        """
        return any(v.is_overridden for v in self.variables_map.values())


class AuditStep(BaseModel):
    """Etape d'audit avec verdict."""
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
