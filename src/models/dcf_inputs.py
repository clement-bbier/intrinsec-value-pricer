"""
Paramètres d'entrée pour les modèles DCF.

Ce module définit les structures de configuration pour les paramètres
utilisés dans les modèles de Discounted Cash Flow (DCF), incluant
les taux, la croissance et les paramètres Monte Carlo.
"""

from __future__ import annotations

from typing import Any, Dict, Optional  # Any requis pour _decimal_guard

from pydantic import BaseModel, Field, field_validator

from .enums import TerminalValueMethod
from .scenarios import ScenarioParameters, SOTPParameters
from src.config.constants import ModelDefaults


def _decimal_guard(v: Any) -> Optional[float]:
    """Convertit les pourcentages en decimales si necessaire."""
    if v is None or v == "":
        return None
    try:
        val = float(v)
        return val / 100.0 if 1.0 < val <= 100.0 else val
    except (ValueError, TypeError):
        return None


class CoreRateParameters(BaseModel):
    """Paramètres de taux financiers.

    Contient les taux d'actualisation essentiels pour les calculs DCF :
    taux sans risque, prime de risque marché, coût de la dette, etc.

    Attributes
    ----------
    risk_free_rate : float, optional
        Taux sans risque.
    risk_free_source : str, default="N/A"
        Source du taux sans risque.
    market_risk_premium : float, optional
        Prime de risque marché.
    corporate_aaa_yield : float, optional
        Rendement obligataire AAA corporate.
    cost_of_debt : float, optional
        Coût de la dette après impôts.
    tax_rate : float, optional
        Taux d'imposition effectif.
    manual_cost_of_equity : float, optional
        Coût des fonds propres manuel.
    wacc_override : float, optional
        WACC forcé (remplace le calcul automatique).
    manual_beta : float, optional
        Bêta manuel (remplace le bêta automatique).
    """
    risk_free_rate: Optional[float] = None
    risk_free_source: str = "N/A"
    market_risk_premium: Optional[float] = None
    corporate_aaa_yield: Optional[float] = None
    cost_of_debt: Optional[float] = None
    tax_rate: Optional[float] = None
    manual_cost_of_equity: Optional[float] = None
    wacc_override: Optional[float] = None
    manual_beta: Optional[float] = None

    @field_validator('risk_free_rate', 'market_risk_premium', 'corporate_aaa_yield',
                     'cost_of_debt', 'tax_rate', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class GrowthParameters(BaseModel):
    """Paramètres de croissance et projections.

    Définit les hypothèses de croissance pour les projections de flux
    et la valorisation terminale.

    Attributes
    ----------
    fcf_growth_rate : float, optional
        Taux de croissance des Free Cash Flows.
    projection_years : int, default=ModelDefaults.DEFAULT_PROJECTION_YEARS
        Nombre d'années de projection explicite.
    high_growth_years : int, default=ModelDefaults.DEFAULT_HIGH_GROWTH_YEARS
        Nombre d'années de croissance élevée.
    terminal_method : TerminalValueMethod, default=TerminalValueMethod.GORDON_GROWTH
        Méthode de calcul de la valeur terminale.
    perpetual_growth_rate : float, optional
        Taux de croissance perpétuelle.
    exit_multiple_value : float, optional
        Multiple de sortie pour la valeur terminale.
    target_equity_weight : float, optional
        Poids cible des fonds propres dans le capital.
    target_debt_weight : float, optional
        Poids cible de la dette dans le capital.
    target_fcf_margin : float, optional
        Marge FCF cible.
    annual_dilution_rate : float, optional
        Taux annuel de dilution.
    manual_fcf_base : float, optional
        Base FCF manuelle.
    manual_stock_price : float, optional
        Prix d'action manuel.
    manual_total_debt : float, optional
        Dette totale manuelle.
    manual_cash : float, optional
        Trésorerie manuelle.
    manual_minority_interests : float, optional
        Intérêts minoritaires manuels.
    manual_pension_provisions : float, optional
        Provisions pour pensions manuelles.
    manual_shares_outstanding : float, optional
        Actions en circulation manuelles.
    manual_book_value : float, optional
        Valeur comptable manuelle.
    manual_net_borrowing : float, optional
        Variation nette d'endettement manuelle.
    manual_dividend_base : float, optional
        Base de dividende manuelle.
    """
    fcf_growth_rate: Optional[float] = None
    projection_years: int = ModelDefaults.DEFAULT_PROJECTION_YEARS
    high_growth_years: int = ModelDefaults.DEFAULT_HIGH_GROWTH_YEARS
    terminal_method: TerminalValueMethod = TerminalValueMethod.GORDON_GROWTH
    perpetual_growth_rate: Optional[float] = None
    exit_multiple_value: Optional[float] = None
    target_equity_weight: Optional[float] = None
    target_debt_weight: Optional[float] = None
    target_fcf_margin: Optional[float] = None
    annual_dilution_rate: Optional[float] = None

    # Surcharges Analyste
    manual_fcf_base: Optional[float] = None
    manual_stock_price: Optional[float] = None
    manual_total_debt: Optional[float] = None
    manual_cash: Optional[float] = None
    manual_minority_interests: Optional[float] = None
    manual_pension_provisions: Optional[float] = None
    manual_shares_outstanding: Optional[float] = None
    manual_book_value: Optional[float] = None
    manual_net_borrowing: Optional[float] = None
    manual_dividend_base: Optional[float] = None

    @field_validator('fcf_growth_rate', 'perpetual_growth_rate', 'annual_dilution_rate', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class MonteCarloConfig(BaseModel):
    """Configuration des simulations Monte Carlo.

    Paramètres pour l'analyse de sensibilité probabiliste des
    valorisations DCF.

    Attributes
    ----------
    enable_monte_carlo : bool, default=False
        Active les simulations Monte Carlo.
    num_simulations : int, default=2000
        Nombre de simulations à effectuer.
    base_flow_volatility : float, optional
        Volatilité de base des flux.
    beta_volatility : float, optional
        Volatilité du bêta.
    growth_volatility : float, optional
        Volatilité du taux de croissance.
    terminal_growth_volatility : float, optional
        Volatilité du taux de croissance terminal.
    correlation_beta_growth : float, default=-0.30
        Corrélation entre bêta et croissance.
    """
    enable_monte_carlo: bool = False
    num_simulations: int = 2000
    base_flow_volatility: Optional[float] = None
    beta_volatility: Optional[float] = None
    growth_volatility: Optional[float] = None
    terminal_growth_volatility: Optional[float] = None
    correlation_beta_growth: float = -0.30

    @field_validator('beta_volatility', 'growth_volatility', 'terminal_growth_volatility', mode='before')
    @classmethod
    def enforce_decimal(cls, v: Any) -> Any:
        return _decimal_guard(v)


class DCFParameters(BaseModel):
    """Conteneur principal des paramètres DCF.

    Structure de configuration complète pour une valorisation DCF,
    regroupant taux, croissance et paramètres stochastiques.

    Attributes
    ----------
    rates : CoreRateParameters
        Paramètres de taux financiers.
    growth : GrowthParameters
        Paramètres de croissance et projections.
    monte_carlo : MonteCarloConfig
        Configuration des simulations Monte Carlo.
    scenarios : ScenarioParameters
        Configuration des scénarios déterministes.
    sotp : SOTPParameters
        Configuration de la valorisation par segments.
    """
    rates: CoreRateParameters = Field(default_factory=CoreRateParameters)
    growth: GrowthParameters = Field(default_factory=GrowthParameters)
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)
    scenarios: ScenarioParameters = Field(default_factory=ScenarioParameters)
    sotp: SOTPParameters = Field(default_factory=SOTPParameters)

    # Alias pour acces rapide
    @property
    def projection_years(self) -> int:
        return self.growth.projection_years

    def normalize_weights(self) -> None:
        """Normalise les poids equity/dette pour sommer à 1.

        Ajuste automatiquement les poids cibles d'equity et dette
        pour qu'ils totalisent 100% du capital.
        """
        w_e = self.growth.target_equity_weight or 0.0
        w_d = self.growth.target_debt_weight or 0.0
        total = w_e + w_d
        if total > 0:
            self.growth.target_equity_weight = w_e / total
            self.growth.target_debt_weight = w_d / total
        else:
            self.growth.target_equity_weight = 1.0
            self.growth.target_debt_weight = 0.0

    @classmethod
    def from_legacy(cls, data: Dict[str, Any]) -> 'DCFParameters':
        """Construit depuis un dictionnaire plat (compatibilité).

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionnaire contenant les paramètres DCF dans un format plat.

        Returns
        -------
        DCFParameters
            Instance configurée avec les paramètres fournis.
        """
        return cls(
            rates=CoreRateParameters(**data),
            growth=GrowthParameters(**data),
            monte_carlo=MonteCarloConfig(**data)
        )
