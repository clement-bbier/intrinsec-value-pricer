from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ValuationMode(str, Enum):
    """
    Modes de valorisation disponibles pour le moteur DCF.
    """
    SIMPLE_FCFF = "simple_fcff"
    FUNDAMENTAL_FCFF = "fundamental_fcff"
    MONTE_CARLO = "monte_carlo"


@dataclass
class CompanyFinancials:
    """
    Données financières normalisées pour une entreprise.
    Contient à la fois les données brutes (Bilan), les données retraitées (FCF lissé)
    et le rapport d'audit de fiabilité.
    """

    ticker: str
    currency: str

    # Identité Sectorielle
    sector: str = "Unknown"
    industry: str = "Unknown"

    # Données Marché
    current_price: float = 0.0
    shares_outstanding: float = 0.0

    # Données Bilan & Dette
    total_debt: float = 0.0
    cash_and_equivalents: float = 0.0

    # Charges d'intérêts (Critique pour le WACC Synthétique)
    interest_expense: float = 0.0

    # Données de Flux (Cash Flow)
    fcf_last: float = 0.0  # Pour Méthode 1 (TTM)

    # Paramètres de Risque Actuels
    beta: float = 1.0

    # FCFF fondamental lissé (Moyenne Pondérée Time-Anchored)
    fcf_fundamental_smoothed: Optional[float] = None

    # Résultat du Reverse DCF (Implied Growth)
    implied_growth_rate: Optional[float] = None

    # Journal de bord technique
    warnings: List[str] = field(default_factory=list)

    # --- NOUVEAUX CHAMPS AUDIT (Bulletin de Notes) ---
    audit_score: float = 100.0  # Ex: 75.0
    audit_rating: str = "Non Audité"  # Ex: "FIABLE (A)"

    # Pour l'UI (Tableau riche) : Liste de dicts {"category", "penalty", "reason", "context"}
    audit_details: List[Dict] = field(default_factory=list)

    # Pour le Terminal (Log brut formaté)
    audit_logs: List[str] = field(default_factory=list)

    def to_log_dict(self) -> Dict[str, Any]:
        """Retourne une représentation en dictionnaire pour les logs structurés."""
        return {
            "ticker": self.ticker,
            "price": self.current_price,
            "debt": self.total_debt,
            "cash": self.cash_and_equivalents,
            "interest": self.interest_expense,
            "fcf_ttm": self.fcf_last,
            "fcf_fundamental": self.fcf_fundamental_smoothed,
            "implied_g": self.implied_growth_rate,
            "audit_score": self.audit_score,
            "audit_rating": self.audit_rating,
            "warnings_count": len(self.warnings),
        }

    def __repr__(self) -> str:
        return (
            f"CompanyFinancials(ticker='{self.ticker}', price={self.current_price:.2f}, "
            f"FCF_TTM={self.fcf_last:.2e}, Audit={self.audit_score}/100)"
        )


@dataclass
class DCFParameters:
    """
    Paramètres d'entrée pour le moteur mathématique DCF.
    """
    # --- 1. Taux d'Actualisation (Risk) ---
    risk_free_rate: float
    market_risk_premium: float
    cost_of_debt: float
    tax_rate: float

    # --- 2. Hypothèses de Croissance ---
    fcf_growth_rate: float
    perpetual_growth_rate: float

    # --- 3. Horizon Temporel ---
    projection_years: int

    # --- 4. Structure de Croissance (Multi-Stage) ---
    high_growth_years: int = 0

    # --- 5. Paramètres de Simulation (Monte Carlo) ---
    beta_volatility: float = 0.10
    growth_volatility: float = 0.01
    terminal_growth_volatility: float = 0.0025

    def to_log_dict(self) -> Dict[str, Any]:
        return {
            "Rf": self.risk_free_rate,
            "MRP": self.market_risk_premium,
            "Rd": self.cost_of_debt,
            "Tax": self.tax_rate,
            "g_start": self.fcf_growth_rate,
            "g_term": self.perpetual_growth_rate,
            "high_growth_years": self.high_growth_years,
            "years": self.projection_years,
        }


@dataclass
class DCFResult:
    """
    Résultat de sortie du moteur de calcul.
    """
    # Résultats du WACC
    wacc: float
    cost_of_equity: float
    after_tax_cost_of_debt: float

    # Résultats de la Projection
    projected_fcfs: List[float]
    discount_factors: List[float]

    # Composants de la Valeur
    sum_discounted_fcf: float
    terminal_value: float
    discounted_terminal_value: float

    # Valeurs Agrégées
    enterprise_value: float
    equity_value: float

    # KPI Final
    intrinsic_value_per_share: float

    # Résultats Monte Carlo (Optionnel)
    simulation_results: Optional[List[float]] = None

    def to_log_dict(self) -> Dict[str, Any]:
        return {
            "wacc": self.wacc,
            "EV": self.enterprise_value,
            "EqV": self.equity_value,
            "IV_Share": self.intrinsic_value_per_share,
            "Simulated": bool(self.simulation_results),
        }