"""
src/domain/models/pitchbook.py

PITCHBOOK DATA TRANSFER OBJECT — ST-5.2

Version : V1.0 — Sprint 5
Pattern : DTO (Data Transfer Object)
Style : Numpy docstrings

ST-5.2 : REPORTING PREMIUM PDF
==============================
Ce DTO regroupe toutes les données nécessaires pour générer
un rapport Pitchbook professionnel de 3 pages :
1. Résumé exécutif (prix cible, score d'audit)
2. Preuves de calcul (formules LaTeX, substitutions)
3. Analyse de risque (sensibilité, Monte Carlo)

Financial Impact:
    Le Pitchbook est le livrable final présenté aux investisseurs.
    Sa qualité reflète directement la rigueur de l'analyse.

Usage:
    from src.domain.models.pitchbook import PitchbookData
    from src.reporting.pdf_generator import generate_pitchbook_pdf
    
    data = PitchbookData.from_valuation_result(result, provider)
    pdf_bytes = generate_pitchbook_pdf(data)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel

from src.domain.models.request_response import (
    ValuationResult, DCFValuationResult, RIMValuationResult,
    EquityDCFValuationResult, GrahamValuationResult
)
from src.domain.models.glass_box import CalculationStep
from src.domain.models.audit import AuditReport
from src.domain.models.enums import ValuationMode


@dataclass
class ExecutiveSummary:
    """
    Résumé exécutif pour la page 1 du Pitchbook.
    
    Attributes
    ----------
    ticker : str
        Symbole boursier.
    company_name : str
        Nom de l'entreprise.
    sector : str
        Secteur d'activité.
    currency : str
        Devise de valorisation.
    valuation_date : datetime
        Date de l'analyse.
    valuation_mode : str
        Mode de valorisation utilisé.
    
    intrinsic_value : float
        Valeur intrinsèque par action.
    market_price : float
        Prix de marché actuel.
    upside_pct : float
        Potentiel de hausse en pourcentage.
    recommendation : str
        Recommandation (ACHAT, CONSERVER, VENTE).
    
    audit_score : float
        Score d'audit global (0-100).
    audit_grade : str
        Grade d'audit (A, B, C, D, F).
    
    key_metrics : Dict[str, Any]
        Métriques clés additionnelles.
    """
    ticker: str
    company_name: str
    sector: str
    currency: str
    valuation_date: datetime
    valuation_mode: str
    
    intrinsic_value: float
    market_price: float
    upside_pct: float
    recommendation: str
    
    audit_score: float
    audit_grade: str
    
    key_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CalculationProof:
    """
    Preuves de calcul pour la page 2 du Pitchbook.
    
    Attributes
    ----------
    steps : List[CalculationStep]
        Étapes de calcul Glass Box.
    key_assumptions : Dict[str, float]
        Hypothèses clés utilisées.
    dcf_components : Dict[str, float]
        Composantes du DCF (PV flux, TV, etc.).
    """
    steps: List[CalculationStep]
    key_assumptions: Dict[str, float]
    dcf_components: Dict[str, float]


@dataclass
class RiskAnalysis:
    """
    Analyse de risque pour la page 3 du Pitchbook.
    
    Attributes
    ----------
    sensitivity_data : Dict[str, Any]
        Données pour la matrice de sensibilité.
    monte_carlo_stats : Optional[Dict[str, float]]
        Statistiques Monte Carlo (P10, P50, P90, etc.).
    scenario_results : Optional[Dict[str, float]]
        Résultats des scénarios Bull/Base/Bear.
    risk_factors : List[str]
        Facteurs de risque identifiés.
    """
    sensitivity_data: Dict[str, Any]
    monte_carlo_stats: Optional[Dict[str, float]] = None
    scenario_results: Optional[Dict[str, float]] = None
    risk_factors: List[str] = field(default_factory=list)


class PitchbookData(BaseModel):
    """
    DTO complet pour la génération du Pitchbook PDF.
    
    Regroupe toutes les données nécessaires pour générer
    un rapport professionnel de 3 pages.
    
    Attributes
    ----------
    executive_summary : ExecutiveSummary
        Données pour le résumé exécutif (page 1).
    calculation_proof : CalculationProof
        Preuves de calcul (page 2).
    risk_analysis : RiskAnalysis
        Analyse de risque (page 3).
    metadata : Dict[str, Any]
        Métadonnées du rapport.
    
    Examples
    --------
    >>> data = PitchbookData.from_valuation_result(result)
    >>> pdf = generate_pitchbook_pdf(data)
    """
    executive_summary: Dict[str, Any]
    calculation_proof: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def _extract_cost_of_capital(cls, result: ValuationResult) -> Optional[float]:
        """Extrait le coût du capital selon le type de modèle."""
        if isinstance(result, DCFValuationResult):
            return result.wacc
        elif isinstance(result, (RIMValuationResult, EquityDCFValuationResult)):
            return result.cost_of_equity
        return None

    @classmethod
    def _extract_terminal_value(cls, result: ValuationResult) -> Optional[float]:
        """Extrait la valeur terminale selon le type de modèle."""
        if isinstance(result, DCFValuationResult):
            return result.discounted_terminal_value
        elif isinstance(result, EquityDCFValuationResult):
            return result.discounted_terminal_value
        elif isinstance(result, RIMValuationResult):
            return result.total_equity_value * 0.5  # Approximation pour RIM
        elif isinstance(result, GrahamValuationResult):
            return result.eps_used * 8.5  # Graham formula
        return None

    @classmethod
    def _extract_calculation_steps(cls, result: ValuationResult) -> List[Dict[str, Any]]:
        """Extrait les étapes de calcul de la Glass Box."""
        if result.calculation_trace:
            return [step.model_dump() for step in result.calculation_trace]
        return []

    @classmethod
    def _extract_audit_data(cls, result: ValuationResult) -> Dict[str, Any]:
        """Extrait les données complètes du rapport d'audit."""
        if not result.audit_report:
            return {"global_score": 0, "grade": "F", "steps": []}

        return {
            "global_score": result.audit_report.global_score,
            "grade": cls._compute_grade(result.audit_report.global_score),
            "steps": [step.model_dump() for step in result.audit_report.steps],
            "alerts": [step.label for step in result.audit_report.steps if not step.verdict]
        }

    @classmethod
    def from_valuation_result(
        cls,
        result: ValuationResult,
        company_name: str = "",
        sector: str = ""
    ) -> "PitchbookData":
        """
        Crée un PitchbookData depuis un ValuationResult.

        Parameters
        ----------
        result : ValuationResult
            Résultat de valorisation.
        company_name : str, optional
            Nom de l'entreprise.
        sector : str, optional
            Secteur d'activité.

        Returns
        -------
        PitchbookData
            DTO prêt pour la génération PDF.
        """
        # Calcul de la recommandation
        upside = ((result.intrinsic_value_per_share / result.market_price) - 1) * 100 if result.market_price > 0 else 0
        recommendation = cls._compute_recommendation(upside)

        # Données d'audit complètes
        audit_data = cls._extract_audit_data(result)

        # Executive Summary
        executive = {
            "ticker": result.ticker,
            "company_name": company_name or result.ticker,
            "sector": sector or "N/A",
            "currency": result.financials.currency if result.financials else "USD",
            "valuation_date": datetime.now().isoformat(),
            "valuation_mode": result.mode.value if result.mode else "UNKNOWN",
            "intrinsic_value": result.intrinsic_value_per_share,
            "market_price": result.market_price,
            "upside_pct": upside,
            "recommendation": recommendation,
            "audit_score": audit_data["global_score"],
            "audit_grade": audit_data["grade"],
            "key_metrics": {
                "cost_of_capital": cls._extract_cost_of_capital(result),
                "perpetual_growth": result.params.growth.perpetual_growth_rate if result.params else None,
                "enterprise_value": getattr(result, 'enterprise_value', 0),
                "terminal_value": cls._extract_terminal_value(result),
            }
        }
        
        # Calculation Proof
        calculation = {
            "steps": cls._extract_calculation_steps(result),
            "key_assumptions": {
                "risk_free_rate": result.params.rates.risk_free_rate if result.params else None,
                "market_risk_premium": result.params.rates.market_risk_premium if result.params else None,
                "beta": result.params.rates.beta if result.params else None,
                "cost_of_debt": result.params.rates.cost_of_debt if result.params else None,
                "tax_rate": result.params.rates.tax_rate if result.params else None,
            },
            "dcf_components": {
                "pv_explicit_flows": getattr(result, 'pv_explicit_flows', 0),
                "terminal_value": cls._extract_terminal_value(result),
                "enterprise_value": getattr(result, 'enterprise_value', 0),
                "equity_value": getattr(result, 'equity_value', 0),
            }
        }
        
        # Risk Analysis - Statistiques Monte Carlo complètes
        mc_stats = None
        if result.simulation_results:
            import numpy as np
            values = [v for v in result.simulation_results if v is not None and isinstance(v, (int, float))]
            if values and len(values) > 10:  # Minimum de données pour être significatif
                mc_stats = {
                    "count": len(values),
                    "mean": float(np.mean(values)),
                    "median": float(np.median(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "p5": float(np.percentile(values, 5)),
                    "p10": float(np.percentile(values, 10)),
                    "p25": float(np.percentile(values, 25)),
                    "p75": float(np.percentile(values, 75)),
                    "p90": float(np.percentile(values, 90)),
                    "p95": float(np.percentile(values, 95)),
                    "skewness": float(np.mean(((values - np.mean(values)) / np.std(values)) ** 3)),
                    "kurtosis": float(np.mean(((values - np.mean(values)) / np.std(values)) ** 4) - 3),
                }

        # Scénarios
        scenario_results = None
        if result.scenario_synthesis and result.scenario_synthesis.variants:
            scenario_results = {
                variant.label: variant.intrinsic_value
                for variant in result.scenario_synthesis.variants
            }

        # Coût du capital pour la sensibilité
        cost_of_capital = cls._extract_cost_of_capital(result) or 0.08
        perpetual_growth = result.params.growth.perpetual_growth_rate if result.params else 0.02

        risk = {
            "sensitivity_data": {
                "base_cost_of_capital": cost_of_capital,
                "base_growth": perpetual_growth,
            },
            "monte_carlo_stats": mc_stats,
            "scenario_results": scenario_results,
            "audit_data": audit_data,  # Inclure les données d'audit complètes
            "risk_factors": audit_data.get("alerts", [])[:8],  # Limiter à 8 facteurs max
        }
        
        return cls(
            executive_summary=executive,
            calculation_proof=calculation,
            risk_analysis=risk,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "generator": "Intrinsic Value Pricer",
            }
        )
    
    @staticmethod
    def _compute_recommendation(upside: float) -> str:
        """Calcule la recommandation basée sur le potentiel."""
        if upside > 30:
            return "ACHAT FORT"
        elif upside > 10:
            return "ACHAT"
        elif upside > -10:
            return "CONSERVER"
        elif upside > -30:
            return "VENTE"
        else:
            return "VENTE FORTE"
    
    @staticmethod
    def _compute_grade(score: float) -> str:
        """Calcule le grade d'audit."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
