"""
tests/contracts/test_config_contracts.py
Tests de Contrats — Configuration Centralisée

Ces tests garantissent que les constantes de configuration restent stables.
DT-010/011/012/013 Resolution.

RÈGLE D'OR : Ces tests NE DOIVENT PAS CHANGER lors des refactorings.
"""

import pytest


class TestMonteCarloDefaultsContract:
    """Contrat de stabilité pour MonteCarloDefaults."""
    
    def test_constants_exist(self):
        """Vérifie que les constantes Monte Carlo existent."""
        from core.config import MonteCarloDefaults
        
        assert MonteCarloDefaults.MIN_SIMULATIONS == 100
        assert MonteCarloDefaults.MAX_SIMULATIONS == 20_000
        assert MonteCarloDefaults.DEFAULT_SIMULATIONS == 5_000
        assert MonteCarloDefaults.STEP_SIMULATIONS == 200
    
    def test_default_rho_exists(self):
        """Vérifie que le rho par défaut existe."""
        from core.config import MonteCarloDefaults
        
        assert MonteCarloDefaults.DEFAULT_RHO == -0.30


class TestPeerDefaultsContract:
    """Contrat de stabilité pour PeerDefaults."""
    
    def test_max_peers_exists(self):
        """Vérifie que MAX_PEERS_ANALYSIS existe."""
        from core.config import PeerDefaults
        
        assert PeerDefaults.MAX_PEERS_ANALYSIS == 5
        assert PeerDefaults.MIN_PEERS_REQUIRED == 2


class TestAuditThresholdsContract:
    """Contrat de stabilité pour AuditThresholds."""
    
    def test_icr_threshold_exists(self):
        """Vérifie que le seuil ICR existe."""
        from core.config import AuditThresholds
        
        assert AuditThresholds.ICR_MIN == 1.5
    
    def test_beta_thresholds_exist(self):
        """Vérifie que les seuils Beta existent."""
        from core.config import AuditThresholds
        
        assert AuditThresholds.BETA_MIN == 0.4
        assert AuditThresholds.BETA_MAX == 3.0
    
    def test_sotp_thresholds_exist(self):
        """Vérifie que les seuils SOTP existent."""
        from core.config import AuditThresholds
        
        assert AuditThresholds.SOTP_REVENUE_GAP_WARNING == 0.05
        assert AuditThresholds.SOTP_DISCOUNT_MAX == 0.25


class TestAuditPenaltiesContract:
    """Contrat de stabilité pour AuditPenalties."""
    
    def test_penalties_exist(self):
        """Vérifie que les pénalités existent."""
        from core.config import AuditPenalties
        
        assert AuditPenalties.CRITICAL == 100.0
        assert AuditPenalties.HIGH == 35.0
        assert AuditPenalties.MEDIUM == 15.0
        assert AuditPenalties.LOW == 5.0


class TestAuditWeightsContract:
    """Contrat de stabilité pour AuditWeights."""
    
    def test_auto_weights_sum_to_one(self):
        """Vérifie que les poids AUTO font 100%."""
        from core.config import AuditWeights
        
        total = sum(AuditWeights.AUTO.values())
        assert abs(total - 1.0) < 0.001
    
    def test_manual_weights_sum_to_one(self):
        """Vérifie que les poids MANUAL font 100%."""
        from core.config import AuditWeights
        
        total = sum(AuditWeights.MANUAL.values())
        assert abs(total - 1.0) < 0.001
    
    def test_get_weights_method(self):
        """Vérifie la méthode get_weights."""
        from core.config import AuditWeights
        
        auto = AuditWeights.get_weights(is_manual=False)
        manual = AuditWeights.get_weights(is_manual=True)
        
        assert auto == AuditWeights.AUTO
        assert manual == AuditWeights.MANUAL


class TestSystemDefaultsContract:
    """Contrat de stabilité pour SystemDefaults."""
    
    def test_projection_years_exist(self):
        """Vérifie que les constantes d'horizon existent."""
        from core.config import SystemDefaults
        
        assert SystemDefaults.DEFAULT_PROJECTION_YEARS == 5
        assert SystemDefaults.MIN_PROJECTION_YEARS == 1
        assert SystemDefaults.MAX_PROJECTION_YEARS == 15
    
    def test_default_rates_exist(self):
        """Vérifie que les taux par défaut existent."""
        from core.config import SystemDefaults
        
        assert SystemDefaults.DEFAULT_RISK_FREE_RATE == 0.04
        assert SystemDefaults.DEFAULT_MARKET_RISK_PREMIUM == 0.05
