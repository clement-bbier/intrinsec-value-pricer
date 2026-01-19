"""
src/quant_logger.py

QUANTLOGGER — Logging Institutionnel Standardisé

Version : V1.0 — ST-4.2
Pattern : Decorator + Structured Logging
Style : Numpy docstrings

ST-4.2 : STANDARDISATION DU LOG
================================
Format institutionnel uniforme pour tous les événements de valorisation :
[VALUATION][SUCCESS] Ticker: AAPL | Model: FCFF_STANDARD | IV: 185.20 | AuditScore: 88.5%

Financial Impact:
    Les logs structurés permettent l'analyse post-hoc des valorisations
    et facilitent l'audit des décisions d'investissement.

Usage:
    from src.quant_logger import QuantLogger, log_valuation
    
    # Via le décorateur
    @log_valuation
    def run_valuation(request, financials, params):
        ...
    
    # Via le logger directement
    QuantLogger.log_success(ticker="AAPL", mode="FCFF_STANDARD", iv=185.20, audit_score=88.5)
"""

from __future__ import annotations

import logging
import functools
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, Dict
from enum import Enum

# Type variable pour les décorateurs
F = TypeVar('F', bound=Callable[..., Any])


class LogLevel(Enum):
    """Niveaux de log pour les événements de valorisation."""
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogDomain(Enum):
    """Domaines fonctionnels pour le routage des logs."""
    VALUATION = "VALUATION"
    DATA = "DATA"
    AUDIT = "AUDIT"
    MONTE_CARLO = "MC"
    PROVIDER = "PROVIDER"


# Configuration du logger racine pour le module
_logger = logging.getLogger("quant")
_logger.setLevel(logging.DEBUG)


class QuantLogger:
    """
    Logger institutionnel pour les événements de valorisation.
    
    Implémente un format standardisé pour tous les logs :
    [DOMAIN][LEVEL] Ticker: XXX | Key1: Val1 | Key2: Val2
    
    Examples
    --------
    >>> QuantLogger.log_success(
    ...     ticker="AAPL",
    ...     mode="FCFF_STANDARD",
    ...     iv=185.20,
    ...     audit_score=88.5
    ... )
    [VALUATION][SUCCESS] Ticker: AAPL | Model: FCFF_STANDARD | IV: 185.20 | AuditScore: 88.5%
    
    >>> QuantLogger.log_warning(
    ...     ticker="MSFT",
    ...     message="Mode dégradé activé",
    ...     reason="API failure"
    ... )
    [DATA][WARNING] Ticker: MSFT | Mode dégradé activé | Reason: API failure
    """
    
    @staticmethod
    def _format_message(
        domain: LogDomain,
        level: LogLevel,
        ticker: str,
        **kwargs: Any
    ) -> str:
        """
        Formate un message de log selon le standard institutionnel.
        
        Parameters
        ----------
        domain : LogDomain
            Domaine fonctionnel.
        level : LogLevel
            Niveau de log.
        ticker : str
            Symbole boursier.
        **kwargs
            Paramètres additionnels à inclure.
        
        Returns
        -------
        str
            Message formaté.
        """
        parts = [f"[{domain.value}][{level.value}]", f"Ticker: {ticker}"]
        
        # Formatage des paramètres avec types intelligents
        for key, value in kwargs.items():
            if value is None:
                continue
            
            # Formatage contextuel
            if isinstance(value, float):
                if "score" in key.lower() or "ratio" in key.lower():
                    formatted = f"{value:.1f}%"
                elif "rate" in key.lower() or "growth" in key.lower():
                    formatted = f"{value:.2%}"
                elif abs(value) >= 1e9:
                    formatted = f"{value/1e9:,.2f}B"
                elif abs(value) >= 1e6:
                    formatted = f"{value/1e6:,.2f}M"
                else:
                    formatted = f"{value:,.2f}"
            else:
                formatted = str(value)
            
            # CamelCase pour les clés
            display_key = key.replace("_", " ").title().replace(" ", "")
            parts.append(f"{display_key}: {formatted}")
        
        return " | ".join(parts)
    
    @classmethod
    def log_success(
        cls,
        ticker: str,
        mode: str,
        iv: float,
        audit_score: Optional[float] = None,
        market_price: Optional[float] = None,
        upside: Optional[float] = None,
        **extra: Any
    ) -> None:
        """
        Log un événement de valorisation réussie.
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        mode : str
            Mode de valorisation (ex: "FCFF_STANDARD").
        iv : float
            Valeur intrinsèque par action.
        audit_score : float, optional
            Score d'audit (0-100).
        market_price : float, optional
            Prix de marché actuel.
        upside : float, optional
            Potentiel haussier (%).
        **extra
            Paramètres additionnels.
        """
        msg = cls._format_message(
            LogDomain.VALUATION,
            LogLevel.SUCCESS,
            ticker,
            model=mode,
            iv=iv,
            audit_score=audit_score,
            market_price=market_price,
            upside=upside,
            **extra
        )
        _logger.info(msg)
    
    @classmethod
    def log_warning(
        cls,
        ticker: str,
        message: str,
        domain: LogDomain = LogDomain.DATA,
        **context: Any
    ) -> None:
        """
        Log un avertissement.
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        message : str
            Message d'avertissement.
        domain : LogDomain
            Domaine concerné.
        **context
            Contexte additionnel.
        """
        msg = cls._format_message(
            domain,
            LogLevel.WARNING,
            ticker,
            warning=message,
            **context
        )
        _logger.warning(msg)
    
    @classmethod
    def log_error(
        cls,
        ticker: str,
        error: str,
        domain: LogDomain = LogDomain.VALUATION,
        **context: Any
    ) -> None:
        """
        Log une erreur.
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        error : str
            Message d'erreur.
        domain : LogDomain
            Domaine concerné.
        **context
            Contexte additionnel.
        """
        msg = cls._format_message(
            domain,
            LogLevel.ERROR,
            ticker,
            error=error,
            **context
        )
        _logger.error(msg)
    
    @classmethod
    def log_monte_carlo(
        cls,
        ticker: str,
        simulations: int,
        valid_ratio: float,
        p50: float,
        p10: float,
        p90: float
    ) -> None:
        """
        Log les résultats d'une simulation Monte Carlo.
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        simulations : int
            Nombre de simulations.
        valid_ratio : float
            Ratio de simulations valides.
        p50 : float
            Médiane (percentile 50).
        p10, p90 : float
            Bornes de l'intervalle de confiance.
        """
        msg = cls._format_message(
            LogDomain.MONTE_CARLO,
            LogLevel.INFO,
            ticker,
            simulations=simulations,
            valid_ratio=valid_ratio,
            p50=p50,
            range_80=f"{p10:.2f}-{p90:.2f}"
        )
        _logger.info(msg)
    
    @classmethod
    def log_audit(
        cls,
        ticker: str,
        score: float,
        passed: int,
        failed: int,
        grade: str
    ) -> None:
        """
        Log le résultat d'un audit.
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        score : float
            Score global (0-100).
        passed : int
            Nombre de tests réussis.
        failed : int
            Nombre de tests échoués.
        grade : str
            Grade final (A, B, C, D, F).
        """
        msg = cls._format_message(
            LogDomain.AUDIT,
            LogLevel.INFO,
            ticker,
            score=score,
            passed=passed,
            failed=failed,
            grade=grade
        )
        _logger.info(msg)
    
    @classmethod
    def log_degraded_mode(
        cls,
        ticker: str,
        reason: str,
        fallback_source: str,
        confidence: float
    ) -> None:
        """
        Log l'activation du mode dégradé (ST-4.1).
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        reason : str
            Raison du passage en mode dégradé.
        fallback_source : str
            Source de fallback utilisée.
        confidence : float
            Score de confiance des données.
        """
        msg = cls._format_message(
            LogDomain.PROVIDER,
            LogLevel.WARNING,
            ticker,
            degraded_mode="ACTIVE",
            reason=reason,
            source=fallback_source,
            confidence_score=confidence
        )
        _logger.warning(msg)


def log_valuation(func: F) -> F:
    """
    Décorateur pour logger automatiquement les valorisations.
    
    Parameters
    ----------
    func : Callable
        Fonction de valorisation à décorer.
    
    Returns
    -------
    Callable
        Fonction décorée avec logging automatique.
    
    Examples
    --------
    >>> @log_valuation
    ... def run_valuation(request, financials, params):
    ...     # ... logique de valorisation ...
    ...     return result
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        # Extraction du ticker depuis les arguments
        ticker = "UNKNOWN"
        if args:
            first_arg = args[0]
            if hasattr(first_arg, 'ticker'):
                ticker = first_arg.ticker
        
        try:
            result = func(*args, **kwargs)
            
            # Log du succès
            if hasattr(result, 'intrinsic_value_per_share'):
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                QuantLogger.log_success(
                    ticker=ticker,
                    mode=result.mode.value if hasattr(result, 'mode') else "UNKNOWN",
                    iv=result.intrinsic_value_per_share,
                    audit_score=result.audit_report.global_score if hasattr(result, 'audit_report') and result.audit_report else None,
                    market_price=result.market_price if hasattr(result, 'market_price') else None,
                    duration_ms=int(duration_ms)
                )
            
            return result
            
        except Exception as e:
            QuantLogger.log_error(
                ticker=ticker,
                error=str(e),
                domain=LogDomain.VALUATION
            )
            raise
    
    return wrapper  # type: ignore
