"""
core/exceptions.py
Exceptions typées transportant des diagnostics structurés.
Version V6.7 — Alignement institutionnel et pilotage par Registre.
"""

import logging
from typing import Optional, Any
from core.diagnostics import (
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    DiagnosticRegistry
)

logger = logging.getLogger(__name__)


class ValuationException(Exception):
    """
    Exception racine standardisée.
    Elle transporte un DiagnosticEvent structuré au lieu d'un simple message texte.
    """

    def __init__(self, diagnostic: DiagnosticEvent):
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)
        # Log automatique structuré pour la traçabilité serveur
        logger.error(
            f"[{diagnostic.code}] {diagnostic.message} "
            f"(Severity: {diagnostic.severity.value}, Domain: {diagnostic.domain.value})"
        )


# ==============================================================================
# 1. ADAPTATEURS DE DONNÉES ET INFRASTRUCTURE
# ==============================================================================

class TickerNotFoundError(ValuationException):
    """Levée quand le symbole boursier est inconnu du fournisseur."""
    def __init__(self, ticker: str):
        event = DiagnosticEvent(
            code="DATA_TICKER_NOT_FOUND",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.DATA,
            message=f"Le ticker '{ticker}' est introuvable sur Yahoo Finance.",
            technical_detail=f"Symbole reçu : {ticker}",
            remediation_hint="Vérifiez l'orthographe (ex: 'AIR.PA' pour Airbus) ou si l'entreprise est radiée."
        )
        super().__init__(event)


class DataMissingError(ValuationException):
    """Utilisé quand un champ précis manque (ex: Pas de Beta, Pas de FCF 2023)."""
    def __init__(self, missing_field: str, ticker: str, year: Optional[int] = None):
        if year:
            msg = f"Donnée manquante pour {ticker} : '{missing_field}' pour l'année {year}."
        else:
            msg = f"Donnée fondamentale manquante pour {ticker} : '{missing_field}' est vide ou invalide."

        event = DiagnosticEvent(
            code="DATA_MISSING_FIELD",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.DATA,
            message=msg,
            remediation_hint="Cette entreprise ne publie peut-être pas cette donnée, ou l'historique est trop court."
        )
        super().__init__(event)


class ExternalServiceError(ValuationException):
    """Levée en cas d'échec de l'API ou de la connexion réseau."""
    def __init__(self, provider: str, error_detail: str):
        event = DiagnosticEvent(
            code="PROVIDER_CONNECTION_FAIL",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.PROVIDER,
            message=f"Échec de connexion au fournisseur {provider}.",
            technical_detail=error_detail,
            remediation_hint="Vérifiez votre connexion internet. L'API est peut-être temporairement indisponible."
        )
        super().__init__(event)


# ==============================================================================
# 2. ERREURS DE MODÉLISATION ET CALCULS (AUDIT-GRADE)
# ==============================================================================

class ModelIncoherenceError(ValuationException):
    """Utilisé pour les incohérences logiques détectées par l'auditeur."""
    def __init__(self, model_name: str, issue: str, values_context: str):
        event = DiagnosticEvent(
            code="MODEL_LOGIC_ERROR",
            severity=SeverityLevel.WARNING,
            domain=DiagnosticDomain.MODEL,
            message=f"Incohérence dans le modèle {model_name} : {issue}",
            technical_detail=f"Valeurs : {values_context}",
            remediation_hint="Vérifiez vos hypothèses de croissance ou de taux d'actualisation."
        )
        super().__init__(event)


class ModelDivergenceError(ValuationException):
    """
    Erreur critique g >= WACC.
    Délègue la création du message au Registre pour inclure les données chiffrées.
    """
    def __init__(self, g: float, wacc: float):
        # Utilisation du DiagnosticRegistry pour une cohérence parfaite avec l'UI
        super().__init__(DiagnosticRegistry.MODEL_G_DIVERGENCE(g, wacc))


class MonteCarloInstabilityError(ValuationException):
    """
    Instabilité statistique des simulations.
    Explique à l'utilisateur pourquoi la simulation a été rejetée.
    """
    def __init__(self, valid_ratio: float, threshold: float):
        super().__init__(DiagnosticRegistry.MODEL_MC_INSTABILITY(valid_ratio, threshold))


class CalculationError(ValuationException):
    """
    Erreur générique de calcul.
    Maintenue pour la compatibilité avec les calculs simples non encore typés.
    """
    def __init__(self, message: str):
        event = DiagnosticEvent(
            code="CALCULATION_GENERIC_ERROR",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=message,
            remediation_hint="Vérifiez les données d'entrée ou les paramètres du modèle dans le Terminal Expert."
        )
        super().__init__(event)