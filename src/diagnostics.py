"""
src/diagnostics.py

DIAGNOSTIC TYPE SYSTEM AND STRUCTURED ERROR MANAGEMENT
======================================================
Role: Defines diagnostic events with pedagogical financial context.
Facilitates analyst understanding of model risks and technical failures.

Architecture: Type-Safe Registry Pattern.
Style: Numpy docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict

# i18n Imports for UI-facing localized strings
from src.i18n import DiagnosticTexts, AuditMessages


class SeverityLevel(Enum):
    """Classification of diagnostic impact on the valuation lifecycle."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DiagnosticDomain(Enum):
    """Categorization of the problem origin for audit routing."""
    CONFIG = "CONFIG"
    ENGINE = "ENGINE"
    DATA = "DATA"
    MODEL = "MODEL"
    PROVIDER = "PROVIDER"
    USER_INPUT = "USER_INPUT"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class FinancialContext:
    """
    Pedagogical financial context explaining parameter risk (ST-4.2).

    Attributes
    ----------
    parameter_name : str
        The localized name of the financial parameter (e.g., "Market Beta").
    current_value : float
        The calculated or input value being diagnosed.
    typical_range : tuple[float, float]
        The normative bounds for this parameter (min, max).
    statistical_risk : str
        Explanation of why the current value is statistically or economically risky.
    recommendation : str
        Localized guidance for the analyst to remediate the risk.
    """
    parameter_name: str
    current_value: float
    typical_range: tuple[float, float]
    statistical_risk: str
    recommendation: str

    def to_human_readable(self) -> str:
        """Converts the context into a localized human-readable paragraph."""
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
    Encapsulates a unique diagnostic event with full institutional lineage.

    Attributes
    ----------
    code : str
        Unique alphanumeric event code (e.g., "MODEL_G_DIVERGENCE").
    severity : SeverityLevel
        Visual and logical severity of the event.
    domain : DiagnosticDomain
        The architecture layer where the event occurred.
    message : str
        The primary analyst-facing message (localized).
    technical_detail : str, optional
        Raw error string or stack trace for development/debugging.
    remediation_hint : str, optional
        Actionable localized advice to solve the issue.
    financial_context : FinancialContext, optional
        Extended financial rationale for institutional auditing.
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
        """Determines if this event prevents the valuation from completing."""
        return self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]

    @property
    def has_financial_context(self) -> bool:
        """Indicates if analytical context is attached."""
        return self.financial_context is not None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the event for JSON/API transmission.

        Explicitly typed to handle nested dictionary structures for
        financial context metadata.
        """
        # Explicitly hint 'result' to prevent the IDE from narrowing
        # the type to 'Dict[str, str | bool]'
        result: Dict[str, Any] = {
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
        Synthesizes a complete pedagogical message for the UI.

        Combines the root diagnostic, financial context, and remediation hint.
        """
        parts = [self.message]
        if self.financial_context:
            parts.append(self.financial_context.to_human_readable())
        if self.remediation_hint:
            parts.append(f"Action suggérée : {self.remediation_hint}")
        return " ".join(parts)


# ==============================================================================
# NORMATIVE EVENT REGISTRY (ST-4.2 Enhanced)
# ==============================================================================

class DiagnosticRegistry:
    """
    Centralized catalog of standardized diagnostic events.

    Maps technical mathematical errors into localized institutional insights.
    """

    @staticmethod
    def model_g_divergence(g: float, wacc: float) -> DiagnosticEvent:
        """Gordon Shapiro convergence error (g >= WACC)."""
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
        """Statistical instability during Monte Carlo draws."""
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
                    "Les résultats ne sont pas statistiquement fiables"
                ),
                recommendation="Réduire les volatilités ou ajuster les bornes de paramètres"
            )
        )

    @staticmethod
    def risk_excessive_growth(g: float) -> DiagnosticEvent:
        """Alert for unrealistic high-growth phase assumptions."""
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
                    "Seules les hypergrowth-tech maintiennent >10% sur 5 ans"
                ),
                recommendation="Vérifier les guidances management et les consensus"
            )
        )

    @staticmethod
    def fcfe_negative_flow(val: float) -> DiagnosticEvent:
        """FCFE model error: cash burn detected."""
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
                    f"Un FCFE négatif ({val:,.0f}) signifie que l'entreprise brûle "
                    "du cash actionnaire structurellement"
                ),
                recommendation="Utiliser le modèle FCFF ou augmenter l'horizon de projection"
            )
        )

    @staticmethod
    def provider_api_failure(provider: str, error: str) -> DiagnosticEvent:
        """External service communication failure."""
        return DiagnosticEvent(
            code="PROVIDER_API_FAILURE",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.PROVIDER,
            message=AuditMessages.PROVIDER_API_FAILURE_MSG.format(provider=provider),
            technical_detail=error,
            remediation_hint=AuditMessages.PROVIDER_API_FAILURE_HINT
        )

    @staticmethod
    def risk_missing_sbc_dilution(sector: str, rate: float) -> DiagnosticEvent:
        """
        Generates a warning when Stock-Based Compensation (SBC) dilution is ignored.

        SBC dilution is a critical factor for Tech and Growth sectors. Failing to
        account for annual share count increases leads to significant intrinsic
        value overestimation.

        Parameters
        ----------
        sector : str
            The industry sector of the company (e.g., 'Technology', 'Software').
        rate : float
            The current annual dilution rate being evaluated (typically 0.0 here).

        Returns
        -------
        DiagnosticEvent
            A structured event containing pedagogical context and remediation hints.
        """
        return DiagnosticEvent(
            code="RISK_MISSING_SBC_DILUTION",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            # Use of i18n keys with dynamic formatting
            message=DiagnosticTexts.RISK_MISSING_SBC_MSG.format(sector=sector),
            remediation_hint=DiagnosticTexts.RISK_MISSING_SBC_HINT,
            financial_context=FinancialContext(
                parameter_name=DiagnosticTexts.PARAM_SBC_LABEL.format(sector=sector),
                current_value=rate,
                typical_range=(0.01, 0.05),
                statistical_risk=DiagnosticTexts.RISK_SBC_STAT_RISK.format(sector=sector),
                recommendation=DiagnosticTexts.RISK_SBC_RECOMMENDATION
            )
        )