"""
Données financières de l'entreprise.

Ce module définit les structures de données pour les informations
financières de base d'une entreprise, utilisées par tous les moteurs
de valorisation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from src.config.constants import ModelDefaults


class CompanyFinancials(BaseModel):
    """Données financières unifiées d'une entreprise.

    Conteneur principal pour toutes les données financières nécessaires
    aux calculs de valorisation. Centralise les informations de marché,
    bilan, compte de résultat et flux de trésorerie.

    Attributes
    ----------
    ticker : str
        Symbole boursier de l'entreprise.
    name : str, default="Unknown"
        Nom de l'entreprise.
    currency : str
        Devise des données financières.
    sector : str, default="Unknown"
        Secteur d'activité.
    industry : str, default="Unknown"
        Industrie spécifique.
    country : str, default="Unknown"
        Pays d'origine.
    current_price : float
        Prix actuel de l'action.
    shares_outstanding : float
        Nombre d'actions en circulation.
    beta : float, default=ModelDefaults.DEFAULT_BETA
        Coefficient bêta (risque systématique).
    total_debt : float, default=ModelDefaults.DEFAULT_TOTAL_DEBT
        Dettes totales.
    cash_and_equivalents : float, default=ModelDefaults.DEFAULT_CASH_EQUIVALENTS
        Trésorerie et équivalents.
    minority_interests : float, default=ModelDefaults.DEFAULT_MINORITY_INTERESTS
        Intérêts minoritaires.
    pension_provisions : float, default=ModelDefaults.DEFAULT_PENSION_PROVISIONS
        Provisions pour pensions.
    book_value : float, default=ModelDefaults.DEFAULT_BOOK_VALUE
        Valeur comptable totale.
    book_value_per_share : float, optional
        Valeur comptable par action.
    revenue_ttm : float, optional
        Chiffre d'affaires des 12 derniers mois.
    ebitda_ttm : float, optional
        EBITDA des 12 derniers mois.
    ebit_ttm : float, optional
        EBIT des 12 derniers mois.
    net_income_ttm : float, optional
        Bénéfice net des 12 derniers mois.
    interest_expense : float, default=ModelDefaults.DEFAULT_INTEREST_EXPENSE
        Charges d'intérêts.
    eps_ttm : float, optional
        Bénéfice par action des 12 derniers mois.
    dividend_share : float, optional
        Dividende par action.
    fcf_last : float, optional
        Free Cash Flow de la dernière période.
    fcf_fundamental_smoothed : float, optional
        FCF fondamental lissé.
    net_borrowing_ttm : float, optional
        Variation nette de l'endettement sur 12 mois.
    capex : float, optional
        Dépenses d'investissement (CAPEX).
    depreciation_and_amortization : float, optional
        Dotations aux amortissements.
    """
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
        """Capitalisation boursière.

        Returns
        -------
        float
            Produit du prix actuel par le nombre d'actions en circulation.
        """
        return self.current_price * self.shares_outstanding

    @property
    def net_debt(self) -> float:
        """Dette nette.

        Returns
        -------
        float
            Dettes totales moins trésorerie et équivalents.
        """
        return self.total_debt - self.cash_and_equivalents

    @property
    def dividends_total_calculated(self) -> float:
        """Dividendes totaux calculés.

        Returns
        -------
        float
            Dividende par action multiplié par le nombre d'actions en circulation.
        """
        return (self.dividend_share or 0.0) * self.shares_outstanding

    # Alias pour compatibilite
    @property
    def fcf(self) -> Optional[float]:
        """Alias pour fcf_last.

        Returns
        -------
        Optional[float]
            Valeur du dernier Free Cash Flow disponible.
        """
        return self.fcf_last

    @property
    def pe_ratio(self) -> Optional[float]:
        """Ratio cours/bénéfice (P/E).

        Returns
        -------
        Optional[float]
            Rapport entre le prix actuel et le bénéfice par action.
            None si les données ne sont pas disponibles ou négatives.
        """
        if (self.eps_ttm is not None and self.eps_ttm > 0 and
            self.current_price is not None and self.current_price > 0):
            return self.current_price / self.eps_ttm
        return None

    @property
    def pb_ratio(self) -> Optional[float]:
        """Ratio cours/valeur comptable (P/B).

        Returns
        -------
        Optional[float]
            Rapport entre le prix actuel et la valeur comptable par action.
            None si les données ne sont pas disponibles ou négatives.
        """
        if (self.book_value_per_share is not None and self.book_value_per_share > 0 and
            self.current_price is not None and self.current_price > 0):
            return self.current_price / self.book_value_per_share
        return None

    @property
    def ev_ebitda_ratio(self) -> Optional[float]:
        """Ratio valeur entreprise/EBITDA (EV/EBITDA).

        Returns
        -------
        Optional[float]
            Rapport entre la valeur d'entreprise et l'EBITDA.
            None si les données ne sont pas disponibles ou négatives.
        """
        if (self.ebitda_ttm is not None and self.ebitda_ttm > 0 and
            self.market_cap is not None and self.market_cap > 0):
            return self.market_cap / self.ebitda_ttm
        return None


