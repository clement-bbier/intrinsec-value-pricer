"""
tests/contracts/test_i18n_contracts.py
Tests de Contrats — Internationalisation (i18n)

Ces tests garantissent que les exports de textes restent stables.
Importants pour la migration i18n prévue au Sprint 8.

RÈGLE D'OR : Ces tests NE DOIVENT PAS CHANGER lors des refactorings.
"""

import pytest


class TestCoreI18nContract:
    """Contrat de stabilité pour core.i18n."""
    
    def test_core_i18n_exports_main_classes(self):
        """Vérifie que core.i18n exporte les classes principales."""
        from src.i18n import (
            CommonTexts,
            SidebarTexts,
            OnboardingTexts,
            FeedbackMessages,
            DiagnosticTexts,
        )
        
        # Ces classes DOIVENT être exportées
        assert CommonTexts is not None
        assert SidebarTexts is not None
        assert OnboardingTexts is not None
        assert FeedbackMessages is not None
        assert DiagnosticTexts is not None
    
    def test_core_i18n_exports_audit_classes(self):
        """Vérifie que core.i18n exporte les classes d'audit."""
        from src.i18n import (
            AuditEngineTexts,
            AuditCategories,
            AuditMessages,
            AuditTexts,
        )
        
        assert AuditEngineTexts is not None
        assert AuditCategories is not None
        assert AuditMessages is not None
        assert AuditTexts is not None


class TestI18nStructureContract:
    """Contrat de stabilite pour la structure i18n."""
    
    def test_fr_module_exports_ui_classes(self):
        """Verifie que core.i18n.fr exporte les classes UI."""
        from src.i18n.fr import (
            CommonTexts,
            SidebarTexts,
            SharedTexts,
            KPITexts,
        )
        
        assert hasattr(CommonTexts, "APP_TITLE")
        assert hasattr(SidebarTexts, "TICKER_LABEL")
        assert hasattr(SharedTexts, "BTN_CALCULATE")
        assert hasattr(KPITexts, "TAB_INPUTS")
    
    def test_fr_module_exports_backend_classes(self):
        """Verifie que core.i18n.fr exporte les classes backend."""
        from src.i18n.fr import (
            WorkflowTexts,
            DiagnosticTexts,
            CalculationErrors,
        )
        
        assert hasattr(WorkflowTexts, "STATUS_COMPLETE")
        assert hasattr(DiagnosticTexts, "UNKNOWN_STRATEGY_MSG")
        assert hasattr(CalculationErrors, "CONTRACT_VIOLATION")


class TestCommonTextsContract:
    """Contrat de stabilité pour CommonTexts."""
    
    def test_required_attributes(self):
        """Vérifie les attributs obligatoires de CommonTexts."""
        from src.i18n import CommonTexts
        
        required = [
            "APP_TITLE",
            "RUN_BUTTON",
            "DEFAULT_TICKER",
        ]
        
        for attr in required:
            assert hasattr(CommonTexts, attr), f"Attribut '{attr}' manquant"


class TestDiagnosticTextsContract:
    """Contrat de stabilité pour DiagnosticTexts."""
    
    def test_required_messages(self):
        """Vérifie les messages de diagnostic obligatoires."""
        from src.i18n import DiagnosticTexts
        
        required = [
            "UNKNOWN_STRATEGY_MSG",
            "UNKNOWN_STRATEGY_HINT",
            "CALC_GENERIC_HINT",
            "STRATEGY_CRASH_MSG",
            "STRATEGY_CRASH_HINT",
        ]
        
        for attr in required:
            assert hasattr(DiagnosticTexts, attr), f"Message '{attr}' manquant"


class TestSidebarTextsContract:
    """Contrat de stabilité pour SidebarTexts."""
    
    def test_section_headers(self):
        """Vérifie les en-têtes de section obligatoires."""
        from src.i18n import SidebarTexts
        
        required = [
            "SEC_1_COMPANY",
            "SEC_2_METHODOLOGY",
            "SEC_3_SOURCE",
            "TICKER_LABEL",
        ]
        
        for attr in required:
            assert hasattr(SidebarTexts, attr), f"En-tête '{attr}' manquant"
