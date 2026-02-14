"""
src/models/enums.py

GLOBAL ENUMERATIONS
===================
Role: Single source of truth for fixed choices (Dropdowns, Strategies, Sectors).
Responsibility: Defines valid states and types for Pydantic validation.
Architecture: String Enums for easy JSON serialization and UI binding.
Style: NumPy docstrings.
"""

from enum import Enum


class ValuationMethodology(str, Enum):
    """
    Supported valuation strategies available in the engine.
    """

    FCFF_STANDARD = "FCFF_STANDARD"
    FCFF_NORMALIZED = "FCFF_NORMALIZED"
    FCFF_GROWTH = "FCFF_GROWTH"
    FCFE = "FCFE"
    DDM = "DDM"
    RIM = "RIM"
    GRAHAM = "GRAHAM"

    @property
    def is_direct_equity(self) -> bool:
        """
        Determines if the model calculates Equity Value directly.

        Returns
        -------
        bool
            True if the model skips Enterprise Value (DDM, RIM, FCFE).
        """
        return self in [ValuationMethodology.DDM, ValuationMethodology.RIM, ValuationMethodology.FCFE]


class TerminalValueMethod(str, Enum):
    """
    Method used to calculate the value beyond the projection horizon.
    """

    GORDON_GROWTH = "GORDON_GROWTH"
    EXIT_MULTIPLE = "EXIT_MULTIPLE"
    # Legacy/Fallback
    PERPETUAL_GROWTH = "Perpetual Growth"


class DiscountRateMethod(str, Enum):
    """
    Method used to derive the cost of capital.
    """

    CAPM = "CAPM"  # Capital Asset Pricing Model
    BUILD_UP = "Build-Up"  # Additive risk premiums


class ParametersSource(str, Enum):
    """
    Provenance of a specific input parameter value.
    Used during the 'Ghost Box' resolution to track data origin.
    """

    MANUAL = "USER_INPUT"  # Expert override via UI
    AUTO = "PROVIDER_INPUT"  # Market data provider (Yahoo)
    SYSTEM = "SYSTEM_INPUT"  # Internal fallback or sector benchmark
    EMPTY = "EMPTY"  # Placeholder for missing data


class VariableSource(str, Enum):
    """
    Provenance of a specific variable within a calculation step.
    Essential for the 'Glass Box' audit trail and UI coloring.
    """

    # 1. External Data
    YAHOO_FINANCE = "YAHOO_FINANCE"  # Raw provider data
    YAHOO_TTM_SIMPLE = "YAHOO_TTM_SIMPLE"  # Aggregated TTM data
    MACRO_PROVIDER = "MACRO_PROVIDER"  # Risk-free rates, ERP, Yields

    # 2. User Input
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"  # User forced value

    # 3. Internal Logic
    SYSTEM = "SYSTEM"  # Hardcoded defaults (e.g., 10 years)
    DEFAULT = "DEFAULT"  # Fallback constants

    # 4. Computed Results
    CALCULATED = "CALCULATED"  # Result of a math operation
    FORMULA = "FORMULA"  # Specific formula application (e.g., Graham)
    EV_CALC = "EV_CALC"  # Enterprise Value specific steps


class SOTPMethod(str, Enum):
    """
    Valuation techniques for segment-based analysis (Sum-Of-The-Parts).
    """

    DCF = "DCF"
    MULTIPLES = "MULTIPLES"
    ASSET_VALUE = "ASSET_VALUE"


class DiagnosticLevel(str, Enum):
    """
    Classification levels for audit trace findings.
    """

    CRITICAL = "CRITICAL"  # Prevents calculation
    WARNING = "WARNING"  # Calculation proceeds with risk
    INFO = "INFO"  # Informational note


class CompanySector(str, Enum):
    """
    High-level GICS Sectors used for fallback logic and peer selection.

    Note: Keys must align with `src/config/sector_multiples.py`.
    """

    # Technology
    TECHNOLOGY = "technology"
    SOFTWARE_INFRA = "software_infrastructure"
    SOFTWARE_APPS = "software_application"
    SEMICONDUCTORS = "semiconductors"
    CONSUMER_ELECTRONICS = "consumer_electronics"

    # Financials
    FINANCIAL_SERVICES = "financial_services"
    BANKS_DIVERSIFIED = "banks_diversified"
    BANKS_REGIONAL = "banks_regional"
    INSURANCE = "insurance_diversified"
    ASSET_MANAGEMENT = "asset_management"
    REAL_ESTATE = "real_estate_reit"

    # Healthcare
    HEALTHCARE = "healthcare"
    PHARMA = "drug_manufacturers_general"
    BIOTECH = "biotechnology"
    MEDICAL_DEVICES = "medical_devices"
    HEALTHCARE_PLANS = "healthcare_plans"

    # Consumer
    CONSUMER_CYCLICAL = "consumer_cyclical"
    AUTO = "auto_manufacturers"
    LUXURY = "luxury_goods"
    INTERNET_RETAIL = "internet_retail"
    RESTAURANTS = "restaurants"
    CONSUMER_DEFENSIVE = "consumer_defensive"
    BEVERAGES = "beverages_non_alcoholic"
    FOOD = "packaged_foods"
    TOBACCO = "tobacco"

    # Industry & Energy
    INDUSTRIALS = "industrials"
    AEROSPACE = "aerospace_defense"
    MACHINERY = "specialty_industrial_machinery"
    RAILROADS = "railroads"
    ENERGY = "energy"
    OIL_GAS_INTEGRATED = "oil_gas_integrated"
    OIL_GAS_EP = "oil_gas_e_p"
    RENEWABLE = "renewable_energy"
    CHEMICALS = "chemicals"

    # Services & Utilities
    COMMUNICATION_SERVICES = "communication_services"
    INTERNET_CONTENT = "internet_content_information"
    TELECOM = "telecom_services"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities_regulated"

    # Fallback
    UNKNOWN = "default"
