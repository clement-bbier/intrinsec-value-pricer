"""
src/domain/models/company.py

Données financières de l'entreprise.

Version : V2.0 — ST-1.2 Type-Safe Resolution
Pattern : Pydantic Model (Value Object)
Style : Numpy Style docstrings

RISQUES FINANCIERS:
- Ces données alimentent tous les modèles de valorisation
- Une erreur de normalisation invalide l'ensemble du calcul

DEPENDANCES CRITIQUES:
- pydantic >= 2.0.0
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from src.config.constants import ModelDefaults


class CompanyFinancials(BaseModel):
    """Contrat de donnees financier unifie."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Identite
    ticker: str
    name: str = "Unknown"
    currency: str
    sector: str = "Unknown"
    industry: str = "Unknown"
    country: str = "Unknown"
    
    # Marche
    current_price: float
    shares_outstanding: float
    beta: float = ModelDefaults.DEFAULT_BETA

    # Bilan
    total_debt: float = ModelDefaults.DEFAULT_TOTAL_DEBT
    cash_and_equivalents: float = ModelDefaults.DEFAULT_CASH_EQUIVALENTS
    minority_interests: float = ModelDefaults.DEFAULT_MINORITY_INTERESTS
    pension_provisions: float = ModelDefaults.DEFAULT_PENSION_PROVISIONS
    book_value: float = ModelDefaults.DEFAULT_BOOK_VALUE
    book_value_per_share: Optional[float] = None

    # Compte de resultat
    revenue_ttm: Optional[float] = None
    ebitda_ttm: Optional[float] = None
    ebit_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    interest_expense: float = ModelDefaults.DEFAULT_INTEREST_EXPENSE
    eps_ttm: Optional[float] = None

    # Flux
    dividend_share: Optional[float] = None
    fcf_last: Optional[float] = None
    fcf_fundamental_smoothed: Optional[float] = None
    net_borrowing_ttm: Optional[float] = None
    capex: Optional[float] = None
    depreciation_and_amortization: Optional[float] = None

    @property
    def market_cap(self) -> float:
        """Capitalisation boursiere."""
        return self.current_price * self.shares_outstanding

    @property
    def net_debt(self) -> float:
        """Dette nette."""
        return self.total_debt - self.cash_and_equivalents

    @property
    def dividends_total_calculated(self) -> float:
        """Dividendes totaux calcules."""
        return (self.dividend_share or 0.0) * self.shares_outstanding

    # Alias pour compatibilite
    @property
    def fcf(self) -> Optional[float]:
        """Alias pour fcf_last."""
        return self.fcf_last

    @property
    def pe_ratio(self) -> Optional[float]:
        """Ratio cours/benefice (P/E)."""
        if (self.eps_ttm is not None and self.eps_ttm > 0 and
            self.current_price is not None and self.current_price > 0):
            return self.current_price / self.eps_ttm
        return None

    @property
    def pb_ratio(self) -> Optional[float]:
        """Ratio cours/valeur comptable (P/B)."""
        if (self.book_value_per_share is not None and self.book_value_per_share > 0 and
            self.current_price is not None and self.current_price > 0):
            return self.current_price / self.book_value_per_share
        return None

    @property
    def ev_ebitda_ratio(self) -> Optional[float]:
        """Ratio valeur entreprise/EBITDA (EV/EBITDA)."""
        if (self.ebitda_ttm is not None and self.ebitda_ttm > 0 and
            self.market_cap is not None and self.market_cap > 0):
            return self.market_cap / self.ebitda_ttm
        return None


