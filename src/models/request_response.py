"""
Requêtes et résultats de valorisation.

Ce module définit les structures de données pour les requêtes
de valorisation et leurs résultats, formant le contrat principal
d'interface avec les moteurs de calcul.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional  # Any requis pour Pydantic model_post_init

from pydantic import BaseModel, ConfigDict, Field

from .enums import ValuationMode, InputSource
from .company import CompanyFinancials
from .dcf_inputs import DCFParameters
from .glass_box import CalculationStep
from .audit import AuditReport, ValuationOutputContract
from .scenarios import ScenarioSynthesis, SOTPParameters
from src.config.constants import ModelDefaults


class ValuationRequest(BaseModel):
    """Requête de valorisation.

    Structure de données pour une demande de valorisation d'entreprise.
    Spécifie le ticker, la méthode et les paramètres optionnels.

    Attributes
    ----------
    ticker : str
        Symbole boursier de l'entreprise à valoriser.
    projection_years : int
        Nombre d'années de projection explicite.
    mode : ValuationMode
        Mode de valorisation à utiliser.
    input_source : InputSource
        Source des données d'entrée (AUTO ou MANUAL).
    manual_params : DCFParameters, optional
        Paramètres DCF manuels (si input_source=MANUAL).
    options : Dict[str, Any], default={}
        Options supplémentaires pour le calcul.
    """
    model_config = ConfigDict(frozen=True)

    ticker: str
    projection_years: int
    mode: ValuationMode
    input_source: InputSource
    manual_params: Optional[DCFParameters] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class HistoricalPoint(BaseModel):
    """Résultat de valorisation à un instant T passé (Backtest).

    Point de données historique pour l'analyse de backtesting,
    comparant la valeur intrinsèque calculée avec le prix de marché.

    Attributes
    ----------
    valuation_date : date
        Date de la valorisation historique.
    intrinsic_value : float
        Valeur intrinsèque calculée à cette date.
    market_price : float
        Prix de marché effectif à cette date.
    error_pct : float
        Erreur de valorisation en pourcentage.
    was_undervalued : bool
        True si la valeur intrinsèque > prix de marché.
    """
    valuation_date: date
    intrinsic_value: float
    market_price: float
    error_pct: float
    was_undervalued: bool


class BacktestResult(BaseModel):
    """Synthèse complète d'un backtesting.

    Résultats agrégés d'une analyse de backtesting sur une période
    historique, incluant métriques de précision du modèle.

    Attributes
    ----------
    points : List[HistoricalPoint], default=[]
        Liste des points de valorisation historique.
    mean_absolute_error : float, default=0.0
        Erreur absolue moyenne du modèle.
    alpha_vs_market : float, default=0.0
        Alpha généré par rapport au marché.
    model_accuracy_score : float, default=0.0
        Score de précision global du modèle.
    """
    model_config = ConfigDict(protected_namespaces=())

    points: List[HistoricalPoint] = Field(default_factory=list)
    mean_absolute_error: float = 0.0
    alpha_vs_market: float = 0.0
    model_accuracy_score: float = 0.0


class ValuationResult(BaseModel, ABC):
    """Résultat de valorisation (classe abstraite).

    Classe de base pour tous les résultats de valorisation.
    Définit le contrat commun incluant valeur intrinsèque,
    audit et traçabilité.

    Attributes
    ----------
    request : ValuationRequest, optional
        Requête originale ayant généré ce résultat.
    financials : CompanyFinancials
        Données financières utilisées dans le calcul.
    params : DCFParameters
        Paramètres utilisés pour la valorisation.
    intrinsic_value_per_share : float
        Valeur intrinsèque par action.
    market_price : float
        Prix de marché au moment du calcul.
    upside_pct : float, optional
        Potentiel de hausse en pourcentage.
    calculation_trace : List[CalculationStep], default=[]
        Trace détaillée des étapes de calcul.
    audit_report : AuditReport, optional
        Rapport d'audit de la valorisation.
    simulation_results : List[float], optional
        Résultats des simulations Monte Carlo.
    quantiles : Dict[str, float], optional
        Quantiles des distributions Monte Carlo.
    rho_sensitivity : Dict[str, float], default={}
        Sensibilité aux paramètres (rho coefficients).
    stress_test_value : float, optional
        Valeur dans un scénario de stress.
    mc_valid_ratio : float, optional
        Ratio de simulations valides.
    mc_clamping_applied : bool, optional
        True si du clamping a été appliqué.
    multiples_triangulation : 'MultiplesValuationResult', optional
        Résultat de triangulation par multiples.
    relative_valuation : Dict[str, float], optional
        Métriques de valorisation relative.
    scenario_synthesis : ScenarioSynthesis, optional
        Synthèse des scénarios.
    sotp_results : SOTPParameters, optional
        Résultats SOTP.
    backtest_report : BacktestResult, optional
        Rapport de backtesting.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    request: Optional[ValuationRequest] = None
    financials: CompanyFinancials
    params: DCFParameters
    intrinsic_value_per_share: float
    market_price: float
    upside_pct: Optional[float] = None
    calculation_trace: List[CalculationStep] = Field(default_factory=list)
    audit_report: Optional[AuditReport] = None
    
    # Monte Carlo
    simulation_results: Optional[List[float]] = None
    quantiles: Optional[Dict[str, float]] = None
    rho_sensitivity: Dict[str, float] = Field(default_factory=dict)
    stress_test_value: Optional[float] = None
    mc_valid_ratio: Optional[float] = None
    mc_clamping_applied: Optional[bool] = None

    # Extensions
    multiples_triangulation: Optional['MultiplesValuationResult'] = None
    relative_valuation: Optional[Dict[str, float]] = None
    scenario_synthesis: Optional[ScenarioSynthesis] = None
    sotp_results: Optional[SOTPParameters] = None
    backtest_report: Optional[BacktestResult] = None

    def model_post_init(self, __context: Any) -> None:
        if self.market_price > 0 and self.upside_pct is None:
            self.upside_pct = (self.intrinsic_value_per_share / self.market_price) - 1.0

    @property
    def ticker(self) -> str:
        """Retourne le ticker du résultat ou 'UNKNOWN' si non disponible.

        Returns
        -------
        str
            Symbole boursier ou 'UNKNOWN' si non disponible.
        """
        return self.request.ticker if self.request else "UNKNOWN"

    @property
    def mode(self) -> Optional[ValuationMode]:
        """Retourne le mode de valorisation ou None si non disponible.

        Returns
        -------
        Optional[ValuationMode]
            Mode de valorisation utilisé ou None si non disponible.
        """
        return self.request.mode if self.request else None

    @abstractmethod
    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie de valorisation.

        Returns
        -------
        ValuationOutputContract
            Contrat spécifiant les éléments disponibles dans ce résultat.
        """
        raise NotImplementedError


class DCFValuationResult(ValuationResult):
    """Résultat DCF (Free Cash Flow to Firm).

    Résultat d'une valorisation DCF basée sur les flux de trésorerie
    disponibles pour les investisseurs (FCFF).

    Attributes
    ----------
    wacc : float
        Weighted Average Cost of Capital utilisé.
    projected_fcfs : List[float]
        Liste des FCFF projetés pour chaque année.
    enterprise_value : float
        Valeur d'entreprise calculée.
    equity_value : float
        Valeur des fonds propres.
    discounted_terminal_value : float, optional
        Valeur terminale actualisée.
    """
    wacc: float
    projected_fcfs: List[float]
    enterprise_value: float
    equity_value: float
    discounted_terminal_value: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie pour un résultat DCF.

        Returns
        -------
        ValuationOutputContract
            Contrat spécifiant les éléments disponibles.
        """
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_fcfs) > 0,
            has_terminal_value=self.discounted_terminal_value is not None,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class RIMValuationResult(ValuationResult):
    """Résultat Residual Income Model.

    Résultat d'une valorisation par le modèle du revenu résiduel,
    basé sur les flux de trésorerie disponibles pour les actionnaires (FCFE).

    Attributes
    ----------
    cost_of_equity : float
        Coût des fonds propres utilisé.
    total_equity_value : float
        Valeur totale des fonds propres.
    projected_residual_incomes : List[float]
        Liste des revenus résiduels projetés.
    """
    cost_of_equity: float
    total_equity_value: float
    projected_residual_incomes: List[float]

    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie pour un résultat RIM.

        Returns
        -------
        ValuationOutputContract
            Contrat spécifiant les éléments disponibles.
        """
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_residual_incomes) > 0,
            has_terminal_value=True,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class GrahamValuationResult(ValuationResult):
    """Résultat Graham Number.

    Résultat d'une valorisation selon la formule de Benjamin Graham,
    basée sur les fondamentaux EPS et croissance.

    Attributes
    ----------
    eps_used : float
        Bénéfice par action utilisé dans le calcul.
    growth_rate_used : float
        Taux de croissance utilisé dans le calcul.
    """
    eps_used: float
    growth_rate_used: float

    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie pour un résultat Graham.

        Returns
        -------
        ValuationOutputContract
            Contrat spécifiant les éléments disponibles.
        """
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=True,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class EquityDCFValuationResult(ValuationResult):
    """Résultat FCFE / Dividend Discount Model.

    Résultat d'une valorisation basée sur les flux de trésorerie
    disponibles pour les actionnaires (FCFE) ou les dividendes.

    Attributes
    ----------
    cost_of_equity : float
        Coût des fonds propres utilisé.
    projected_equity_flows : List[float]
        Liste des flux actionnariaux projetés.
    equity_value : float
        Valeur des fonds propres calculée.
    discounted_terminal_value : float, optional
        Valeur terminale actualisée.
    """
    cost_of_equity: float
    projected_equity_flows: List[float]
    equity_value: float
    discounted_terminal_value: Optional[float] = None

    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie pour un résultat FCFE/DDM.

        Returns
        -------
        ValuationOutputContract
            Contrat spécifiant les éléments disponibles.
        """
        return ValuationOutputContract(
            has_params=True,
            has_projection=len(self.projected_equity_flows) > 0,
            has_terminal_value=self.discounted_terminal_value is not None,
            has_intrinsic_value=True,
            has_audit=self.audit_report is not None
        )


class PeerMetric(BaseModel):
    """Métriques brutes d'un concurrent.

    Données financières d'une entreprise comparable utilisée
    pour la triangulation par multiples.

    Attributes
    ----------
    ticker : str
        Symbole boursier du concurrent.
    name : str, optional, default="Unknown"
        Nom du concurrent.
    pe_ratio : float, optional
        Ratio cours/bénéfice.
    ev_ebitda : float, optional
        Ratio valeur entreprise/EBITDA.
    ev_revenue : float, optional
        Ratio valeur entreprise/chiffre d'affaires.
    market_cap : float, optional
        Capitalisation boursière.
    """
    ticker: str
    name: Optional[str] = "Unknown"
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_revenue: Optional[float] = None
    market_cap: Optional[float] = None


class MultiplesData(BaseModel):
    """Synthèse sectorielle pour la triangulation.

    Données agrégées des entreprises comparables pour
    l'estimation par multiples sectoriels.

    Attributes
    ----------
    peers : List[PeerMetric], default=[]
        Liste des entreprises comparables.
    median_pe : float, default=ModelDefaults.DEFAULT_MEDIAN_PE
        Médiane du ratio P/E sectoriel.
    median_ev_ebitda : float, default=ModelDefaults.DEFAULT_MEDIAN_EV_EBITDA
        Médiane du ratio EV/EBITDA sectoriel.
    median_ev_ebit : float, default=ModelDefaults.DEFAULT_MEDIAN_EV_EBIT
        Médiane du ratio EV/EBIT sectoriel.
    median_pb : float, default=ModelDefaults.DEFAULT_MEDIAN_PB
        Médiane du ratio P/B sectoriel.
    median_ev_rev : float, default=ModelDefaults.DEFAULT_MEDIAN_EV_REV
        Médiane du ratio EV/Revenue sectoriel.
    implied_value_ev_ebitda : float, default=ModelDefaults.DEFAULT_IMPLIED_VALUE_EV_EBITDA
        Valeur impliquée par EV/EBITDA.
    implied_value_pe : float, default=ModelDefaults.DEFAULT_IMPLIED_VALUE_PE
        Valeur impliquée par P/E.
    source : str, default="Yahoo Finance"
        Source des données.
    """
    peers: List[PeerMetric] = Field(default_factory=list)
    median_pe: float = ModelDefaults.DEFAULT_MEDIAN_PE
    median_ev_ebitda: float = ModelDefaults.DEFAULT_MEDIAN_EV_EBITDA
    median_ev_ebit: float = ModelDefaults.DEFAULT_MEDIAN_EV_EBIT
    median_pb: float = ModelDefaults.DEFAULT_MEDIAN_PB
    median_ev_rev: float = ModelDefaults.DEFAULT_MEDIAN_EV_REV
    implied_value_ev_ebitda: float = ModelDefaults.DEFAULT_IMPLIED_VALUE_EV_EBITDA
    implied_value_pe: float = ModelDefaults.DEFAULT_IMPLIED_VALUE_PE
    source: str = "Yahoo Finance"

    @property
    def peer_count(self) -> int:
        """Nombre de sociétés comparables dans le panel.

        Returns
        -------
        int
            Nombre d'entreprises dans la liste des comparables.
        """
        return len(self.peers)


class MultiplesValuationResult(ValuationResult):
    """Résultat de valorisation par multiples.

    Résultat d'une valorisation basée sur les ratios de marché
    des entreprises comparables.

    Attributes
    ----------
    pe_based_price : float, default=ModelDefaults.DEFAULT_PE_BASED_PRICE
        Prix estimé par ratio P/E.
    ebitda_based_price : float, default=ModelDefaults.DEFAULT_EBITDA_BASED_PRICE
        Prix estimé par ratio EV/EBITDA.
    rev_based_price : float, default=ModelDefaults.DEFAULT_REV_BASED_PRICE
        Prix estimé par ratio EV/Revenue.
    multiples_data : MultiplesData
        Données des comparables utilisées.
    """
    pe_based_price: float = ModelDefaults.DEFAULT_PE_BASED_PRICE
    ebitda_based_price: float = ModelDefaults.DEFAULT_EBITDA_BASED_PRICE
    rev_based_price: float = ModelDefaults.DEFAULT_REV_BASED_PRICE
    multiples_data: MultiplesData

    def build_output_contract(self) -> ValuationOutputContract:
        """Construit le contrat de sortie pour un résultat par multiples.

        Returns
        -------
        ValuationOutputContract
            Contrat spécifiant les éléments disponibles.
        """
        return ValuationOutputContract(
            has_params=True,
            has_projection=False,
            has_terminal_value=False,
            has_intrinsic_value=True,
            has_audit=True
        )
