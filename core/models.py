from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class ValuationMode(str, Enum):
    """
    Modes de valorisation disponibles pour le moteur DCF.
    Énumération technique interne ; l'interface utilisateur mappera ceci à des libellés plus conviviaux.
    """

    SIMPLE_FCFF = "simple_fcff"
    FUNDAMENTAL_FCFF = "fundamental_fcff"
    MARKET_MULTIPLES = "market_multiples"
    ADVANCED_SIMULATION = "advanced_simulation"


@dataclass
class CompanyFinancials:
    """
    Données financières normalisées pour une entreprise.
    Fournies par les data providers (ex: Yahoo).

    Le champ `warnings` permet de remonter à l'interface des messages
    de qualité de données (FCF TTM manquant, dette/cash approximés, etc.).
    """

    ticker: str
    currency: str

    current_price: float
    shares_outstanding: float

    total_debt: float
    cash_and_equivalents: float

    fcf_last: float  # Dernier Flux de Trésorerie Disponible pour la Firme (FCFF) connu
    beta: float      # Bêta de l'action utilisé dans le CAPM

    # Messages de qualité de données (affichables côté UI)
    warnings: List[str] = field(default_factory=list)

    def to_log_dict(self) -> Dict[str, Any]:
        """Retourne une représentation en dictionnaire pour le logging structuré."""
        return {
            "ticker": self.ticker,
            "currency": self.currency,
            "current_price": self.current_price,
            "shares_outstanding": self.shares_outstanding,
            "total_debt": self.total_debt,
            "cash_and_equivalents": self.cash_and_equivalents,
            "fcf_last": self.fcf_last,
            "beta": self.beta,
            "warnings": self.warnings,
        }

    def __repr__(self) -> str:
        return (
            f"CompanyFinancials(ticker='{self.ticker}', currency='{self.currency}', "
            f"price={self.current_price:.2f}, FCF={self.fcf_last:.2e})"
        )


@dataclass
class DCFParameters:
    """
    Paramètres d'entrée pour le modèle DCF.
    Ils contiennent à la fois des inputs macro (taux sans risque) et des hypothèses (taux de croissance).
    """

    # CAPM inputs
    risk_free_rate: float  # Taux sans risque (Rf) (décimal)
    market_risk_premium: float  # Prime de risque du marché (MRP) (décimal)

    # WACC inputs
    cost_of_debt: float  # Coût de la dette (Rd) (décimal)
    tax_rate: float  # Taux d'imposition effectif (décimal)

    # Growth assumptions
    fcf_growth_rate: float  # Taux de croissance annuel des FCF pendant la période de projection (g) (décimal)
    perpetual_growth_rate: float  # Taux de croissance perpétuel (g∞) (décimal)

    projection_years: int  # Nombre d'années de projection (n)

    def to_log_dict(self) -> Dict[str, Any]:
        """Retourne une représentation en dictionnaire pour le logging structuré."""
        return {
            "Rf": self.risk_free_rate,
            "MRP": self.market_risk_premium,
            "Rd": self.cost_of_debt,
            "TaxRate": self.tax_rate,
            "g": self.fcf_growth_rate,
            "g_inf": self.perpetual_growth_rate,
            "Years": self.projection_years,
        }


@dataclass
class DCFResult:
    """
    Résultat complet d'une exécution du modèle DCF.
    """

    # Intermediate WACC components
    wacc: float
    cost_of_equity: float
    after_tax_cost_of_debt: float

    # Cash-flow projections
    projected_fcfs: List[float]
    discount_factors: List[float]

    # Valuation components
    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: float
    enterprise_value: float
    equity_value: float

    # Final result
    intrinsic_value_per_share: float

    def to_log_dict(self) -> Dict[str, Any]:
        """Retourne une représentation en dictionnaire pour le logging structuré."""
        return {
            "wacc": self.wacc,
            "cost_of_equity": self.cost_of_equity,
            "after_tax_cost_of_debt": self.after_tax_cost_of_debt,
            "projected_fcfs": self.projected_fcfs,
            "discount_factors": self.discount_factors,
            "sum_discounted_fcf": self.sum_discounted_fcf,
            "terminal_value": self.terminal_value,
            "discounted_terminal_value": self.discounted_terminal_value,
            "enterprise_value": self.enterprise_value,
            "equity_value": self.equity_value,
            "intrinsic_value_per_share": self.intrinsic_value_per_share,
        }

    def __repr__(self) -> str:
        return (
            f"DCFResult(IV/Share={self.intrinsic_value_per_share:.2f}, WACC={self.wacc:.2%})"
        )