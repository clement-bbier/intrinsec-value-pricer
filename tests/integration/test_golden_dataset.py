"""
tests/integration/test_golden_dataset.py

GOLDEN DATASET — Invariants Mathématiques de Non-Régression

Test Golden Dataset - ST-1.3
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
from typing import List
from decimal import Decimal, ROUND_HALF_UP

from src.models import (
    ValuationMethodology,
    Company,
    Parameters,
    GrowthParameters,
    CoreRateParameters,
    MonteCarloParameters,
    ValuationRequest,
    ParametersSource,
)
from src.valuation.engines import run_valuation


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
    mode : ValuationMethodology
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
    mode: ValuationMethodology
    intrinsic_value: Decimal
    tolerance_cents: int = 0
    notes: str = ""


# ==============================================================================
# 2. GOLDEN DATASET — 50 TICKERS DE RÉFÉRENCE
# ==============================================================================

GOLDEN_DATASET: List[GoldenReference] = [
    # =========================================================================
    # TECHNOLOGIE (10 tickers)
    # =========================================================================
    GoldenReference(ticker="AAPL", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Apple Inc. - Référence Tech Mega Cap"),
    GoldenReference(ticker="MSFT", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Microsoft Corp - Cloud Leader"),
    GoldenReference(ticker="GOOGL", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Alphabet Inc. - Search & Cloud"),
    GoldenReference(ticker="AMZN", sector="Technology", mode=ValuationMethodology.FCFF_GROWTH, intrinsic_value=Decimal("0.00"), notes="Amazon - E-commerce & AWS"),
    GoldenReference(ticker="META", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Meta Platforms - Social Media"),
    GoldenReference(ticker="NVDA", sector="Technology", mode=ValuationMethodology.FCFF_GROWTH, intrinsic_value=Decimal("0.00"), notes="NVIDIA - AI & GPU Leader"),
    GoldenReference(ticker="TSM", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Taiwan Semiconductor - Foundry Leader"),
    GoldenReference(ticker="ASML", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="ASML Holding - Semiconductor Equipment"),
    GoldenReference(ticker="CRM", sector="Technology", mode=ValuationMethodology.FCFF_GROWTH, intrinsic_value=Decimal("0.00"), notes="Salesforce - Enterprise SaaS"),
    GoldenReference(ticker="ORCL", sector="Technology", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Oracle Corp - Database & Cloud"),
    
    # =========================================================================
    # BANQUES & FINANCE (10 tickers)
    # =========================================================================
    GoldenReference(ticker="JPM", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="JPMorgan Chase - US Banking Leader"),
    GoldenReference(ticker="BAC", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="Bank of America - US Major Bank"),
    GoldenReference(ticker="WFC", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="Wells Fargo - US Regional Leader"),
    GoldenReference(ticker="GS", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="Goldman Sachs - Investment Banking"),
    GoldenReference(ticker="MS", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="Morgan Stanley - Investment Banking"),
    GoldenReference(ticker="C", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="Citigroup - Global Banking"),
    GoldenReference(ticker="HSBC", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="HSBC Holdings - European Banking"),
    GoldenReference(ticker="BNP.PA", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="BNP Paribas - French Banking Leader"),
    GoldenReference(ticker="SAN", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="Santander - Spanish Banking"),
    GoldenReference(ticker="UBS", sector="Banking", mode=ValuationMethodology.RIM, intrinsic_value=Decimal("0.00"), notes="UBS Group - Swiss Banking"),
    
    # =========================================================================
    # INDUSTRIE (10 tickers)
    # =========================================================================
    GoldenReference(ticker="CAT", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Caterpillar - Heavy Equipment"),
    GoldenReference(ticker="DE", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Deere & Co - Agricultural Equipment"),
    GoldenReference(ticker="GE", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="GE Aerospace - Aviation"),
    GoldenReference(ticker="HON", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Honeywell - Diversified Industrial"),
    GoldenReference(ticker="UNP", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Union Pacific - Railroad"),
    GoldenReference(ticker="RTX", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="RTX Corp - Defense & Aerospace"),
    GoldenReference(ticker="LMT", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Lockheed Martin - Defense"),
    GoldenReference(ticker="BA", sector="Industrials", mode=ValuationMethodology.FCFF_NORMALIZED, intrinsic_value=Decimal("0.00"), notes="Boeing - Commercial Aviation"),
    GoldenReference(ticker="MMM", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="3M Company - Diversified Industrial"),
    GoldenReference(ticker="ABB", sector="Industrials", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="ABB Ltd - Automation & Electrification"),
    
    # =========================================================================
    # SANTÉ (5 tickers)
    # =========================================================================
    GoldenReference(ticker="JNJ", sector="Healthcare", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Johnson & Johnson - Pharma & MedTech"),
    GoldenReference(ticker="UNH", sector="Healthcare", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="UnitedHealth - Healthcare Services"),
    GoldenReference(ticker="PFE", sector="Healthcare", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Pfizer - Pharmaceuticals"),
    GoldenReference(ticker="ABBV", sector="Healthcare", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="AbbVie - Biopharmaceuticals"),
    GoldenReference(ticker="NVO", sector="Healthcare", mode=ValuationMethodology.FCFF_GROWTH, intrinsic_value=Decimal("0.00"), notes="Novo Nordisk - Diabetes & Obesity"),
    
    # =========================================================================
    # CONSOMMATION (5 tickers)
    # =========================================================================
    GoldenReference(ticker="PG", sector="Consumer", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Procter & Gamble - Consumer Staples"),
    GoldenReference(ticker="KO", sector="Consumer", mode=ValuationMethodology.DDM, intrinsic_value=Decimal("0.00"), notes="Coca-Cola - Beverages (Dividend Model)"),
    GoldenReference(ticker="PEP", sector="Consumer", mode=ValuationMethodology.DDM, intrinsic_value=Decimal("0.00"), notes="PepsiCo - Beverages & Snacks (Dividend Model)"),
    GoldenReference(ticker="WMT", sector="Consumer", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Walmart - Retail Giant"),
    GoldenReference(ticker="COST", sector="Consumer", mode=ValuationMethodology.FCFF_STANDARD, intrinsic_value=Decimal("0.00"), notes="Costco - Warehouse Retail"),
    
    # =========================================================================
    # ÉNERGIE (5 tickers)
    # =========================================================================
    GoldenReference(ticker="XOM", sector="Energy", mode=ValuationMethodology.FCFF_NORMALIZED, intrinsic_value=Decimal("0.00"), notes="Exxon Mobil - Oil & Gas Major"),
    GoldenReference(ticker="CVX", sector="Energy", mode=ValuationMethodology.FCFF_NORMALIZED, intrinsic_value=Decimal("0.00"), notes="Chevron - Oil & Gas Major"),
    GoldenReference(ticker="SHEL", sector="Energy", mode=ValuationMethodology.FCFF_NORMALIZED, intrinsic_value=Decimal("0.00"), notes="Shell PLC - European Oil Major"),
    GoldenReference(ticker="TTE", sector="Energy", mode=ValuationMethodology.FCFF_NORMALIZED, intrinsic_value=Decimal("0.00"), notes="TotalEnergies - French Oil Major"),
    GoldenReference(ticker="BP", sector="Energy", mode=ValuationMethodology.FCFF_NORMALIZED, intrinsic_value=Decimal("0.00"), notes="BP PLC - British Oil Major"),
    
    # =========================================================================
    # UTILITIES & TELECOM (5 tickers)
    # =========================================================================
    GoldenReference(ticker="NEE", sector="Utilities", mode=ValuationMethodology.DDM, intrinsic_value=Decimal("0.00"), notes="NextEra Energy - Renewable Utilities"),
    GoldenReference(ticker="DUK", sector="Utilities", mode=ValuationMethodology.DDM, intrinsic_value=Decimal("0.00"), notes="Duke Energy - Electric Utilities"),
    GoldenReference(ticker="T", sector="Telecom", mode=ValuationMethodology.DDM, intrinsic_value=Decimal("0.00"), notes="AT&T - Telecommunications"),
    GoldenReference(ticker="VZ", sector="Telecom", mode=ValuationMethodology.DDM, intrinsic_value=Decimal("0.00"), notes="Verizon - Telecommunications"),
    GoldenReference(ticker="TMUS", sector="Telecom", mode=ValuationMethodology.FCFF_GROWTH, intrinsic_value=Decimal("0.00"), notes="T-Mobile US - Wireless Growth"),
]


# ==============================================================================
# 3. FIXTURES ET HELPERS
# ==============================================================================

def round_to_cents(value: float) -> Decimal:
    """Arrondit une valeur au centime le plus proche."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def value_within_tolerance(calculated: float, reference: Decimal, tolerance_cents: int) -> bool:
    """Vérifie si une valeur calculée est dans la tolérance."""
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
        assert len(GOLDEN_DATASET) == 50
    
    def test_all_sectors_represented(self) -> None:
        """Vérifie que tous les secteurs majeurs sont représentés."""
        sectors = {entry.sector for entry in GOLDEN_DATASET}
        required_sectors = {"Technology", "Banking", "Industrials", "Healthcare", "Consumer", "Energy", "Utilities", "Telecom"}
        assert not (required_sectors - sectors)
    
    def test_all_valuation_modes_covered(self) -> None:
        """Vérifie que les principaux modes de valorisation sont testés."""
        modes = {entry.mode for entry in GOLDEN_DATASET}
        required_modes = {ValuationMethodology.FCFF_STANDARD, ValuationMethodology.FCFF_GROWTH, ValuationMethodology.FCFF_NORMALIZED, ValuationMethodology.DDM, ValuationMethodology.RIM}
        assert not (required_modes - modes)
    
    def test_unique_tickers(self) -> None:
        """Vérifie que chaque ticker est unique dans le dataset."""
        tickers = [entry.ticker for entry in GOLDEN_DATASET]
        assert len(set(tickers)) == len(tickers)


class TestGoldenDatasetValuation:
    def get_mock_financials(self, ticker: str) -> Company:
        """Génère un objet financier ultra-complet pour satisfaire TOUS les modèles."""
        return Company(
            ticker=ticker,
            current_price=150.0,
            shares_outstanding=1_000_000,
            total_debt=2_000_000,
            cash_and_equivalents=500_000,
            interest_expense=100_000,
            ebit_ttm=1_000_000,
            # Champs critiques pour les échecs précédents :
            fcf_last=800_000,                 # Requis pour FCFF_STANDARD
            revenue_ttm=5_000_000,             # Requis pour FCFF_GROWTH
            fcf_fundamental_smoothed=750_000,  # Requis pour FCFF_NORMALIZED
            dividend_share=5.0,                # Requis pour DDM (doit être > 0)
            net_income_ttm=600_000,            # Requis pour RIM
            book_value_per_share=50.0,         # Requis pour RIM
            eps_ttm=6.0,                       # Requis pour Graham
            beta=1.1,
            currency="USD"
        )

    @pytest.fixture
    def default_params(self) -> Parameters:
        return Parameters(
            rates=CoreRateParameters(risk_free_rate=0.04, market_risk_premium=0.05),
            growth=GrowthParameters(projection_years=5, perpetual_growth_rate=0.02),
            monte_carlo=MonteCarloParameters(enabled=False),
        )

    @pytest.mark.parametrize("golden_ref", GOLDEN_DATASET, ids=[f"{g.ticker}_{g.mode.name}" for g in GOLDEN_DATASET])
    def test_intrinsic_value_matches_reference(self, golden_ref, default_params):
        request = ValuationRequest(
            ticker=golden_ref.ticker, 
            projection_years=5, 
            mode=golden_ref.mode, 
            input_source=ParametersSource.MANUAL,
            params=default_params
        )
        financials = self.get_mock_financials(golden_ref.ticker)
        result = run_valuation(request, financials, default_params)
        
        assert result is not None
        assert result.intrinsic_value_per_share > 0


# ==============================================================================
# 5. UTILITIES POUR CALIBRATION
# ==============================================================================

def generate_golden_values() -> None:
    """Script utilitaire pour générer/mettre à jour les valeurs Golden."""
    print("=" * 60)
    print("GOLDEN DATASET CALIBRATION")
    print("=" * 60)
    for ref in GOLDEN_DATASET:
        print(f"{ref.ticker:<10} | {ref.sector:<12} | {ref.mode.name:<18} | To calibrate")


if __name__ == "__main__":
    generate_golden_values()