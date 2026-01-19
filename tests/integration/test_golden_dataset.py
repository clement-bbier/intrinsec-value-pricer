"""
tests/integration/test_golden_dataset.py

GOLDEN DATASET — Invariants Mathématiques de Non-Régression

Version : V1.0 — ST-1.3 Resolution
Pattern : Golden Master Testing
Style : Numpy Style docstrings

Ce fichier contient les valeurs de référence ("Golden") pour 50 tickers
représentatifs de différents secteurs (Tech, Banques, Industrie, etc.).

OBJECTIF CRITIQUE:
- Chaque refactorisation doit garantir que le résultat final ne dévie pas
  d'un centime par rapport au Golden Dataset.
- Ce test est exécuté automatiquement sur chaque Pull Request.

PROTOCOLE DE MISE À JOUR:
1. Si une modification INTENTIONNELLE change les résultats, mettre à jour ce fichier
2. Documenter la raison du changement dans le commit
3. Obtenir l'approbation d'un reviewer senior

RISQUES FINANCIERS:
- Une régression non détectée peut invalider toutes les valorisations
- Ce test est le garde-fou ultime contre les bugs de calcul
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP

from src.domain.models import (
    ValuationMode,
    CompanyFinancials,
    DCFParameters,
    GrowthParameters,
    CoreRateParameters,
    MonteCarloConfig,
)


# ==============================================================================
# 1. CONFIGURATION DU GOLDEN DATASET
# ==============================================================================

@dataclass(frozen=True)
class GoldenReference:
    """
    Référence Golden pour un ticker.
    
    Attributes
    ----------
    ticker : str
        Symbole du ticker.
    sector : str
        Secteur d'activité.
    mode : ValuationMode
        Mode de valorisation utilisé.
    intrinsic_value : Decimal
        Valeur intrinsèque de référence (en devise locale).
    tolerance_cents : int
        Tolérance en centimes (0 = exactitude parfaite).
    notes : str
        Notes sur le calcul de référence.
    """
    ticker: str
    sector: str
    mode: ValuationMode
    intrinsic_value: Decimal
    tolerance_cents: int = 0
    notes: str = ""


# ==============================================================================
# 2. GOLDEN DATASET — 50 TICKERS DE RÉFÉRENCE
# ==============================================================================

# NOTE: Ces valeurs sont calculées avec les paramètres par défaut du système
# et les données financières normalisées au 2026-01-01 (date de référence).
# 
# IMPORTANT: Les valeurs ci-dessous sont des PLACEHOLDERS initiaux.
# Elles doivent être recalculées et validées lors de la première exécution
# complète du système de valorisation.

GOLDEN_DATASET: List[GoldenReference] = [
    # =========================================================================
    # TECHNOLOGIE (10 tickers)
    # =========================================================================
    GoldenReference(
        ticker="AAPL",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),  # À calibrer
        notes="Apple Inc. - Référence Tech Mega Cap"
    ),
    GoldenReference(
        ticker="MSFT",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Microsoft Corp - Cloud Leader"
    ),
    GoldenReference(
        ticker="GOOGL",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Alphabet Inc. - Search & Cloud"
    ),
    GoldenReference(
        ticker="AMZN",
        sector="Technology",
        mode=ValuationMode.FCFF_GROWTH,
        intrinsic_value=Decimal("0.00"),
        notes="Amazon - E-commerce & AWS"
    ),
    GoldenReference(
        ticker="META",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Meta Platforms - Social Media"
    ),
    GoldenReference(
        ticker="NVDA",
        sector="Technology",
        mode=ValuationMode.FCFF_GROWTH,
        intrinsic_value=Decimal("0.00"),
        notes="NVIDIA - AI & GPU Leader"
    ),
    GoldenReference(
        ticker="TSM",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Taiwan Semiconductor - Foundry Leader"
    ),
    GoldenReference(
        ticker="ASML",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="ASML Holding - Semiconductor Equipment"
    ),
    GoldenReference(
        ticker="CRM",
        sector="Technology",
        mode=ValuationMode.FCFF_GROWTH,
        intrinsic_value=Decimal("0.00"),
        notes="Salesforce - Enterprise SaaS"
    ),
    GoldenReference(
        ticker="ORCL",
        sector="Technology",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Oracle Corp - Database & Cloud"
    ),
    
    # =========================================================================
    # BANQUES & FINANCE (10 tickers)
    # =========================================================================
    GoldenReference(
        ticker="JPM",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="JPMorgan Chase - US Banking Leader"
    ),
    GoldenReference(
        ticker="BAC",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="Bank of America - US Major Bank"
    ),
    GoldenReference(
        ticker="WFC",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="Wells Fargo - US Regional Leader"
    ),
    GoldenReference(
        ticker="GS",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="Goldman Sachs - Investment Banking"
    ),
    GoldenReference(
        ticker="MS",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="Morgan Stanley - Investment Banking"
    ),
    GoldenReference(
        ticker="C",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="Citigroup - Global Banking"
    ),
    GoldenReference(
        ticker="HSBC",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="HSBC Holdings - European Banking"
    ),
    GoldenReference(
        ticker="BNP.PA",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="BNP Paribas - French Banking Leader"
    ),
    GoldenReference(
        ticker="SAN",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="Santander - Spanish Banking"
    ),
    GoldenReference(
        ticker="UBS",
        sector="Banking",
        mode=ValuationMode.RIM,
        intrinsic_value=Decimal("0.00"),
        notes="UBS Group - Swiss Banking"
    ),
    
    # =========================================================================
    # INDUSTRIE (10 tickers)
    # =========================================================================
    GoldenReference(
        ticker="CAT",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Caterpillar - Heavy Equipment"
    ),
    GoldenReference(
        ticker="DE",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Deere & Co - Agricultural Equipment"
    ),
    GoldenReference(
        ticker="GE",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="GE Aerospace - Aviation"
    ),
    GoldenReference(
        ticker="HON",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Honeywell - Diversified Industrial"
    ),
    GoldenReference(
        ticker="UNP",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Union Pacific - Railroad"
    ),
    GoldenReference(
        ticker="RTX",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="RTX Corp - Defense & Aerospace"
    ),
    GoldenReference(
        ticker="LMT",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Lockheed Martin - Defense"
    ),
    GoldenReference(
        ticker="BA",
        sector="Industrials",
        mode=ValuationMode.FCFF_NORMALIZED,
        intrinsic_value=Decimal("0.00"),
        notes="Boeing - Commercial Aviation"
    ),
    GoldenReference(
        ticker="MMM",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="3M Company - Diversified Industrial"
    ),
    GoldenReference(
        ticker="ABB",
        sector="Industrials",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="ABB Ltd - Automation & Electrification"
    ),
    
    # =========================================================================
    # SANTÉ (5 tickers)
    # =========================================================================
    GoldenReference(
        ticker="JNJ",
        sector="Healthcare",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Johnson & Johnson - Pharma & MedTech"
    ),
    GoldenReference(
        ticker="UNH",
        sector="Healthcare",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="UnitedHealth - Healthcare Services"
    ),
    GoldenReference(
        ticker="PFE",
        sector="Healthcare",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Pfizer - Pharmaceuticals"
    ),
    GoldenReference(
        ticker="ABBV",
        sector="Healthcare",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="AbbVie - Biopharmaceuticals"
    ),
    GoldenReference(
        ticker="NVO",
        sector="Healthcare",
        mode=ValuationMode.FCFF_GROWTH,
        intrinsic_value=Decimal("0.00"),
        notes="Novo Nordisk - Diabetes & Obesity"
    ),
    
    # =========================================================================
    # CONSOMMATION (5 tickers)
    # =========================================================================
    GoldenReference(
        ticker="PG",
        sector="Consumer",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Procter & Gamble - Consumer Staples"
    ),
    GoldenReference(
        ticker="KO",
        sector="Consumer",
        mode=ValuationMode.DDM,
        intrinsic_value=Decimal("0.00"),
        notes="Coca-Cola - Beverages (Dividend Model)"
    ),
    GoldenReference(
        ticker="PEP",
        sector="Consumer",
        mode=ValuationMode.DDM,
        intrinsic_value=Decimal("0.00"),
        notes="PepsiCo - Beverages & Snacks (Dividend Model)"
    ),
    GoldenReference(
        ticker="WMT",
        sector="Consumer",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Walmart - Retail Giant"
    ),
    GoldenReference(
        ticker="COST",
        sector="Consumer",
        mode=ValuationMode.FCFF_STANDARD,
        intrinsic_value=Decimal("0.00"),
        notes="Costco - Warehouse Retail"
    ),
    
    # =========================================================================
    # ÉNERGIE (5 tickers)
    # =========================================================================
    GoldenReference(
        ticker="XOM",
        sector="Energy",
        mode=ValuationMode.FCFF_NORMALIZED,
        intrinsic_value=Decimal("0.00"),
        notes="Exxon Mobil - Oil & Gas Major"
    ),
    GoldenReference(
        ticker="CVX",
        sector="Energy",
        mode=ValuationMode.FCFF_NORMALIZED,
        intrinsic_value=Decimal("0.00"),
        notes="Chevron - Oil & Gas Major"
    ),
    GoldenReference(
        ticker="SHEL",
        sector="Energy",
        mode=ValuationMode.FCFF_NORMALIZED,
        intrinsic_value=Decimal("0.00"),
        notes="Shell PLC - European Oil Major"
    ),
    GoldenReference(
        ticker="TTE",
        sector="Energy",
        mode=ValuationMode.FCFF_NORMALIZED,
        intrinsic_value=Decimal("0.00"),
        notes="TotalEnergies - French Oil Major"
    ),
    GoldenReference(
        ticker="BP",
        sector="Energy",
        mode=ValuationMode.FCFF_NORMALIZED,
        intrinsic_value=Decimal("0.00"),
        notes="BP PLC - British Oil Major"
    ),
    
    # =========================================================================
    # UTILITIES & TELECOM (5 tickers)
    # =========================================================================
    GoldenReference(
        ticker="NEE",
        sector="Utilities",
        mode=ValuationMode.DDM,
        intrinsic_value=Decimal("0.00"),
        notes="NextEra Energy - Renewable Utilities"
    ),
    GoldenReference(
        ticker="DUK",
        sector="Utilities",
        mode=ValuationMode.DDM,
        intrinsic_value=Decimal("0.00"),
        notes="Duke Energy - Electric Utilities"
    ),
    GoldenReference(
        ticker="T",
        sector="Telecom",
        mode=ValuationMode.DDM,
        intrinsic_value=Decimal("0.00"),
        notes="AT&T - Telecommunications"
    ),
    GoldenReference(
        ticker="VZ",
        sector="Telecom",
        mode=ValuationMode.DDM,
        intrinsic_value=Decimal("0.00"),
        notes="Verizon - Telecommunications"
    ),
    GoldenReference(
        ticker="TMUS",
        sector="Telecom",
        mode=ValuationMode.FCFF_GROWTH,
        intrinsic_value=Decimal("0.00"),
        notes="T-Mobile US - Wireless Growth"
    ),
]


# ==============================================================================
# 3. FIXTURES ET HELPERS
# ==============================================================================

def round_to_cents(value: float) -> Decimal:
    """
    Arrondit une valeur au centime le plus proche.
    
    Args
    ----
    value : float
        Valeur à arrondir.
        
    Returns
    -------
    Decimal
        Valeur arrondie au centime.
    """
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def value_within_tolerance(
    calculated: float, 
    reference: Decimal, 
    tolerance_cents: int
) -> bool:
    """
    Vérifie si une valeur calculée est dans la tolérance.
    
    Args
    ----
    calculated : float
        Valeur calculée par le moteur.
    reference : Decimal
        Valeur de référence Golden.
    tolerance_cents : int
        Tolérance en centimes.
        
    Returns
    -------
    bool
        True si la valeur est dans la tolérance.
    """
    calculated_decimal = round_to_cents(calculated)
    tolerance = Decimal(str(tolerance_cents)) / Decimal("100")
    
    return abs(calculated_decimal - reference) <= tolerance


# ==============================================================================
# 4. TESTS GOLDEN DATASET
# ==============================================================================

class TestGoldenDatasetConfiguration:
    """Tests de validation de la configuration du Golden Dataset."""
    
    def test_golden_dataset_has_50_entries(self) -> None:
        """Vérifie que le dataset contient exactement 50 entrées."""
        assert len(GOLDEN_DATASET) == 50, (
            f"Golden Dataset should have 50 entries, found {len(GOLDEN_DATASET)}"
        )
    
    def test_all_sectors_represented(self) -> None:
        """Vérifie que tous les secteurs majeurs sont représentés."""
        sectors = {entry.sector for entry in GOLDEN_DATASET}
        required_sectors = {
            "Technology",
            "Banking",
            "Industrials",
            "Healthcare",
            "Consumer",
            "Energy",
            "Utilities",
            "Telecom",
        }
        
        missing = required_sectors - sectors
        assert not missing, f"Missing sectors: {missing}"
    
    def test_all_valuation_modes_covered(self) -> None:
        """Vérifie que les principaux modes de valorisation sont testés."""
        modes = {entry.mode for entry in GOLDEN_DATASET}
        required_modes = {
            ValuationMode.FCFF_STANDARD,
            ValuationMode.FCFF_GROWTH,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.DDM,
            ValuationMode.RIM,
        }
        
        missing = required_modes - modes
        assert not missing, f"Missing valuation modes: {missing}"
    
    def test_unique_tickers(self) -> None:
        """Vérifie que chaque ticker est unique dans le dataset."""
        tickers = [entry.ticker for entry in GOLDEN_DATASET]
        duplicates = [t for t in tickers if tickers.count(t) > 1]
        
        assert not duplicates, f"Duplicate tickers found: {set(duplicates)}"


@pytest.mark.skip(reason="Golden Dataset values must be calibrated first")
class TestGoldenDatasetValuation:
    """
    Tests de non-régression des valorisations.
    
    IMPORTANT: Ces tests sont désactivés jusqu'à la calibration initiale.
    Pour activer, supprimer le décorateur @pytest.mark.skip et exécuter
    une première fois pour générer les valeurs de référence.
    """
    
    @pytest.fixture
    def mock_financials(self, ticker: str) -> CompanyFinancials:
        """
        Génère des données financières mock pour un ticker.
        
        Notes
        -----
        En production, ces données seraient chargées depuis une source
        de données de référence (snapshot figé au 2026-01-01).
        """
        # TODO: Implémenter le chargement depuis un snapshot de données
        raise NotImplementedError(
            "Mock financials loader must be implemented for Golden Dataset testing"
        )
    
    @pytest.fixture
    def default_params(self) -> DCFParameters:
        """Retourne les paramètres DCF par défaut."""
        return DCFParameters(
            rates=CoreRateParameters(),
            growth=GrowthParameters(),
            monte_carlo=MonteCarloConfig(enable_monte_carlo=False),
        )
    
    @pytest.mark.parametrize(
        "golden_ref",
        GOLDEN_DATASET,
        ids=[f"{g.ticker}_{g.mode.name}" for g in GOLDEN_DATASET]
    )
    def test_intrinsic_value_matches_reference(
        self,
        golden_ref: GoldenReference,
        mock_financials,
        default_params,
    ) -> None:
        """
        Vérifie que la valeur intrinsèque calculée correspond à la référence.
        
        Financial Impact
        ----------------
        Une déviation de ce test indique une régression dans les calculs
        de valorisation. Toute modification intentionnelle doit être
        documentée et approuvée.
        """
        # Skip si valeur non calibrée
        if golden_ref.intrinsic_value == Decimal("0.00"):
            pytest.skip(f"Golden value not calibrated for {golden_ref.ticker}")
        
        # TODO: Implémenter l'appel au moteur de valorisation
        # from src.valuation.engines import run_valuation
        # from src.domain.models import ValuationRequest, InputSource
        # 
        # request = ValuationRequest(
        #     ticker=golden_ref.ticker,
        #     projection_years=5,
        #     mode=golden_ref.mode,
        #     input_source=InputSource.AUTO,
        # )
        # 
        # financials = mock_financials(golden_ref.ticker)
        # result = run_valuation(request, financials, default_params)
        # 
        # assert value_within_tolerance(
        #     result.intrinsic_value_per_share,
        #     golden_ref.intrinsic_value,
        #     golden_ref.tolerance_cents
        # ), (
        #     f"Golden Dataset violation for {golden_ref.ticker}:\n"
        #     f"  Expected: ${golden_ref.intrinsic_value}\n"
        #     f"  Got: ${round_to_cents(result.intrinsic_value_per_share)}\n"
        #     f"  Tolerance: {golden_ref.tolerance_cents} cents\n"
        #     f"  Mode: {golden_ref.mode.value}"
        # )
        
        pytest.skip("Full implementation pending data snapshot setup")


# ==============================================================================
# 5. UTILITIES POUR CALIBRATION
# ==============================================================================

def generate_golden_values() -> None:
    """
    Script utilitaire pour générer/mettre à jour les valeurs Golden.
    
    Usage:
        python -c "from tests.integration.test_golden_dataset import generate_golden_values; generate_golden_values()"
    
    ATTENTION: À n'exécuter que lors d'une calibration intentionnelle!
    """
    print("=" * 60)
    print("GOLDEN DATASET CALIBRATION")
    print("=" * 60)
    print()
    print("Ce script doit:")
    print("1. Charger les données financières de référence (snapshot)")
    print("2. Exécuter la valorisation pour chaque ticker")
    print("3. Afficher les valeurs calculées pour mise à jour manuelle")
    print()
    print("TODO: Implémenter le script de calibration")
    print()
    
    for ref in GOLDEN_DATASET:
        print(f"{ref.ticker:<10} | {ref.sector:<12} | {ref.mode.name:<18} | To calibrate")


if __name__ == "__main__":
    generate_golden_values()
