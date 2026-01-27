"""
app/ui/expert_terminals/factory.py

FACTORY — Création dynamique des terminaux experts.

Factory des terminaux - Logical Path
Pattern : Factory Method (GoF)
Style : Numpy docstrings

La factory maintient un registre de tous les terminaux disponibles
et instancie le bon selon le mode de valorisation sélectionné.

HIÉRARCHIE ANALYTIQUE (ST-3.1 — McKinsey/Damodaran):
=====================================================
Les modes sont ordonnés selon une montée en puissance analytique :

1. DÉFENSIF (Quick Screening)
   - Graham Value : Barrière de sécurité conservatrice

2. RELATIF (Market Comparison)  
   - RIM Banks : Valorisation des institutions financières
   - DDM : Dividend Discount pour les entreprises matures

3. FONDAMENTAL (Intrinsic Value)
   - FCFF Standard : DCF classique pour entreprises stables
   - FCFF Normalized : DCF avec flux normalisés (cycliques)
   - FCFF Growth : DCF piloté par les revenus (high-growth)
   - FCFE : Direct Equity pour structures complexes

Usage :
    terminal = create_expert_terminal(ValuationMode.DDM, "AAPL")
    request = terminal.render()
"""

from __future__ import annotations

from typing import Dict, Type, List, Tuple
from dataclasses import dataclass
from enum import IntEnum

from src.models import ValuationMode
from src.i18n import SharedTexts
from .base_terminal import ExpertTerminalBase

# Import des terminaux concrets
from app.ui.expert.terminals.fcff_standard_terminal import FCFFStandardTerminal
from app.ui.expert.terminals.fcff_normalized_terminal import FCFFNormalizedTerminal
from app.ui.expert.terminals.fcff_growth_terminal import FCFFGrowthTerminal
from app.ui.expert.terminals.fcfe_terminal import FCFETerminal
from app.ui.expert.terminals.ddm_terminal import DDMTerminal
from app.ui.expert.terminals.rim_bank_terminal import RIMBankTerminal
from app.ui.expert.terminals.graham_value_terminal import GrahamValueTerminal


class AnalyticalTier(IntEnum):
    """
    Niveau de complexité analytique pour le tri des modèles.
    
    Plus le tier est bas, plus le modèle est simple/défensif.
    """
    DEFENSIVE = 1      # Screening rapide, barrière de sécurité
    RELATIVE = 2       # Comparaison marché, multiples
    FUNDAMENTAL = 3    # Valeur intrinsèque, DCF complet


@dataclass(frozen=True)
class TerminalMetadata:
    """
    Métadonnées d'un terminal pour le tri et l'affichage.
    
    Attributes
    ----------
    terminal_cls : Type[ExpertTerminalBase]
        Classe du terminal.
    tier : AnalyticalTier
        Niveau de complexité analytique.
    sort_order : int
        Ordre de tri au sein du tier.
    category_label : str
        Label de la catégorie pour l'affichage groupé.
    """
    terminal_cls: Type[ExpertTerminalBase]
    tier: AnalyticalTier
    sort_order: int
    category_label: str


class ExpertTerminalFactory:
    """
    Factory pour créer les terminaux experts.
    
    Le registre associe chaque ValuationMode à sa classe de terminal
    avec des métadonnées de tri selon la hiérarchie analytique.
    
    Notes
    -----
    ST-3.1 : Les modes sont ordonnés pour guider l'analyste dans une
    montée en puissance progressive : Défensif → Relatif → Fondamental.
    """
    
    # Registre enrichi avec métadonnées de tri (ST-3.1)
    _REGISTRY: Dict[ValuationMode, TerminalMetadata] = {
        # ══════════════════════════════════════════════════════════════════
        # TIER 1 : DÉFENSIF (Quick Screening)
        # ══════════════════════════════════════════════════════════════════
        ValuationMode.GRAHAM: TerminalMetadata(
            terminal_cls=GrahamValueTerminal,
            tier=AnalyticalTier.DEFENSIVE,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_DEFENSIVE
        ),
        
        # ══════════════════════════════════════════════════════════════════
        # TIER 2 : RELATIF (Market Comparison)
        # ══════════════════════════════════════════════════════════════════
        ValuationMode.RIM: TerminalMetadata(
            terminal_cls=RIMBankTerminal,
            tier=AnalyticalTier.RELATIVE,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_RELATIVE_SECTORIAL
        ),
        ValuationMode.DDM: TerminalMetadata(
            terminal_cls=DDMTerminal,
            tier=AnalyticalTier.RELATIVE,
            sort_order=2,
            category_label=SharedTexts.CATEGORY_RELATIVE_SECTORIAL
        ),
        
        # ══════════════════════════════════════════════════════════════════
        # TIER 3 : FONDAMENTAL (Intrinsic Value DCF)
        # ══════════════════════════════════════════════════════════════════
        ValuationMode.FCFF_STANDARD: TerminalMetadata(
            terminal_cls=FCFFStandardTerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=1,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMode.FCFF_NORMALIZED: TerminalMetadata(
            terminal_cls=FCFFNormalizedTerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=2,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMode.FCFF_GROWTH: TerminalMetadata(
            terminal_cls=FCFFGrowthTerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=3,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
        ValuationMode.FCFE: TerminalMetadata(
            terminal_cls=FCFETerminal,
            tier=AnalyticalTier.FUNDAMENTAL,
            sort_order=4,
            category_label=SharedTexts.CATEGORY_FUNDAMENTAL_DCF
        ),
    }
    
    @classmethod
    def create(cls, mode: ValuationMode, ticker: str) -> ExpertTerminalBase:
        """
        Crée le terminal approprié pour le mode donné.
        
        Parameters
        ----------
        mode : ValuationMode
            Le mode de valorisation.
        ticker : str
            Le symbole boursier.
        
        Returns
        -------
        ExpertTerminalBase
            Instance du terminal prête à être rendue.
        
        Raises
        ------
        ValueError
            Si le mode n'a pas de terminal associé.
        """
        metadata = cls._REGISTRY.get(mode)
        
        if metadata is None:
            available = ", ".join(m.value for m in cls._REGISTRY.keys())
            raise ValueError(
                f"Aucun terminal pour le mode '{mode.value}'. "
                f"Modes disponibles: {available}"
            )
        
        return metadata.terminal_cls(ticker)
    
    @classmethod
    def get_available_modes(cls) -> List[ValuationMode]:
        """
        Liste des modes triés selon la hiérarchie analytique (ST-3.1).
        
        Returns
        -------
        List[ValuationMode]
            Modes ordonnés : Défensif → Relatif → Fondamental.
        """
        return sorted(
            cls._REGISTRY.keys(),
            key=lambda m: (cls._REGISTRY[m].tier, cls._REGISTRY[m].sort_order)
        )
    
    @classmethod
    def get_mode_display_names(cls) -> Dict[ValuationMode, str]:
        """Mapping mode -> nom d'affichage."""
        return {
            mode: meta.terminal_cls.DISPLAY_NAME
            for mode, meta in cls._REGISTRY.items()
        }
    
    @classmethod
    def get_mode_descriptions(cls) -> Dict[ValuationMode, str]:
        """Mapping mode → description."""
        return {
            mode: meta.terminal_cls.DESCRIPTION
            for mode, meta in cls._REGISTRY.items()
        }
    
    @classmethod
    def get_modes_by_tier(cls) -> Dict[AnalyticalTier, List[Tuple[ValuationMode, TerminalMetadata]]]:
        """
        Retourne les modes groupés par tier analytique (ST-3.1).
        
        Returns
        -------
        Dict[AnalyticalTier, List[Tuple[ValuationMode, TerminalMetadata]]]
            Modes groupés et triés par niveau de complexité.
        
        Examples
        --------
        >> tiers = ExpertTerminalFactory.get_modes_by_tier()
        >> for tier, modes in tiers.items():
            print(f"{tier.name}: {[m.value for m, _ in modes]}")
        DEFENSIVE: ['Graham Intrinsic Value']
        RELATIVE: ['Residual Income Model', 'Dividend Discount Model']
        FUNDAMENTAL: ['DCF - Free Cash Flow to Firm', ...]
        """
        result: Dict[AnalyticalTier, List[Tuple[ValuationMode, TerminalMetadata]]] = {}
        
        for mode, meta in cls._REGISTRY.items():
            if meta.tier not in result:
                result[meta.tier] = []
            result[meta.tier].append((mode, meta))
        
        # Tri par sort_order au sein de chaque tier
        for tier in result:
            result[tier].sort(key=lambda x: x[1].sort_order)
        
        return result
    
    @classmethod
    def get_tier_label(cls, mode: ValuationMode) -> str:
        """
        Retourne le label de catégorie pour un mode donné.
        
        Parameters
        ----------
        mode : ValuationMode
            Le mode de valorisation.
            
        Returns
        -------
        str
            Label de catégorie (ex: "Défensif", "Fondamental (DCF)").
        """
        meta = cls._REGISTRY.get(mode)
        return meta.category_label if meta else SharedTexts.CATEGORY_OTHER


def create_expert_terminal(mode: ValuationMode, ticker: str) -> ExpertTerminalBase:
    """
    Raccourci pour créer un terminal expert.
    
    Parameters
    ----------
    mode : ValuationMode
        Le mode de valorisation.
    ticker : str
        Le symbole boursier.
    
    Returns
    -------
    ExpertTerminalBase
        Terminal prêt à être rendu.
    
    Example
    -------
    >> terminal = create_expert_terminal(ValuationMode.DDM, "AAPL")
    >> request = terminal.render()  # Affiche l'UI
    """
    return ExpertTerminalFactory.create(mode, ticker)
