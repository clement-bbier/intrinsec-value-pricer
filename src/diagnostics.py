"""
src/diagnostics.py

Système de types pour le diagnostic et la gestion d'erreurs structurée.

Version : V3.0 — ST-4.2 Financial Pedagogy
Pattern : Value Objects (Diagnostic Domain)
Style : Numpy Style docstrings

ST-4.2 : PÉDAGOGIE DES ERREURS
==============================
Les erreurs mathématiques brutes sont traduites en diagnostics métier
compréhensibles par les analystes non-techniques.

Exemple : "Math Error" devient "Erreur : La croissance g (5%) est 
supérieure au WACC (4.5%), le modèle ne peut converger".

Audit-Grade : Ajout du registre normatif des événements financiers.

RISQUES FINANCIERS:
- Les diagnostics guident la compréhension des erreurs
- Un diagnostic imprécis peut masquer des problèmes critiques
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, List, Dict  # Any requis pour DiagnosticEvent.context
# DT-001/002: Import depuis core.i18n
from src.i18n import DiagnosticTexts


class SeverityLevel(Enum):
    """Niveau de gravité du diagnostic."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DiagnosticDomain(Enum):
    """Domaine d'origine du problème."""
    DATA = "DATA"
    MODEL = "MODEL"
    PROVIDER = "PROVIDER"
    USER_INPUT = "USER_INPUT"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class FinancialContext:
    """
    Contexte financier expliquant pourquoi un paramètre est risqué (ST-4.2).
    
    Attributes
    ----------
    parameter_name : str
        Nom du paramètre concerné (ex: "Beta", "Growth Rate").
    current_value : float
        Valeur actuelle du paramètre.
    typical_range : tuple[float, float]
        Plage typique du paramètre (min, max).
    statistical_risk : str
        Explication du risque statistique.
    recommendation : str
        Recommandation pour l'analyste.
    
    Examples
    --------
    >>> ctx = FinancialContext(
    ...     parameter_name="Beta",
    ...     current_value=3.5,
    ...     typical_range=(0.5, 2.0),
    ...     statistical_risk="Beta supérieur à 3.0 implique une volatilité extrême",
    ...     recommendation="Vérifier la source ou utiliser un proxy sectoriel"
    ... )
    """
    parameter_name: str
    current_value: float
    typical_range: tuple
    statistical_risk: str
    recommendation: str
    
    def to_human_readable(self) -> str:
        """Convertit le contexte en texte lisible."""
        range_str = f"{self.typical_range[0]:.2f} - {self.typical_range[1]:.2f}"
        return (
            f"Le paramètre {self.parameter_name} ({self.current_value:.2f}) "
            f"est hors de la plage typique ({range_str}). "
            f"{self.statistical_risk}. "
            f"Recommandation : {self.recommendation}."
        )


@dataclass(frozen=True)
class DiagnosticEvent:
    """
    Représente un événement de diagnostic unique avec contexte financier.
    
    ST-4.2 : Enrichi avec financial_context pour la pédagogie.
    
    Attributes
    ----------
    code : str
        Code unique de l'événement (ex: "MODEL_G_DIVERGENCE").
    severity : SeverityLevel
        Niveau de gravité.
    domain : DiagnosticDomain
        Domaine d'origine du problème.
    message : str
        Message principal compréhensible par un analyste.
    technical_detail : Optional[str]
        Détail technique pour le debugging.
    remediation_hint : Optional[str]
        Conseil de remédiation.
    financial_context : Optional[FinancialContext]
        Contexte financier expliquant le risque (ST-4.2).
    """
    code: str
    severity: SeverityLevel
    domain: DiagnosticDomain
    message: str
    technical_detail: Optional[str] = None
    remediation_hint: Optional[str] = None
    financial_context: Optional[FinancialContext] = None

    @property
    def is_blocking(self) -> bool:
        """Retourne Vrai si ce diagnostic empêche le calcul de continuer."""
        return self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]
    
    @property
    def has_financial_context(self) -> bool:
        """Vérifie si un contexte financier est disponible."""
        return self.financial_context is not None

    def to_dict(self) -> dict:
        result = {
            "code": self.code,
            "severity": self.severity.value,
            "domain": self.domain.value,
            "message": self.message,
            "is_blocking": self.is_blocking
        }
        if self.financial_context:
            result["financial_context"] = {
                "parameter": self.financial_context.parameter_name,
                "value": self.financial_context.current_value,
                "typical_range": list(self.financial_context.typical_range),
                "risk": self.financial_context.statistical_risk,
            }
        return result
    
    def get_pedagogical_message(self) -> str:
        """
        Retourne un message pédagogique complet pour l'UI (ST-4.2).
        
        Returns
        -------
        str
            Message combinant le diagnostic et le contexte financier.
        """
        parts = [self.message]
        if self.financial_context:
            parts.append(self.financial_context.to_human_readable())
        if self.remediation_hint:
            parts.append(f"Action suggérée : {self.remediation_hint}")
        return " ".join(parts)

# ==============================================================================
# REGISTRE NORMATIF DES ÉVÉNEMENTS (ST-4.2 Enhanced)
# ==============================================================================

class DiagnosticRegistry:
    """
    Catalogue centralisé des événements utilisant DiagnosticTexts.
    
    ST-4.2 : Enrichi avec financial_context pour la pédagogie.
    Chaque événement fournit maintenant un contexte financier explicatif.
    """

    @staticmethod
    def model_g_divergence(g: float, wacc: float) -> DiagnosticEvent:
        """
        Erreur de convergence Gordon Shapiro (ST-4.2 Enhanced).
        
        Traduit "Math Error" en explication compréhensible :
        "La croissance g est supérieure au WACC, le modèle ne peut converger."
        """
        return DiagnosticEvent(
            code="MODEL_G_DIVERGENCE",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_G_DIV_MSG.format(g=g, wacc=wacc),
            remediation_hint=DiagnosticTexts.MODEL_G_DIV_HINT,
            financial_context=FinancialContext(
                parameter_name="Taux de croissance perpétuelle (g)",
                current_value=g,
                typical_range=(0.01, 0.03),
                statistical_risk=(
                    f"Le modèle de Gordon requiert g < WACC. Avec g={g:.2%} et WACC={wacc:.2%}, "
                    "la formule TV = FCF/(WACC-g) produit une valeur négative ou infinie"
                ),
                recommendation="Réduire g en dessous de 3% ou utiliser la méthode Exit Multiple"
            )
        )

    @staticmethod
    def model_mc_instability(valid_ratio: float, threshold: float) -> DiagnosticEvent:
        """Instabilité statistique lors des simulations Monte Carlo."""
        return DiagnosticEvent(
            code="MODEL_MC_INSTABILITY",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_MC_INST_MSG.format(valid_ratio=valid_ratio, threshold=threshold),
            remediation_hint=DiagnosticTexts.MODEL_MC_INST_HINT,
            financial_context=FinancialContext(
                parameter_name="Ratio de simulations valides",
                current_value=valid_ratio,
                typical_range=(0.90, 1.00),
                statistical_risk=(
                    f"Seulement {valid_ratio:.0%} des simulations ont convergé. "
                    "Les résultats Monte Carlo ne sont pas statistiquement fiables"
                ),
                recommendation="Réduire les volatilités ou ajuster les bornes de paramètres"
            )
        )

    @staticmethod
    def data_missing_core_metric(metric_name: str) -> DiagnosticEvent:
        """Donnée critique manquante empêchant la valorisation."""
        return DiagnosticEvent(
            code="DATA_MISSING_CORE_METRIC",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message=DiagnosticTexts.DATA_MISSING_CORE_MSG.format(metric_name=metric_name),
            remediation_hint=DiagnosticTexts.DATA_MISSING_CORE_HINT
        )

    @staticmethod
    def risk_excessive_growth(g: float) -> DiagnosticEvent:
        """Alerte sur une hypothèse de croissance irréaliste (ST-4.2 Enhanced)."""
        return DiagnosticEvent(
            code="RISK_EXCESSIVE_GROWTH",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.USER_INPUT,
            message=DiagnosticTexts.RISK_EXCESSIVE_GROWTH_MSG.format(g=g),
            remediation_hint=DiagnosticTexts.RISK_EXCESSIVE_GROWTH_HINT,
            financial_context=FinancialContext(
                parameter_name="Taux de croissance des flux",
                current_value=g,
                typical_range=(0.02, 0.08),
                statistical_risk=(
                    f"Un taux de croissance de {g:.1%} est rarement soutenable à long terme. "
                    "Seules les entreprises en hypercroissance maintiennent >10% sur 5 ans"
                ),
                recommendation="Vérifier avec les guidances du management et les consensus analystes"
            )
        )

    @staticmethod
    def data_negative_beta(beta: float) -> DiagnosticEvent:
        """Détection d'un Beta inhabituel (ST-4.2 Enhanced)."""
        return DiagnosticEvent(
            code="DATA_NEGATIVE_BETA",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.DATA,
            message=DiagnosticTexts.DATA_NEGATIVE_BETA_MSG.format(beta=beta),
            remediation_hint=DiagnosticTexts.DATA_NEGATIVE_BETA_HINT,
            financial_context=FinancialContext(
                parameter_name="Beta",
                current_value=beta,
                typical_range=(0.5, 2.0),
                statistical_risk=(
                    f"Un Beta de {beta:.2f} est statistiquement inhabituel. "
                    "Les Betas < 0 ou > 3 indiquent souvent des données de marché peu fiables"
                ),
                recommendation="Utiliser le Beta sectoriel moyen ou vérifier la période de calcul"
            )
        )

    @staticmethod
    def risk_extreme_beta(beta: float) -> DiagnosticEvent:
        """
        Alerte sur un Beta statistiquement extrême (ST-4.2 New).
        
        Parameters
        ----------
        beta : float
            Valeur du Beta.
        
        Returns
        -------
        DiagnosticEvent
            Événement avec contexte financier explicatif.
        """
        return DiagnosticEvent(
            code="RISK_EXTREME_BETA",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.DATA,
            message=f"Le Beta ({beta:.2f}) est statistiquement extrême et peut fausser le coût du capital.",
            remediation_hint="Envisager un Beta sectoriel ou ajuster manuellement.",
            financial_context=FinancialContext(
                parameter_name="Beta",
                current_value=beta,
                typical_range=(0.5, 2.0),
                statistical_risk=(
                    f"Un Beta > 3.0 implique une volatilité 3x supérieure au marché. "
                    "Cela impacte drastiquement le coût des fonds propres (Ke)"
                ),
                recommendation="Vérifier la liquidité du titre et considérer un ajustement Blume"
            )
        )

    @staticmethod
    def fcfe_negative_flow(val: float) -> DiagnosticEvent:
        """Erreur : Le flux FCFE calculé est négatif."""
        return DiagnosticEvent(
            code="FCFE_NEGATIVE_FLOW",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.FCFE_NEGATIVE_MSG.format(val=val),
            remediation_hint=DiagnosticTexts.FCFE_NEGATIVE_HINT,
            financial_context=FinancialContext(
                parameter_name="Free Cash Flow to Equity",
                current_value=val,
                typical_range=(0.0, float('inf')),
                statistical_risk=(
                    f"Un FCFE négatif ({val:,.0f}) signifie que l'entreprise consomme "
                    "plus de cash qu'elle n'en génère pour les actionnaires"
                ),
                recommendation="Utiliser le modèle FCFF ou ajuster l'horizon de projection"
            )
        )

    @staticmethod
    def ddm_payout_excessive(payout: float) -> DiagnosticEvent:
        """Avertissement : Le Payout Ratio dépasse les bénéfices."""
        return DiagnosticEvent(
            code="DDM_PAYOUT_EXCESSIVE",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.DDM_PAYOUT_MSG.format(payout=payout),
            remediation_hint=DiagnosticTexts.DDM_PAYOUT_HINT,
            financial_context=FinancialContext(
                parameter_name="Payout Ratio",
                current_value=payout,
                typical_range=(0.20, 0.80),
                statistical_risk=(
                    f"Un payout de {payout:.0%} est insoutenable à long terme. "
                    "L'entreprise puise dans ses réserves pour maintenir le dividende"
                ),
                recommendation="Normaliser le payout sur la moyenne historique ou sectorielle"
            )
        )

    @staticmethod
    def model_sgr_divergence(g: float, sgr: float) -> DiagnosticEvent:
        """Avertissement : Croissance > Sustainable Growth Rate."""
        return DiagnosticEvent(
            code="MODEL_SGR_DIVERGENCE",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=DiagnosticTexts.MODEL_SGR_DIV_MSG.format(g=g, sgr=sgr),
            remediation_hint=DiagnosticTexts.MODEL_SGR_DIV_HINT,
            financial_context=FinancialContext(
                parameter_name="Sustainable Growth Rate",
                current_value=g,
                typical_range=(0.0, sgr),
                statistical_risk=(
                    f"La croissance projetée ({g:.1%}) dépasse le SGR ({sgr:.1%}). "
                    "Cela implique une augmentation de capital ou de dette"
                ),
                recommendation="Aligner g sur le SGR ou modéliser explicitement le financement"
            )
        )
    
    @staticmethod
    def provider_api_failure(provider: str, error: str) -> DiagnosticEvent:
        """
        Erreur de communication avec un fournisseur externe (ST-4.2 New).
        
        Parameters
        ----------
        provider : str
            Nom du fournisseur (ex: "Yahoo Finance").
        error : str
            Message d'erreur technique.
        
        Returns
        -------
        DiagnosticEvent
            Événement avec contexte pour le mode dégradé.
        """
        return DiagnosticEvent(
            code="PROVIDER_API_FAILURE",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.PROVIDER,
            message=f"Le fournisseur {provider} n'a pas répondu. Utilisation des données de secours.",
            technical_detail=error,
            remediation_hint="Les données de fallback sectoriel sont utilisées automatiquement."
        )
