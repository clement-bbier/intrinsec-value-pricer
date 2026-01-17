"""
tests/e2e/test_expert_mode_workflow.py
Tests End-to-End — Workflow Mode Expert

Ces tests simulent le parcours d'un analyste expert.
"""

import pytest


class TestExpertModeWorkflow:
    """Tests du workflow Expert complet."""
    
    def test_expert_can_override_parameters(self, sample_financials, sample_params):
        """L'expert peut surcharger les paramètres automatiques."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        # L'expert définit ses propres paramètres
        sample_params.rates.risk_free_rate = 0.035  # Override
        sample_params.growth.fcf_growth_rate = 0.08  # Override
        sample_params.growth.perpetual_growth_rate = 0.025  # Override
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=7,  # Horizon personnalisé
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.MANUAL,
            manual_params=sample_params,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        # Vérifier que les paramètres ont été utilisés
        assert result is not None
        assert result.audit_report.audit_mode == InputSource.MANUAL
    
    def test_expert_mode_uses_reduced_data_weight(self, sample_financials, sample_params):
        """Le mode Expert réduit le poids du pilier DATA_CONFIDENCE."""
        from core.valuation.engines import run_valuation
        from core.models import (
            ValuationRequest, ValuationMode, InputSource, AuditPillar
        )
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.MANUAL,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        # Vérifier le pillar breakdown si disponible
        if result.audit_report.pillar_breakdown:
            pillars = result.audit_report.pillar_breakdown.pillars
            if AuditPillar.DATA_CONFIDENCE in pillars:
                data_pillar = pillars[AuditPillar.DATA_CONFIDENCE]
                # En mode MANUAL, le poids devrait être réduit (10% vs 30%)
                assert data_pillar.weight <= 0.15


class TestExpertModeScenarios:
    """Tests de scénarios Expert."""
    
    def test_pessimistic_scenario(self, sample_financials, sample_params):
        """Scénario pessimiste avec croissance faible."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        # Paramètres pessimistes
        sample_params.growth.fcf_growth_rate = 0.01  # 1%
        sample_params.growth.perpetual_growth_rate = 0.005  # 0.5%
        sample_params.rates.market_risk_premium = 0.07  # 7% MRP (prudent)
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.MANUAL,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        assert result.intrinsic_value_per_share > 0
    
    def test_optimistic_scenario(self, sample_financials, sample_params):
        """Scénario optimiste avec croissance élevée."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        # Paramètres optimistes
        sample_params.growth.fcf_growth_rate = 0.15  # 15%
        sample_params.growth.perpetual_growth_rate = 0.03  # 3%
        sample_params.rates.market_risk_premium = 0.04  # 4% MRP (agressif)
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.MANUAL,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        assert result.intrinsic_value_per_share > 0


class TestExpertModeValidation:
    """Tests de validation mode Expert."""
    
    def test_manual_debt_override(self, sample_financials, sample_params):
        """L'expert peut surcharger la dette."""
        from core.computation.financial_math import calculate_wacc
        
        # Yahoo dit 20M de dette
        sample_financials.total_debt = 20_000_000
        
        # L'expert dit 0 (entreprise sans dette)
        sample_params.growth.manual_total_debt = 0.0
        
        ctx = calculate_wacc(sample_financials, sample_params)
        
        # Le poids de la dette doit être 0
        assert ctx.weight_debt == 0.0 or ctx.weight_debt < 0.01
    
    def test_expert_parameters_preserved(self, sample_financials, sample_params):
        """Les paramètres Expert sont préservés dans le résultat."""
        from core.valuation.engines import run_valuation
        from core.models import ValuationRequest, ValuationMode, InputSource
        
        custom_rate = 0.0375  # Taux personnalisé
        sample_params.rates.risk_free_rate = custom_rate
        
        request = ValuationRequest(
            ticker="TEST",
            projection_years=5,
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.MANUAL,
            manual_params=sample_params,
        )
        
        result = run_valuation(request, sample_financials, sample_params)
        
        # Les paramètres doivent être accessibles dans le résultat
        assert result.params is not None
        assert result.params.rates.risk_free_rate == custom_rate
