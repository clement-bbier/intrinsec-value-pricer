"""
src/quant_logger.py

QUANTLOGGER — INSTITUTIONAL STANDARDIZED LOGGING
================================================
Role: Standardized telemetry for valuation events and mathematical audits.
Pattern: Decorator + Structured Logging.
Architecture: ST-4.2 Compliance.

Format:
[DOMAIN][LEVEL] Ticker: XXX | Key: Value | Key: Value

Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
import functools
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, Union
from enum import Enum

# Type variable for preserving function signatures in decorators
F = TypeVar('F', bound=Callable[..., Any])


class LogLevel(Enum):
    """Log severity levels for valuation telemetry."""
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogDomain(Enum):
    """Functional domains for log routing and filtering."""
    VALUATION = "VALUATION"
    DATA = "DATA"
    AUDIT = "AUDIT"
    MONTE_CARLO = "MC"
    PROVIDER = "PROVIDER"
    ENGINE = "ENGINE"


# Configure specialized quant logger
_logger = logging.getLogger("quant")
_logger.setLevel(logging.DEBUG)

# Terminal Handler (Standard Out)
if not _logger.handlers:
    sh = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    _logger.addHandler(sh)


class QuantLogger:
    """
    Institutional logger for high-precision financial events.

    Implements a standardized, machine-readable format:
    [DOMAIN][LEVEL] Ticker: XXX | Field: Value | Field: Value
    """

    @staticmethod
    def _format_message(
        domain: LogDomain,
        level: LogLevel,
        ticker: str,
        **kwargs: Any
    ) -> str:
        """
        Formats a message into the institutional pipe-separated standard.

        Parameters
        ----------
        domain : LogDomain
            Functional domain of the event.
        level : LogLevel
            Event severity.
        ticker : str
            The stock ticker associated with the event.
        **kwargs
            Key-value pairs to include in the structured segment.

        Returns
        -------
        str
            The formatted log string.
        """
        parts = [f"[{domain.value}][{level.value}]", f"Ticker: {ticker}"]

        for key, value in kwargs.items():
            if value is None:
                continue

            # Smart context-aware formatting
            if isinstance(value, float):
                if any(x in key.lower() for x in ["score", "ratio", "accuracy"]):
                    formatted = f"{value:.1f}%"
                elif any(x in key.lower() for x in ["rate", "growth", "spread", "yield"]):
                    formatted = f"{value:.2%}"
                elif abs(value) >= 1e9:
                    formatted = f"{value/1e9:,.2f}B"
                elif abs(value) >= 1e6:
                    formatted = f"{value/1e6:,.2f}M"
                else:
                    formatted = f"{value:,.2f}"
            elif isinstance(value, (datetime, str)):
                formatted = str(value)
            else:
                formatted = str(value)

            # Key normalization (PascalCase for log consistency)
            display_key = "".join(word.title() for word in key.split("_"))
            parts.append(f"{display_key}: {formatted}")

        return " | ".join(parts)

    @classmethod
    def log_success(
        cls,
        ticker: str,
        mode: str,
        iv: float,
        audit_score: Optional[float] = None,
        upside: Optional[float] = None,
        duration_ms: Optional[int] = None,
        **extra: Any
    ) -> None:
        """Logs a successful valuation completion."""
        msg = cls._format_message(
            LogDomain.VALUATION,
            LogLevel.SUCCESS,
            ticker,
            model=mode,
            intrinsic_value=iv,
            audit_score=audit_score,
            upside=upside,
            compute_time=f"{duration_ms}ms" if duration_ms else None,
            **extra
        )
        _logger.info(msg)

    @classmethod
    def log_audit(
        cls,
        ticker: str,
        score: float,
        grade: str,
        passed: int,
        failed: int
    ) -> None:
        """Logs a Pillar 3 audit result summary."""
        msg = cls._format_message(
            LogDomain.AUDIT,
            LogLevel.INFO,
            ticker,
            global_score=score,
            rating=grade,
            checks_passed=passed,
            checks_failed=failed
        )
        _logger.info(msg)

    @classmethod
    def log_degraded_mode(
        cls,
        ticker: str,
        reason: str,
        fallback: str,
        confidence: float = 0.0
    ) -> None:
        """Logs ST-4.1 Degraded Mode activation."""
        msg = cls._format_message(
            LogDomain.PROVIDER,
            LogLevel.WARNING,
            ticker,
            status="DEGRADED_MODE",
            reason=reason,
            fallback_source=fallback,
            confidence_score=confidence
        )
        _logger.warning(msg)

    @classmethod
    def log_error(
        cls,
        ticker: str,
        error: Union[str, Exception],
        domain: LogDomain = LogDomain.ENGINE,
        **context: Any
    ) -> None:
        """Logs a critical engine or data error."""
        error_msg = str(error)
        msg = cls._format_message(
            domain,
            LogLevel.ERROR,
            ticker,
            error=error_msg,
            **context
        )
        _logger.error(msg)


def log_valuation(func: F) -> F:
    """
    Decorator for automated valuation lifecycle telemetry.

    Captures duration, ticker resolution, and success/failure states.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()

        # Ticker resolution logic from request object
        ticker = "N/A"
        if args and hasattr(args[0], 'ticker'):
            ticker = args[0].ticker
        elif 'request' in kwargs and hasattr(kwargs['request'], 'ticker'):
            ticker = kwargs['request'].ticker

        try:
            result = func(*args, **kwargs)

            # Extract metrics if result follows ValuationResult contract
            if hasattr(result, 'intrinsic_value_per_share'):
                duration = int((datetime.now() - start_time).total_seconds() * 1000)
                QuantLogger.log_success(
                    ticker=ticker,
                    mode=result.mode.value if hasattr(result, 'mode') else "UNKNOWN",
                    iv=result.intrinsic_value_per_share,
                    audit_score=result.audit_report.global_score if result.audit_report else None,
                    upside=result.upside_pct,
                    duration_ms=duration
                )

            return result

        except Exception as e:
            QuantLogger.log_error(
                ticker=ticker,
                error=e,
                domain=LogDomain.VALUATION
            )
            raise

    return wrapper