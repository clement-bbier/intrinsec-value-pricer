"""
infra/data_providers/yahoo_provider.py

FOURNISSEUR DE DONNÉES — YAHOO FINANCE — VERSION V13.0 (ST-4.1 Resilience)
Rôle : Orchestration, acquisition macro localisée, discovery et normalisation des pairs.
Pattern : Provider + Fallback Chain
Style : Numpy docstrings

ST-4.1 : MODE DÉGRADÉ
=====================
Lorsque Yahoo Finance échoue ou renvoie des données aberrantes,
le provider bascule automatiquement sur les multiples sectoriels
avec traçabilité complète pour garantir la transparence.

Financial Impact:
    La résilience API garantit qu'une valorisation est toujours possible,
    même en cas de panne du fournisseur de données externe.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
import streamlit as st
import yfinance as yf
from pydantic import ValidationError

from src.computation.financial_math import (
    calculate_synthetic_cost_of_debt,
    calculate_sustainable_growth
)
from src.exceptions import ExternalServiceError, TickerNotFoundError
from src.domain.models import (
    CompanyFinancials,
    DCFParameters,
    CoreRateParameters,
    GrowthParameters,
    MonteCarloConfig,
    MultiplesData
)
from infra.data_providers.base_provider import DataProvider
from infra.data_providers.yahoo_raw_fetcher import YahooRawFetcher, RawFinancialData
from infra.data_providers.financial_normalizer import FinancialDataNormalizer
from infra.data_providers.extraction_utils import calculate_historical_cagr, safe_api_call
from infra.macro.yahoo_macro_provider import MacroContext, YahooMacroProvider
from infra.ref_data.country_matrix import get_country_context
from infra.ref_data.sector_fallback import get_sector_fallback_with_metadata, SectorFallbackResult
# Migration DT-001/002: Import depuis core.i18n au lieu de app.ui.components
from src.i18n import StrategySources, WorkflowTexts
from src.config import PeerDefaults

logger = logging.getLogger(__name__)


# ============================================================================
# ST-4.1 : CONSTANTES ET TYPES POUR LE MODE DÉGRADÉ
# ============================================================================

@dataclass
class DataProviderStatus:
    """
    État du provider avec traçabilité du mode dégradé (ST-4.1).
    
    Attributes
    ----------
    is_degraded_mode : bool
        True si le provider a dû basculer sur des données de fallback.
    degraded_reason : str
        Raison du passage en mode dégradé.
    fallback_sources : List[str]
        Liste des sources de fallback utilisées.
    confidence_score : float
        Score de confiance global des données (1.0 = données live, 0.7 = fallback).
    """
    is_degraded_mode: bool = False
    degraded_reason: str = ""
    fallback_sources: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    
    def add_fallback(self, source: str) -> None:
        """Ajoute une source de fallback et met à jour le status."""
        self.is_degraded_mode = True
        self.fallback_sources.append(source)
        # Réduire le score de confiance pour chaque fallback
        self.confidence_score = max(0.5, self.confidence_score - 0.15)

class YahooFinanceProvider(DataProvider):
    """
    Orchestrateur de données Yahoo Finance.
    
    Intègre l'intelligence macro par pays, l'arbitrage SGR et la gestion de cohorte (Peers).
    
    ST-4.1 : Implémente le Mode Dégradé avec fallback automatique sur les
    multiples sectoriels en cas d'échec API.
    
    Attributes
    ----------
    macro_provider : YahooMacroProvider
        Fournisseur de données macro (Rf, MRP).
    fetcher : YahooRawFetcher
        Fetcher brut pour les appels Yahoo Finance.
    normalizer : FinancialDataNormalizer
        Normaliseur des données financières.
    last_raw_data : Optional[RawFinancialData]
        Dernières données brutes fetched (pour backtesting).
    status : DataProviderStatus
        État du provider avec traçabilité du mode dégradé (ST-4.1).
    """

    MARKET_SUFFIXES: List[str] = [".PA", ".L", ".DE", ".AS", ".MI", ".MC", ".BR"]
    MAX_RETRY_ATTEMPTS: int = 1
    
    # ST-4.1 : Seuils de validation des données
    MIN_PE_RATIO: float = 1.0
    MAX_PE_RATIO: float = 500.0
    MIN_EV_EBITDA: float = 0.5
    MAX_EV_EBITDA: float = 100.0

    def __init__(self, macro_provider: YahooMacroProvider):
        self.macro_provider = macro_provider
        self.fetcher = YahooRawFetcher()
        self.normalizer = FinancialDataNormalizer()
        self.last_raw_data: Optional[RawFinancialData] = None
        self.status = DataProviderStatus()  # ST-4.1

    # =========================================================================
    # INTERFACE PUBLIQUE (HÉRITÉE DE DATAPROVIDER)
    # =========================================================================

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_company_financials(_self, ticker: str) -> CompanyFinancials:
        normalized_ticker = ticker.upper().strip()
        return _self._fetch_financials_with_fallback(normalized_ticker)

    @st.cache_data(ttl=3600 * 4)
    def get_price_history(_self, ticker: str, period: str = "5y") -> pd.DataFrame:
        return _self.fetcher.fetch_price_history(ticker, period)

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_peer_multiples(_self, ticker: str, manual_peers: Optional[List[str]] = None) -> MultiplesData:
        """
        Orchestration de la cohorte avec limitation stricte et fallback sectoriel (ST-4.1).
        
        Parameters
        ----------
        ticker : str
            Symbole boursier de l'entreprise cible.
        manual_peers : Optional[List[str]]
            Liste manuelle de peers (prioritaire sur auto-discovery).
        
        Returns
        -------
        MultiplesData
            Multiples de valorisation (réels ou fallback sectoriel).
        
        Notes
        -----
        ST-4.1 : En cas d'échec API ou données aberrantes, bascule automatiquement
        sur les multiples sectoriels avec signalétique appropriée.
        
        DT-012: Constante centralisée dans core/config.
        """
        # Constante centralisée (DT-012)
        _MAX_PEERS_ANALYSIS = PeerDefaults.MAX_PEERS_ANALYSIS

        with st.status(WorkflowTexts.STATUS_PEER_DISCOVERY) as status:
            raw_peers = []
            api_failed = False

            try:
                if manual_peers:
                    logger.info(f"[Provider] Utilisation de la cohorte expert pour {ticker}")
                    # --- SÉCURITÉ : Slicing de la liste manuelle ---
                    selected_tickers = manual_peers[:_MAX_PEERS_ANALYSIS]
                    total_peers = len(selected_tickers)

                    for i, p_ticker in enumerate(selected_tickers, 1):
                        # Mise à jour du message de progression (current/total)
                        status.write(WorkflowTexts.STATUS_PEER_FETCHING.format(current=i, total=total_peers))

                        # Appel API sécurisé avec 1 seul retry pour la rapidité
                        p_info = safe_api_call(lambda: yf.Ticker(p_ticker).info, f"PeerInfo/{p_ticker}", 1)
                        if p_info:
                            p_info["symbol"] = p_ticker
                            raw_peers.append(p_info)
                else:
                    # --- AUTO-DISCOVERY : Recherche via l'algorithme Yahoo ---
                    # Le fetcher interne renvoie une liste, on applique le slice ici
                    all_discovered = _self.fetcher.fetch_peer_multiples(ticker)
                    if all_discovered:
                        raw_peers = all_discovered[:_MAX_PEERS_ANALYSIS]
            except Exception as e:
                logger.warning(f"[Provider] Peer API failed for {ticker}: {e}")
                api_failed = True

            # --- ST-4.1 : FALLBACK SECTORIEL ---
            if not raw_peers or api_failed:
                return _self._fallback_to_sector_multiples(ticker, status)

            # Normalisation et calcul des médianes (Rigueur Data Specialist)
            multiples_summary = _self.normalizer.normalize_peers(raw_peers)
            
            # ST-4.1 : Validation des données (détection d'aberrations)
            if not _self._validate_multiples(multiples_summary):
                logger.warning(f"[Provider] Invalid multiples detected for {ticker}, falling back to sector")
                return _self._fallback_to_sector_multiples(ticker, status)

            # --- FINALISATION ---
            # Utilisation du label de succès global
            status.update(label=WorkflowTexts.PEER_SUCCESS, state="complete")

            return multiples_summary
    
    def _validate_multiples(self, multiples: MultiplesData) -> bool:
        """
        Valide les multiples pour détecter les données aberrantes (ST-4.1).
        
        Parameters
        ----------
        multiples : MultiplesData
            Multiples à valider.
        
        Returns
        -------
        bool
            True si les multiples sont valides, False sinon.
        """
        # Vérifier le P/E
        if multiples.median_pe > 0:
            if multiples.median_pe < self.MIN_PE_RATIO or multiples.median_pe > self.MAX_PE_RATIO:
                return False
        
        # Vérifier EV/EBITDA
        if multiples.median_ev_ebitda > 0:
            if multiples.median_ev_ebitda < self.MIN_EV_EBITDA or multiples.median_ev_ebitda > self.MAX_EV_EBITDA:
                return False
        
        return True
    
    def _fallback_to_sector_multiples(self, ticker: str, status: Any) -> MultiplesData:
        """
        Bascule sur les multiples sectoriels en mode dégradé (ST-4.1).
        
        Parameters
        ----------
        ticker : str
            Symbole boursier.
        status : st.status
            Widget de status Streamlit pour mise à jour.
        
        Returns
        -------
        MultiplesData
            Multiples sectoriels de fallback.
        """
        # Récupérer le secteur du ticker
        sector = "default"
        try:
            ticker_info = safe_api_call(lambda: yf.Ticker(ticker).info, f"SectorInfo/{ticker}", 1)
            if ticker_info:
                sector = ticker_info.get("sector", "default")
        except Exception:
            pass
        
        # Récupérer le fallback avec métadonnées
        fallback_result = get_sector_fallback_with_metadata(sector)
        
        # Mettre à jour le status du provider
        self.status.add_fallback(fallback_result.source_description)
        self.status.degraded_reason = f"API peers indisponible pour {ticker}"
        
        # Mise à jour du status UI
        status.update(
            label=f"Mode Dégradé : Multiples sectoriels ({sector})",
            state="complete"
        )
        
        logger.info(
            f"[Provider] Fallback to sector multiples | ticker={ticker} | sector={sector} | "
            f"confidence={fallback_result.confidence_score:.2f}"
        )
        
        return fallback_result.multiples
    
    def is_degraded_mode(self) -> bool:
        """
        Vérifie si le provider est en mode dégradé (ST-4.1).
        
        Returns
        -------
        bool
            True si des données de fallback ont été utilisées.
        """
        return self.status.is_degraded_mode
    
    def get_degraded_mode_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur le mode dégradé pour l'UI (ST-4.1).
        
        Returns
        -------
        Dict[str, Any]
            Informations de traçabilité du mode dégradé.
        """
        return {
            "is_degraded": self.status.is_degraded_mode,
            "reason": self.status.degraded_reason,
            "fallback_sources": self.status.fallback_sources,
            "confidence_score": self.status.confidence_score,
        }

    def get_company_financials_and_parameters(
        self,
        ticker: str,
        projection_years: int
    ) -> Tuple[CompanyFinancials, DCFParameters]:
        """Workflow Auto-Mode : Construit les paramètres avec macro localisée et arbitrage SGR."""
        financials = self.get_company_financials(ticker)
        macro = self._fetch_macro_context(financials)

        # 1. Estimation de la croissance hybride
        growth_hist = self._estimate_dynamic_growth(ticker)

        # 2. Arbitrage SGR
        payout = (financials.dividend_share * financials.shares_outstanding) / financials.net_income_ttm if financials.net_income_ttm and financials.net_income_ttm > 0 else 0.0
        roe = financials.net_income_ttm / financials.book_value if financials.book_value and financials.book_value > 0 else 0.0
        growth_sgr = calculate_sustainable_growth(roe, payout)
        growth_final = max(0.01, min(growth_hist, growth_sgr or 0.05, 0.08))

        # 3. Paramétrage des taux avec traçabilité "Glass Box" (Phase 1 & 2)
        country_data = get_country_context(financials.country)

        params = DCFParameters(
            rates=CoreRateParameters(
                risk_free_rate=macro.risk_free_rate,
                risk_free_source=macro.risk_free_source, #
                market_risk_premium=macro.market_risk_premium,
                corporate_aaa_yield=macro.corporate_aaa_yield,
                cost_of_debt=calculate_synthetic_cost_of_debt(
                    macro.risk_free_rate, financials.ebit_ttm, financials.interest_expense, financials.market_cap
                ),
                tax_rate=float(country_data["tax_rate"])
            ),
            growth=GrowthParameters(
                fcf_growth_rate=growth_final,
                perpetual_growth_rate=macro.perpetual_growth_rate,
                projection_years=projection_years,
                target_equity_weight=financials.market_cap,
                target_debt_weight=financials.total_debt,
                manual_dividend_base=financials.dividend_share
            ),
            monte_carlo=MonteCarloConfig()
        )
        params.normalize_weights()
        return financials, params

    # =========================================================================
    # LOGIQUE INTERNE (PROTECTED)
    # =========================================================================

    def _estimate_dynamic_growth(self, ticker: str) -> float:
        """Estimation CAGR simplifiée avec fallback institutionnel."""
        try:
            # On privilégie le FCF pour la croissance pérenne
            df = safe_api_call(lambda: self.fetcher.fetch_all(ticker).cash_flow, "Hist FCF Growth")
            cagr = calculate_historical_cagr(df, "Free Cash Flow")
            return max(0.01, min(cagr or 0.03, 0.10))
        except Exception:
            return 0.03

    def _fetch_financials_with_fallback(self, ticker: str, _attempt: int = 0) -> CompanyFinancials:
        try:
            result = self._fetch_and_normalize(ticker)
            if result is not None: return result
            return self._attempt_market_suffix_fallback(ticker, _attempt)
        except TickerNotFoundError: raise
        except ValidationError as ve: raise ExternalServiceError(provider="Yahoo/Pydantic", error_detail=str(ve)) from ve
        except Exception as e: raise ExternalServiceError(provider="Yahoo Finance", error_detail=str(e)) from e

    def _fetch_and_normalize(self, ticker: str) -> Optional[CompanyFinancials]:
        self.last_raw_data = self.fetcher.fetch_historical_deep(ticker)
        return self.normalizer.normalize(self.last_raw_data)

    def _attempt_market_suffix_fallback(self, original_ticker: str, current_attempt: int) -> CompanyFinancials:
        if current_attempt >= self.MAX_RETRY_ATTEMPTS or any(original_ticker.upper().endswith(s) for s in self.MARKET_SUFFIXES):
            raise TickerNotFoundError(ticker=original_ticker)
        ticker_with_suffix = f"{original_ticker}.PA"
        try:
            result = self._fetch_and_normalize(ticker_with_suffix)
            if result is not None: return result
        except Exception: pass
        raise TickerNotFoundError(ticker=original_ticker)

    def _fetch_macro_context(self, financials: CompanyFinancials) -> MacroContext:
        """Orchestration de la Phase 2 : Localisation du Rf par pays."""
        try:
            return self.macro_provider.get_macro_context(
                date=datetime.now(),
                currency=financials.currency,
                country_name=financials.country #
            )
        except Exception as e:
            logger.error(f"Echec du MacroContext dynamique pour {financials.country}: {e}")
            country_data = get_country_context(financials.country)
            return MacroContext(
                date=datetime.now(),
                currency=financials.currency,
                risk_free_rate=float(country_data["risk_free_rate"]),
                risk_free_source=StrategySources.MACRO_API_ERROR,
                market_risk_premium=float(country_data["market_risk_premium"]),
                perpetual_growth_rate=float(country_data["inflation_rate"]),
                corporate_aaa_yield=float(country_data["risk_free_rate"] + 0.01)
            )

    def map_raw_to_financials(self, raw: RawFinancialData) -> Optional[CompanyFinancials]:
        """
        Convertit un objet Raw gelé (passé) en modèle financier standard.
        Indispensable pour la boucle de backtesting.
        """
        return self.normalizer.normalize(raw)
