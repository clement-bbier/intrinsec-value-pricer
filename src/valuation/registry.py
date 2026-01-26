"""
core/valuation/registry.py
REGISTRE CENTRALISÉ DES STRATÉGIES DE VALORISATION

Implémentation du pattern Registry avec Auto-Discovery par décorateur.
Assure l'alignement entre les moteurs de calcul, les auditeurs institutionnels
et les composants d'interface utilisateur via le module i18n.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Type, Optional, Callable, TYPE_CHECKING

from src.models import ValuationMode
from src.i18n import RegistryTexts  # Importation du référentiel i18n

if TYPE_CHECKING:
    from src.valuation.strategies.abstract import ValuationStrategy
    from infra.auditing.auditors import IValuationAuditor

logger = logging.getLogger(__name__)


@dataclass
class StrategyMetadata:
    """
    Métadonnées associées à une stratégie de valorisation.

    Attributes
    ----------
    mode : ValuationMode
        Identifiant unique du mode de valorisation.
    strategy_cls : Type[ValuationStrategy]
        Classe implémentant l'algorithme de valorisation.
    auditor_cls_name : str, default "DCFAuditor"
        Nom de la classe d'auditeur associée pour import différé.
    ui_renderer_name : Optional[str], default None
        Nom de la fonction de rendu UI pour le Terminal Expert.
    display_name : Optional[str], default None
        Libellé localisé (i18n) affiché dans l'application.
    """
    mode: ValuationMode
    strategy_cls: Type[ValuationStrategy]
    auditor_cls_name: str = "DCFAuditor"
    ui_renderer_name: Optional[str] = None
    display_name: Optional[str] = None

    def get_auditor_cls(self) -> Type[IValuationAuditor]:
        """
        Importe et résout dynamiquement la classe d'auditeur.

        Returns
        -------
        Type[IValuationAuditor]
            La classe d'auditeur spécialisée ou l'auditeur standard par défaut.
        """
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


class StrategyRegistry:
    """
    Registre global des algorithmes de valorisation (Singleton).

    Gère le cycle de vie et l'accès centralisé aux stratégies et à leurs
    métadonnées d'audit et d'interface.
    """

    _instance: Optional[StrategyRegistry] = None
    _strategies: Dict[ValuationMode, StrategyMetadata] = {}

    def __new__(cls) -> StrategyRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._strategies = {}
        return cls._instance

    @classmethod
    def register(
        cls,
        mode: ValuationMode,
        strategy_cls: Type[ValuationStrategy],
        auditor_cls_name: str = "DCFAuditor",
        ui_renderer_name: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> None:
        """
        Enregistre officiellement une stratégie dans le moteur de calcul.
        """
        metadata = StrategyMetadata(
            mode=mode,
            strategy_cls=strategy_cls,
            auditor_cls_name=auditor_cls_name,
            ui_renderer_name=ui_renderer_name,
            display_name=display_name or mode.value
        )
        cls._strategies[mode] = metadata
        logger.debug("[Registry] Strategy registered | mode=%s", mode.value)

    @classmethod
    def get_strategy_cls(cls, mode: ValuationMode) -> Optional[Type[ValuationStrategy]]:
        """Retourne la classe de calcul pour un mode spécifique."""
        metadata = cls._strategies.get(mode)
        return metadata.strategy_cls if metadata else None

    @classmethod
    def get_auditor_cls(cls, mode: ValuationMode) -> Type[IValuationAuditor]:
        """Retourne la classe d'audit associée au mode."""
        from infra.auditing.auditors import StandardValuationAuditor

        metadata = cls._strategies.get(mode)
        return metadata.get_auditor_cls() if metadata else StandardValuationAuditor

    @classmethod
    def get_ui_renderer_name(cls, mode: ValuationMode) -> Optional[str]:
        """Identifie le renderer Expert UI pour le mode donné."""
        metadata = cls._strategies.get(mode)
        return metadata.ui_renderer_name if metadata else None

    @classmethod
    def get_display_name(cls, mode: ValuationMode) -> str:
        """Récupère le nom localisé (i18n) du modèle."""
        metadata = cls._strategies.get(mode)
        return metadata.display_name if metadata else mode.value

    @classmethod
    def get_all_modes(cls) -> Dict[ValuationMode, StrategyMetadata]:
        """Fournit une copie du catalogue intégral des stratégies."""
        return cls._strategies.copy()

    @classmethod
    def get_display_names_map(cls) -> Dict[ValuationMode, str]:
        """Génère le mapping mode -> label pour les composants UI."""
        return {mode: meta.display_name for mode, meta in cls._strategies.items() if meta.display_name}


def register_strategy(
    mode: ValuationMode,
    auditor: str = "DCFAuditor",
    ui_renderer: Optional[str] = None,
    display_name: Optional[str] = None
) -> Callable[[Type[ValuationStrategy]], Type[ValuationStrategy]]:
    """
    Décorateur pour l'auto-enregistrement des stratégies de valorisation.
    """
    def decorator(cls: Type[ValuationStrategy]) -> Type[ValuationStrategy]:
        StrategyRegistry.register(
            mode=mode,
            strategy_cls=cls,
            auditor_cls_name=auditor,
            ui_renderer_name=ui_renderer,
            display_name=display_name
        )
        # Injection du mode pour introspection ultérieure
        setattr(cls, "_registered_mode", mode)
        return cls

    return decorator


def get_strategy(mode: ValuationMode) -> Optional[Type[ValuationStrategy]]:
    """Facade simplifiée pour l'accès aux classes de stratégie."""
    return StrategyRegistry.get_strategy_cls(mode)


def get_auditor(mode: ValuationMode) -> IValuationAuditor:
    """
    Instancie l'auditeur institutionnel associé au mode.

    Note : Résout l'erreur 'Unresolved reference' en nommant explicitement
    le type résolu.
    """
    target_auditor_cls = StrategyRegistry.get_auditor_cls(mode)
    return target_auditor_cls()


def get_all_strategies() -> Dict[ValuationMode, StrategyMetadata]:
    """Accès global au catalogue des métadonnées."""
    return StrategyRegistry.get_all_modes()


def get_display_names() -> Dict[ValuationMode, str]:
    """Accès simplifié au mapping des labels localisés (i18n)."""
    return StrategyRegistry.get_display_names_map()


def _register_all_strategies() -> None:
    """
    Initialisation du socle de stratégies standards via i18n.

    Utilise exclusivement RegistryTexts pour garantir l'internationalisation
    des noms d'affichage dans l'interface utilisateur.
    """
    from src.valuation.strategies.dcf_standard import StandardFCFFStrategy
    from src.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
    from src.valuation.strategies.dcf_growth import RevenueBasedStrategy
    from src.valuation.strategies.dcf_equity import FCFEStrategy
    from src.valuation.strategies.dcf_dividend import DividendDiscountStrategy
    from src.valuation.strategies.rim_banks import RIMBankingStrategy
    from src.valuation.strategies.graham_value import GrahamNumberStrategy

    # --- Approches Entité (WACC) ---
    StrategyRegistry.register(
        mode=ValuationMode.FCFF_STANDARD,
        strategy_cls=StandardFCFFStrategy,
        ui_renderer_name="render_expert_fcff_standard",
        display_name=RegistryTexts.FCFF_STANDARD_L  # Utilisation i18n
    )

    StrategyRegistry.register(
        mode=ValuationMode.FCFF_NORMALIZED,
        strategy_cls=FundamentalFCFFStrategy,
        ui_renderer_name="render_expert_fcff_fundamental",
        display_name=RegistryTexts.FCFF_NORM_L  # Utilisation i18n
    )

    StrategyRegistry.register(
        mode=ValuationMode.FCFF_GROWTH,
        strategy_cls=RevenueBasedStrategy,
        ui_renderer_name="render_expert_fcff_growth",
        display_name=RegistryTexts.FCFF_GROWTH_L  # Utilisation i18n
    )

    # --- Approches Actionnaire (Ke) ---
    StrategyRegistry.register(
        mode=ValuationMode.FCFE,
        strategy_cls=FCFEStrategy,
        auditor_cls_name="FCFEAuditor",
        ui_renderer_name="render_expert_fcfe",
        display_name=RegistryTexts.FCFE_L  # Utilisation i18n
    )

    StrategyRegistry.register(
        mode=ValuationMode.DDM,
        strategy_cls=DividendDiscountStrategy,
        auditor_cls_name="DDMAuditor",
        ui_renderer_name="render_expert_ddm",
        display_name=RegistryTexts.DDM_L  # Utilisation i18n
    )

    # --- Modèles Alternatifs ---
    StrategyRegistry.register(
        mode=ValuationMode.RIM,
        strategy_cls=RIMBankingStrategy,
        auditor_cls_name="RIMAuditor",
        ui_renderer_name="render_expert_rim",
        display_name=RegistryTexts.RIM_IV_L  # Utilisation i18n
    )

    StrategyRegistry.register(
        mode=ValuationMode.GRAHAM,
        strategy_cls=GrahamNumberStrategy,
        auditor_cls_name="GrahamAuditor",
        ui_renderer_name="render_expert_graham",
        display_name=RegistryTexts.GRAHAM_IV_L  # Utilisation i18n
    )

    # Résolution de l'accès protégé via méthode publique
    count = len(StrategyRegistry.get_all_modes())
    logger.info("[Registry] %d Strategies loaded successfully.", count)


# Amorçage initial du registre
_register_all_strategies()