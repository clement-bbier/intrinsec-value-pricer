"""
src/models/enums.py

GLOBAL ENUMERATIONS
===================
Role: Single source of truth for fixed choices (Dropdowns, Strategies, Sectors).
Style: String Enums for easy serialization.
"""

from enum import Enum

class ValuationMethodology(str, Enum):
    """Supported valuation strategies available in the engine."""
    FCFF_STANDARD = "FCFF_STANDARD"
    FCFF_NORMALIZED = "FCFF_NORMALIZED"
    FCFF_GROWTH = "FCFF_GROWTH"
    FCFE = "FCFE"
    DDM = "DDM"
    RIM = "RIM"
    GRAHAM = "GRAHAM"

    @property
    def is_direct_equity(self) -> bool:
        """True if the model values equity directly (DDM, RIM, FCFE)."""
        return self in [ValuationMethodology.DDM, ValuationMethodology.RIM, ValuationMethodology.FCFE]

class TerminalValueMethod(str, Enum):
    """Method used to calculate the value beyond the projection horizon."""
    GORDON_GROWTH = None
    PERPETUAL_GROWTH = "Perpetual Growth"
    EXIT_MULTIPLE = "Exit Multiple"

class DiscountRateMethod(str, Enum):
    """Method used to derive the cost of capital."""
    CAPM = "CAPM"        # Capital Asset Pricing Model
    BUILD_UP = "Build-Up" # Additive risk premiums

class ParametersSource(str, Enum):
    """
    Provenance of a specific parameter value (Inputs).
    Used for the 'Ghost Box' resolution dance.
    """
    MANUAL = "USER_INPUT"        # Expert override
    AUTO = "PROVIDER_INPUT"      # Market data provider (Yahoo)
    SYSTEM = "SYSTEM_INPUT"      # Internal fallback or sector benchmark
    EMPTY = None

class VariableSource(str, Enum):
    """
    Provenance of a specific variable within a calculation step (Traceability).
    """
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"  # Expert input
    YAHOO_FINANCE = "YAHOO_FINANCE"  # Data Provider
    SYSTEM = "SYSTEM"  # Resolver / Internal Logic
    CALCULATED = "CALCULATED"  # Mathematical Result
    DEFAULT = "DEFAULT"  # Static Fallback constant

class SOTPMethod(str, Enum):
    """Valuation techniques for segment-based analysis."""
    DCF = "DCF"
    MULTIPLES = "MULTIPLES"
    ASSET_VALUE = "ASSET_VALUE"

class DiagnosticLevel(str, Enum):
    """Classification levels for trace findings."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class CompanySector(str, Enum):
    """
    High-level GICS Sectors used for fallback logic.
    Keys must match those defined in src/config/sector_multiples.py.
    """
    TECHNOLOGY = "technology"
    SOFTWARE_INFRA = "software_infrastructure"
    SOFTWARE_APPS = "software_application"
    SEMICONDUCTORS = "semiconductors"
    CONSUMER_ELECTRONICS = "consumer_electronics"
    FINANCIAL_SERVICES = "financial_services"
    BANKS_DIVERSIFIED = "banks_diversified"
    BANKS_REGIONAL = "banks_regional"
    INSURANCE = "insurance_diversified"
    ASSET_MANAGEMENT = "asset_management"
    HEALTHCARE = "healthcare"
    PHARMA = "drug_manufacturers_general"
    BIOTECH = "biotechnology"
    MEDICAL_DEVICES = "medical_devices"
    HEALTHCARE_PLANS = "healthcare_plans"
    CONSUMER_CYCLICAL = "consumer_cyclical"
    AUTO = "auto_manufacturers"
    LUXURY = "luxury_goods"
    INTERNET_RETAIL = "internet_retail"
    RESTAURANTS = "restaurants"
    CONSUMER_DEFENSIVE = "consumer_defensive"
    BEVERAGES = "beverages_non_alcoholic"
    FOOD = "packaged_foods"
    TOBACCO = "tobacco"
    INDUSTRIALS = "industrials"
    AEROSPACE = "aerospace_defense"
    MACHINERY = "specialty_industrial_machinery"
    RAILROADS = "railroads"
    ENERGY = "energy"
    OIL_GAS_INTEGRATED = "oil_gas_integrated"
    OIL_GAS_EP = "oil_gas_e_p"
    RENEWABLE = "renewable_energy"
    COMMUNICATION_SERVICES = "communication_services"
    INTERNET_CONTENT = "internet_content_information"
    TELECOM = "telecom_services"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities_regulated"
    CHEMICALS = "chemicals"
    REAL_ESTATE = "real_estate_reit"
    UNKNOWN = "default"