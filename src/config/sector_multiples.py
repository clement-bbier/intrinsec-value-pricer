"""
src/config/sector_multiples.py

EXHAUSTIVE SECTORIAL & INDUSTRY ANCHORS — 2026 GLOBAL BENCHMARKS
================================================================
Role: Hardcoded fallback data for valuation when live peers are unavailable.
Sources: Damodaran (NYU), S&P Capital IQ, Refinitiv LTM Averages.
Style: Immutable Python Data Structures.
"""

from dataclasses import dataclass
from typing import Optional, Dict

# ==============================================================================
# 1. DATA STRUCTURE DEFINITION
# ==============================================================================

@dataclass(frozen=True)
class SectorBenchmarks:
    """Standardized financial multiples for a specific industry."""
    pe_ratio: float
    ev_ebitda: Optional[float]
    ev_revenue: Optional[float]
    pb_ratio: Optional[float] = None  # Price to Book (Banks/Insurance)
    source: str = "Consensus 2026"


# ==============================================================================
# 2. METADATA
# ==============================================================================

SECTOR_METADATA = {
    "version": "2026.01.04",
    "confidence_score": 0.88,
    "currency": "USD"
}

# ==============================================================================
# 3. SECTOR DATA (SINGLE SOURCE OF TRUTH)
# ==============================================================================

SECTORS: Dict[str, SectorBenchmarks] = {
    # --- TECHNOLOGY ---
    "technology": SectorBenchmarks(
        pe_ratio=28.5, ev_ebitda=19.2, ev_revenue=5.1, source="Tech Macro"
    ),
    "software_infrastructure": SectorBenchmarks(
        pe_ratio=38.4, ev_ebitda=24.5, ev_revenue=8.2, source="SaaS/Cloud"
    ),
    "software_application": SectorBenchmarks(
        pe_ratio=35.2, ev_ebitda=22.1, ev_revenue=7.5, source="App Software"
    ),
    "semiconductors": SectorBenchmarks(
        pe_ratio=26.8, ev_ebitda=18.5, ev_revenue=6.8, source="Semi Index"
    ),
    "consumer_electronics": SectorBenchmarks(
        pe_ratio=24.1, ev_ebitda=15.2, ev_revenue=3.8, source="Hardware"
    ),

    # --- FINANCIAL SERVICES ---
    "financial_services": SectorBenchmarks(
        pe_ratio=12.4, ev_ebitda=None, pb_ratio=1.2, ev_revenue=None, source="Finance Macro"
    ),
    "banks_diversified": SectorBenchmarks(
        pe_ratio=10.2, ev_ebitda=None, pb_ratio=1.1, ev_revenue=None, source="Global Banks"
    ),
    "banks_regional": SectorBenchmarks(
        pe_ratio=9.5, ev_ebitda=None, pb_ratio=0.9, ev_revenue=None, source="Regional Banks"
    ),
    "insurance_diversified": SectorBenchmarks(
        pe_ratio=11.8, ev_ebitda=None, pb_ratio=1.3, ev_revenue=None, source="Insurance"
    ),
    "asset_management": SectorBenchmarks(
        pe_ratio=14.5, ev_ebitda=10.2, ev_revenue=3.5, source="Asset Mgmt"
    ),

    # --- HEALTHCARE ---
    "healthcare": SectorBenchmarks(
        pe_ratio=22.5, ev_ebitda=14.8, ev_revenue=4.1, source="Health Macro"
    ),
    "drug_manufacturers_general": SectorBenchmarks(
        pe_ratio=18.4, ev_ebitda=12.1, ev_revenue=3.8, source="Big Pharma"
    ),
    "biotechnology": SectorBenchmarks(
        pe_ratio=42.1, ev_ebitda=28.4, ev_revenue=9.5, source="Biotech Growth"
    ),
    "medical_devices": SectorBenchmarks(
        pe_ratio=28.2, ev_ebitda=18.6, ev_revenue=5.4, source="MedTech"
    ),
    "healthcare_plans": SectorBenchmarks(
        pe_ratio=16.5, ev_ebitda=11.2, ev_revenue=0.8, source="Managed Care"
    ),

    # --- CONSUMER CYCLICAL ---
    "consumer_cyclical": SectorBenchmarks(
        pe_ratio=18.4, ev_ebitda=11.2, ev_revenue=1.6, source="Cyclical Macro"
    ),
    "auto_manufacturers": SectorBenchmarks(
        pe_ratio=8.2, ev_ebitda=6.4, ev_revenue=0.8, source="Auto Legacy"
    ),
    "luxury_goods": SectorBenchmarks(
        pe_ratio=26.5, ev_ebitda=17.2, ev_revenue=4.5, source="Luxury/High-End"
    ),
    "internet_retail": SectorBenchmarks(
        pe_ratio=32.1, ev_ebitda=16.5, ev_revenue=2.8, source= "E-Commerce"
    ),
    "restaurants": SectorBenchmarks(
        pe_ratio=22.4, ev_ebitda=14.2, ev_revenue=3.1, source="Quick Service"
    ),

    # --- CONSUMER DEFENSIVE ---
    "consumer_defensive": SectorBenchmarks(
        pe_ratio=19.8, ev_ebitda=13.5, ev_revenue=2.1, source="Defensive Macro"
    ),
    "beverages_non_alcoholic": SectorBenchmarks(
        pe_ratio=24.2, ev_ebitda=16.4, ev_revenue=4.2, source="Soft Drinks"
    ),
    "packaged_foods": SectorBenchmarks(
        pe_ratio=17.5, ev_ebitda=11.8, ev_revenue=1.8, source="Food Giants"
    ),
    "tobacco": SectorBenchmarks(
        pe_ratio=10.2, ev_ebitda=8.1, ev_revenue=3.5, source="Tobacco Yield"
    ),

    # --- INDUSTRIALS ---
    "industrials": SectorBenchmarks(
        pe_ratio=19.2, ev_ebitda=12.4, ev_revenue=1.4, source="Industrial Macro"
    ),
    "aerospace_defense": SectorBenchmarks(
        pe_ratio=21.5, ev_ebitda=14.2, ev_revenue=1.8, source="Defense/Aero"
    ),
    "specialty_industrial_machinery": SectorBenchmarks(
        pe_ratio=18.4, ev_ebitda=11.5, ev_revenue=1.6, source="Machinery"
    ),
    "railroads": SectorBenchmarks(
        pe_ratio=19.1, ev_ebitda=12.8, ev_revenue=4.5, source="Logistics"
    ),

    # --- ENERGY ---
    "energy": SectorBenchmarks(
        pe_ratio=10.2, ev_ebitda=5.6, ev_revenue=1.1, source="Energy Macro"
    ),
    "oil_gas_integrated": SectorBenchmarks(
        pe_ratio=9.8, ev_ebitda=4.8, ev_revenue=0.9, source="Big Oil"
    ),
    "oil_gas_e_p": SectorBenchmarks(
        pe_ratio=8.5, ev_ebitda=4.2, ev_revenue=2.1, source="E&P Mid"
    ),
    "renewable_energy": SectorBenchmarks(
        pe_ratio=35.4, ev_ebitda=20.2, ev_revenue=4.2, source="Clean Energy"
    ),

    # --- COMMUNICATION SERVICES ---
    "communication_services": SectorBenchmarks(
        pe_ratio=20.8, ev_ebitda=10.5, ev_revenue=3.1, source="Comm Macro"
    ),
    "internet_content_information": SectorBenchmarks(
        pe_ratio=28.4, ev_ebitda=15.2, ev_revenue=5.4, source="AdTech/Social"
    ),
    "telecom_services": SectorBenchmarks(
        pe_ratio=13.2, ev_ebitda=6.8, ev_revenue=1.5, source="Telco"
    ),
    "entertainment": SectorBenchmarks(
        pe_ratio=24.5, ev_ebitda=12.4, ev_revenue=3.2, source="Media/Streaming"
    ),

    # --- UTILITIES & MATERIALS ---
    "utilities_regulated": SectorBenchmarks(
        pe_ratio=17.8, ev_ebitda=10.8, ev_revenue=2.8, source="Utilities"
    ),
    "chemicals": SectorBenchmarks(
        pe_ratio=15.4, ev_ebitda=8.5, ev_revenue=1.3, source="Chemicals"
    ),
    "real_estate_reit": SectorBenchmarks(
        pe_ratio=30.5, ev_ebitda=18.2, ev_revenue=8.5, source="REITs"
    ),

    # --- SAFETY NET (DEFAULT) ---
    "default": SectorBenchmarks(
        pe_ratio=18.5, ev_ebitda=12.0, ev_revenue=2.2, source="Global Equity Composite"
    ),
}