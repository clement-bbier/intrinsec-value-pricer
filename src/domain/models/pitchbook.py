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

from src.domain.models.request_response import ValuationResult
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
        
        # Grade d'audit
        audit_score = result.audit_report.global_score if result.audit_report else 0
        audit_grade = cls._compute_grade(audit_score)
        
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
            "audit_score": audit_score,
            "audit_grade": audit_grade,
            "key_metrics": {
                "wacc": result.params.rates.wacc if result.params else None,
                "perpetual_growth": result.params.growth.perpetual_growth_rate if result.params else None,
                "enterprise_value": result.enterprise_value,
            }
        }
        
        # Calculation Proof
        calculation = {
            "steps": [step.model_dump() for step in (result.trace.steps if result.trace else [])],
            "key_assumptions": {
                "risk_free_rate": result.params.rates.risk_free_rate if result.params else None,
                "market_risk_premium": result.params.rates.market_risk_premium if result.params else None,
                "beta": result.params.rates.beta if result.params else None,
                "cost_of_debt": result.params.rates.cost_of_debt if result.params else None,
                "tax_rate": result.params.rates.tax_rate if result.params else None,
            },
            "dcf_components": {
                "pv_explicit_flows": getattr(result, 'pv_explicit_flows', 0),
                "terminal_value": getattr(result, 'terminal_value', 0),
                "enterprise_value": result.enterprise_value,
                "equity_value": result.equity_value,
            }
        }
        
        # Risk Analysis
        mc_stats = None
        if result.simulation_results:
            import numpy as np
            values = [v for v in result.simulation_results if v is not None]
            if values:
                mc_stats = {
                    "count": len(values),
                    "mean": float(np.mean(values)),
                    "median": float(np.median(values)),
                    "p10": float(np.percentile(values, 10)),
                    "p90": float(np.percentile(values, 90)),
                    "std": float(np.std(values)),
                }
        
        scenario_results = None
        if result.scenario_synthesis:
            scenario_results = {
                variant.label: variant.intrinsic_value
                for variant in result.scenario_synthesis.variants
            }
        
        risk = {
            "sensitivity_data": {
                "base_wacc": result.params.rates.wacc if result.params else 0.08,
                "base_growth": result.params.growth.perpetual_growth_rate if result.params else 0.02,
            },
            "monte_carlo_stats": mc_stats,
            "scenario_results": scenario_results,
            "risk_factors": cls._extract_risk_factors(result),
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
    
    @staticmethod
    def _extract_risk_factors(result: ValuationResult) -> List[str]:
        """Extrait les facteurs de risque depuis le rapport d'audit."""
        factors = []
        
        if result.audit_report:
            for step in result.audit_report.steps:
                if not step.verdict:
                    factors.append(step.label)
        
        return factors[:5]  # Max 5 facteurs
