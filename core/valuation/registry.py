"""
core/valuation/registry.py
REGISTRE CENTRALISÉ DES STRATÉGIES DE VALORISATION

Version : V1.0 — DT-007/008/009 Resolution
Pattern : Decorator-based Auto-Discovery

AVANT (3 registres manuels à maintenir) :
- STRATEGY_REGISTRY dans engines.py
- EXPERT_UI_REGISTRY dans main.py  
- AuditorFactory.mapping dans audit_engine.py

APRÈS (1 seul point d'enregistrement) :
- Chaque stratégie s'auto-enregistre via @register_strategy
- Les métadonnées (auditor, ui_renderer) sont déclarées au même endroit

Usage :
    from core.valuation.registry import register_strategy, get_strategy, get_auditor
    
    @register_strategy(
        mode=ValuationMode.FCFF_TWO_STAGE,
        auditor_cls=DCFAuditor,
        ui_renderer="render_expert_fcff_standard"
    )
    class StandardFCFFStrategy(ValuationStrategy):
        ...
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Type, Optional, Callable, Any, TYPE_CHECKING

from core.models import ValuationMode

if TYPE_CHECKING:
    from core.valuation.strategies.abstract import ValuationStrategy
    from infra.auditing.auditors import IValuationAuditor

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. METADATA CONTAINER
# ==============================================================================

@dataclass
class StrategyMetadata:
    """
    Métadonnées associées à une stratégie de valorisation.
    
    Attributes:
        mode: Le mode de valorisation (clé primaire)
        strategy_cls: La classe de stratégie
        auditor_cls: La classe d'auditeur associée (lazy import)
        auditor_cls_name: Nom de la classe pour import différé
        ui_renderer_name: Nom de la fonction UI pour le mode Expert (lazy import)
        display_name: Nom affiché dans l'UI
    """
    mode: ValuationMode
    strategy_cls: Type["ValuationStrategy"]
    auditor_cls_name: str = "DCFAuditor"
    ui_renderer_name: Optional[str] = None
    display_name: Optional[str] = None
    
    def get_auditor_cls(self) -> Type["IValuationAuditor"]:
        """Import différé de la classe d'auditeur pour éviter les imports circulaires."""
        from infra.auditing.auditors import (
            DCFAuditor, RIMAuditor, GrahamAuditor,
            StandardValuationAuditor, FCFEAuditor, DDMAuditor
        )
        
        mapping = {
            "DCFAuditor": DCFAuditor,
            "RIMAuditor": RIMAuditor,
            "GrahamAuditor": GrahamAuditor,
            "FCFEAuditor": FCFEAuditor,
            "DDMAuditor": DDMAuditor,
            "StandardValuationAuditor": StandardValuationAuditor,
        }
        
        return mapping.get(self.auditor_cls_name, StandardValuationAuditor)


# ==============================================================================
# 2. REGISTRE GLOBAL (Singleton Pattern)
# ==============================================================================

class StrategyRegistry:
    """
    Registre centralisé de toutes les stratégies de valorisation.
    
    Singleton pattern : une seule instance globale.
    Thread-safe pour les lectures (les écritures se font au démarrage).
    """
    
    _instance: Optional["StrategyRegistry"] = None
    _strategies: Dict[ValuationMode, StrategyMetadata] = {}
    
    def __new__(cls) -> "StrategyRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._strategies = {}
        return cls._instance
    
    @classmethod
    def register(
        cls,
        mode: ValuationMode,
        strategy_cls: Type["ValuationStrategy"],
        auditor_cls_name: str = "DCFAuditor",
        ui_renderer_name: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> None:
        """Enregistre une stratégie avec ses métadonnées."""
        metadata = StrategyMetadata(
            mode=mode,
            strategy_cls=strategy_cls,
            auditor_cls_name=auditor_cls_name,
            ui_renderer_name=ui_renderer_name,
            display_name=display_name or mode.value
        )
        cls._strategies[mode] = metadata
        logger.debug(f"[Registry] Stratégie enregistrée: {mode.value}")
    
    @classmethod
    def get_strategy_cls(cls, mode: ValuationMode) -> Optional[Type["ValuationStrategy"]]:
        """Retourne la classe de stratégie pour un mode donné."""
        metadata = cls._strategies.get(mode)
        return metadata.strategy_cls if metadata else None
    
    @classmethod
    def get_auditor_cls(cls, mode: ValuationMode) -> Type["IValuationAuditor"]:
        """Retourne la classe d'auditeur pour un mode donné."""
        from infra.auditing.auditors import StandardValuationAuditor
        
        metadata = cls._strategies.get(mode)
        if metadata:
            return metadata.get_auditor_cls()
        return StandardValuationAuditor
    
    @classmethod
    def get_ui_renderer_name(cls, mode: ValuationMode) -> Optional[str]:
        """Retourne le nom de la fonction UI pour un mode donné."""
        metadata = cls._strategies.get(mode)
        return metadata.ui_renderer_name if metadata else None
    
    @classmethod
    def get_display_name(cls, mode: ValuationMode) -> str:
        """Retourne le nom affiché pour un mode donné."""
        metadata = cls._strategies.get(mode)
        return metadata.display_name if metadata else mode.value
    
    @classmethod
    def get_all_modes(cls) -> Dict[ValuationMode, StrategyMetadata]:
        """Retourne toutes les stratégies enregistrées."""
        return cls._strategies.copy()
    
    @classmethod
    def get_display_names_map(cls) -> Dict[ValuationMode, str]:
        """Retourne un mapping mode -> display_name pour l'UI."""
        return {mode: meta.display_name for mode, meta in cls._strategies.items()}


# ==============================================================================
# 3. DÉCORATEUR D'ENREGISTREMENT
# ==============================================================================

def register_strategy(
    mode: ValuationMode,
    auditor: str = "DCFAuditor",
    ui_renderer: Optional[str] = None,
    display_name: Optional[str] = None
) -> Callable[[Type["ValuationStrategy"]], Type["ValuationStrategy"]]:
    """
    Décorateur pour enregistrer automatiquement une stratégie.
    
    Usage:
        @register_strategy(
            mode=ValuationMode.FCFF_TWO_STAGE,
            auditor="DCFAuditor",
            ui_renderer="render_expert_fcff_standard",
            display_name="FCFF Standard"
        )
        class StandardFCFFStrategy(ValuationStrategy):
            ...
    
    Args:
        mode: Le mode de valorisation associé
        auditor: Nom de la classe d'auditeur (str pour éviter les imports circulaires)
        ui_renderer: Nom de la fonction de rendu Expert UI
        display_name: Nom affiché dans l'interface
    
    Returns:
        Le décorateur qui enregistre la classe
    """
    def decorator(cls: Type["ValuationStrategy"]) -> Type["ValuationStrategy"]:
        StrategyRegistry.register(
            mode=mode,
            strategy_cls=cls,
            auditor_cls_name=auditor,
            ui_renderer_name=ui_renderer,
            display_name=display_name
        )
        # Ajoute une référence au mode sur la classe (utile pour introspection)
        cls._registered_mode = mode
        return cls
    
    return decorator


# ==============================================================================
# 4. FONCTIONS D'ACCÈS SIMPLIFIÉES (Facade Pattern)
# ==============================================================================

def get_strategy(mode: ValuationMode) -> Optional[Type["ValuationStrategy"]]:
    """Raccourci pour obtenir une classe de stratégie."""
    return StrategyRegistry.get_strategy_cls(mode)


def get_auditor(mode: ValuationMode) -> "IValuationAuditor":
    """Raccourci pour obtenir une instance d'auditeur."""
    auditor_cls = StrategyRegistry.get_auditor_cls(mode)
    return auditor_cls()


def get_all_strategies() -> Dict[ValuationMode, StrategyMetadata]:
    """Raccourci pour obtenir toutes les stratégies."""
    return StrategyRegistry.get_all_modes()


def get_display_names() -> Dict[ValuationMode, str]:
    """Raccourci pour obtenir les noms affichés."""
    return StrategyRegistry.get_display_names_map()


# ==============================================================================
# 5. ENREGISTREMENT INITIAL (Backward Compatibility)
# ==============================================================================

def _register_all_strategies() -> None:
    """
    Enregistre toutes les stratégies existantes.
    
    Cette fonction est appelée au chargement du module pour garantir
    la compatibilité ascendante avec le code existant.
    
    À terme, chaque stratégie utilisera directement @register_strategy
    dans son fichier de définition.
    """
    # Import local pour éviter les dépendances circulaires
    from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
    from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
    from core.valuation.strategies.dcf_growth import RevenueBasedStrategy
    from core.valuation.strategies.dcf_equity import FCFEStrategy
    from core.valuation.strategies.dcf_dividend import DividendDiscountStrategy
    from core.valuation.strategies.rim_banks import RIMBankingStrategy
    from core.valuation.strategies.graham_value import GrahamNumberStrategy
    
    # Approche Entité (Firm Value - WACC Based)
    StrategyRegistry.register(
        mode=ValuationMode.FCFF_TWO_STAGE,
        strategy_cls=StandardFCFFStrategy,
        auditor_cls_name="DCFAuditor",
        ui_renderer_name="render_expert_fcff_standard",
        display_name="FCFF Standard"
    )
    
    StrategyRegistry.register(
        mode=ValuationMode.FCFF_NORMALIZED,
        strategy_cls=FundamentalFCFFStrategy,
        auditor_cls_name="DCFAuditor",
        ui_renderer_name="render_expert_fcff_fundamental",
        display_name="FCFF Fundamental"
    )
    
    StrategyRegistry.register(
        mode=ValuationMode.FCFF_REVENUE_DRIVEN,
        strategy_cls=RevenueBasedStrategy,
        auditor_cls_name="DCFAuditor",
        ui_renderer_name="render_expert_fcff_growth",
        display_name="FCFF Growth"
    )
    
    # Approche Actionnaire (Direct Equity - Ke Based)
    StrategyRegistry.register(
        mode=ValuationMode.FCFE_TWO_STAGE,
        strategy_cls=FCFEStrategy,
        auditor_cls_name="FCFEAuditor",
        ui_renderer_name="render_expert_fcfe",
        display_name="FCFE Direct Equity"
    )
    
    StrategyRegistry.register(
        mode=ValuationMode.DDM_GORDON_GROWTH,
        strategy_cls=DividendDiscountStrategy,
        auditor_cls_name="DDMAuditor",
        ui_renderer_name="render_expert_ddm",
        display_name="DDM Dividendes"
    )
    
    # Autres Modèles (RIM & Graham)
    StrategyRegistry.register(
        mode=ValuationMode.RESIDUAL_INCOME_MODEL,
        strategy_cls=RIMBankingStrategy,
        auditor_cls_name="RIMAuditor",
        ui_renderer_name="render_expert_rim",
        display_name="RIM Residual Income"
    )
    
    StrategyRegistry.register(
        mode=ValuationMode.GRAHAM_1974_REVISED,
        strategy_cls=GrahamNumberStrategy,
        auditor_cls_name="GrahamAuditor",
        ui_renderer_name="render_expert_graham",
        display_name="Graham"
    )
    
    logger.info(f"[Registry] {len(StrategyRegistry._strategies)} stratégies enregistrées")


# Auto-enregistrement au chargement du module
_register_all_strategies()
