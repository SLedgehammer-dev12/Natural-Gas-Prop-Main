"""
Application configuration settings.

Centralizes all constants, limits, and configurable parameters.
"""

from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict


class AppConfig(BaseModel):
    """Application configuration with validation."""
    
    # Physical Constants
    P_ATM_BAR: float = Field(
        default=1.01325,
        description="Standard atmospheric pressure (bar absolute)"
    )
    P_ATM_PSI: float = Field(
        default=14.6959,
        description="Standard atmospheric pressure (psi absolute)"
    )
    
    # Standard Conditions (ISO 13443 default)
    T_STANDARD: float = Field(
        default=288.15,
        description="Standard temperature (K) - 15°C"
    )
    P_STANDARD: float = Field(
        default=101325.0,
        description="Standard pressure (Pa) - 101.325 kPa"
    )
    
    # Normal Conditions (0°C, 1 atm) - for NCM calculation
    T_NORMAL: float = Field(
        default=273.15,
        description="Normal temperature (K) - 0°C"
    )
    P_NORMAL: float = Field(
        default=101325.0,
        description="Normal pressure (Pa) - 101.325 kPa"
    )

    # Predefined Standard Conditions
    STANDARD_CONDITIONS: dict = Field(
        default={
            "ISO 13443 (15°C, 1 atm)": {"T": 288.15, "P": 101325.0},
            "GPA 2172 (60°F, 14.696 psi)": {"T": 288.706, "P": 101325.0},
            "API MPMS (60°F, 14.73 psi)": {"T": 288.706, "P": 101560.0},
            "EPDK (15°C, 1.01325 bar)": {"T": 288.15, "P": 101325.0},
            "GOST 2939 (20°C, 1 atm)": {"T": 293.15, "P": 101325.0},
            "Normal Şartlar (0°C, 1 atm)": {"T": 273.15, "P": 101325.0},
        },
        description="Predefined standard conditions"
    )
    
    # Calculation Limits
    MAX_COMPONENTS: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of gas components in mixture"
    )
    MIN_TEMPERATURE: float = Field(
        default=0.1,
        description="Minimum temperature (K)"
    )
    MAX_TEMPERATURE: float = Field(
        default=5000.0,
        description="Maximum temperature (K)"
    )
    MIN_PRESSURE: float = Field(
        default=1e-10,
        description="Minimum pressure (Pa)"
    )
    MAX_PRESSURE: float = Field(
        default=1e9,
        description="Maximum pressure (Pa) - ~10000 bar"
    )
    MIN_VOLUME: float = Field(
        default=1e-10,
        description="Minimum volume (m³)"
    )
    MAX_VOLUME: float = Field(
        default=1e9,
        description="Maximum volume (m³)"
    )

    # Extrapolation warning thresholds (industrial relevance)
    # Natural gas pyrolyzes above ~700 K and AGA8 is not defined above ~65 MPa.
    # Values beyond these are allowed but flagged as engineering extrapolation.
    EXTRAPOLATION_TEMP_K: float = Field(
        default=1000.0,
        description="Above this temperature results are extrapolation (K)"
    )
    EXTRAPOLATION_PRESS_PA: float = Field(
        default=70_000_000.0,
        description="Above this pressure results are extrapolation (Pa) - ~700 bar"
    )
    
    # UI Settings
    WINDOW_WIDTH: int = Field(
        default=1050,
        description="Main window width (pixels)"
    )
    WINDOW_HEIGHT: int = Field(
        default=850,
        description="Main window height (pixels)"
    )
    WINDOW_TITLE: str = Field(
        default="Termodinamik Gaz Karışımı Hesaplayıcı (Sürüm v1.8.0 - Modüler)",
        description="Application window title"
    )
    UI_THEME: str = Field(
        default="clam",
        description="TTK theme name (Deprecated in 5.2)"
    )
    CTK_THEME: str = Field(
        default="System", # System, dark, light
        description="CustomTkinter appearance mode"
    )
    CTK_COLOR_THEME: str = Field(
        default="blue", # blue, green, dark-blue
        description="CustomTkinter color theme"
    )
    
    # Logging Configuration
    LOG_FILE: str = Field(
        default="thermo_gas_calculator.log",
        description="Log file path (relative paths resolve to user home directory)"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    LOG_ENCODING: str = Field(
        default="utf-8-sig",
        description="Log file encoding"
    )
    
    # Calculation Settings
    DEFAULT_BACKEND: str = Field(
        default="neqsim-gerg2008",
        description="Default thermodynamic backend"
    )
    AVAILABLE_BACKENDS: List[str] = Field(
        default=[
            # --- NeqSim Backends (15 EOS) ---
            "neqsim-gerg2008", "neqsim-gerg2008-h2", "neqsim-eoscg",
            "neqsim-spanwagner", "neqsim-umrpru",
            "neqsim-srk-cpa",
            "neqsim-soreide",
            "neqsim-srk", "neqsim-srk-peneloux",
            "neqsim-srk-mc", "neqsim-srk-twucoon",
            "neqsim-pr", "neqsim-pr-mc",
            "neqsim-pr-twucoon", "neqsim-pr-danesh",
            # --- Existing CoolProp/AGA8 Backends ---
            "GERG-2008", "AGA8-Detail", "HEOS", "SRK", "PR",
        ],
        description="Available thermodynamic backends"
    )
    
    # HEOS Compatible Gases (for mixture calculations)
    HEOS_COMPATIBLE_GASES: List[str] = Field(
        default=[
            "Methane", "Ethane", "n-Propane", "Propane", "n-Butane", "IsoButane",
            "Isobutane", "n-Pentane", "Isopentane", "Neopentane", "n-Hexane",
            "Isohexane", "n-Heptane", "n-Octane", "n-Nonane", "n-Decane",
            "n-Undecane", "n-Dodecane", "Nitrogen", "CarbonDioxide",
            "HydrogenSulfide", "CarbonylSulfide", "SulfurDioxide", "Water",
            "Hydrogen", "Oxygen", "Argon", "Helium", "CarbonMonoxide",
            "Ethylene", "Propylene", "1-Butene", "IsoButene", "cis-2-Butene",
            "trans-2-Butene", "CycloPropane", "Cyclopentane", "CycloHexane",
            "Ammonia", "Neon", "Krypton", "Xenon",
            "Methanol"
        ],
        description="Gases compatible with HEOS backend for mixtures"
    )
    
    # Fallback Gas List (if CoolProp fails to load)
    FALLBACK_GAS_LIST: List[str] = Field(
        default=[
            "Methane", "Ethane", "n-Propane", "Propane", "n-Butane", "IsoButane",
            "n-Pentane", "Isopentane", "n-Hexane", "n-Heptane", "n-Octane",
            "n-Nonane", "n-Decane", "Nitrogen", "CarbonDioxide",
            "HydrogenSulfide", "CarbonylSulfide", "Water", "Hydrogen", "Helium",
            "Oxygen", "Argon", "CarbonMonoxide", "Ethylene", "Propylene", "Air",
            "Methanol", "MEG", "TEG",
        ],
        description="Fallback gas list when CoolProp database unavailable"
    )
    
    # Filtered Gas List (Natural Gas Focus) to hide refrigerants
    NATURAL_GAS_FOCUS_LIST: List[str] = Field(
        default=[
            # Main natural gas hydrocarbons and C5+ representatives
            "Methane", "Ethane", "n-Propane", "Propane", "n-Butane", "IsoButane",
            "Isobutane", "n-Pentane", "Isopentane", "Neopentane", "n-Hexane",
            "Isohexane", "n-Heptane", "n-Octane", "n-Nonane", "n-Decane",
            "n-Undecane", "n-Dodecane",
            # Inerts, acid gases, trace gases and unsaturated hydrocarbons
            "Nitrogen", "CarbonDioxide", "HydrogenSulfide", "CarbonylSulfide",
            "SulfurDioxide", "Water", "Oxygen", "Argon", "Hydrogen",
            "CarbonMonoxide", "Helium", "Ethylene", "Propylene", "1-Butene",
            "IsoButene", "cis-2-Butene", "trans-2-Butene", "CycloPropane",
            "Cyclopentane", "CycloHexane", "Ammonia", "Neon", "Krypton",
            "Xenon", "Air",
            # Hydrate inhibitors (NeqSim CPA-compatible)
            "Methanol", "MEG", "TEG",
        ],
        description="Relevant natural gas components for UI filtering"
    )
    
    # Conversion Constants
    MMBTU_PER_MJ: float = Field(
        default=9.4781712e-4,
        description="MMBtu per MJ conversion factor"
    )
    M3_TO_SCF: float = Field(
        default=35.3147,
        description="Cubic meters to standard cubic feet"
    )
    
    # Update Configuration
    APP_VERSION: str = Field(
        default="v1.8.0",
        description="Current application version"
    )
    REPO_USER: str = Field(
        default="SLedgehammer-dev12",
        description="GitHub username"
    )
    REPO_NAME: str = Field(
        default="Natural-Gas-Prop-Main",
        description="GitHub repository name"
    )
    BRANCH_NAME: str = Field(
        default="main",
        description="Branch name for updates"
    )
    
    @property
    def UPDATE_CHECK_URL(self) -> str:
        """Get URL to check for updates (raw JSON)."""
        return f"https://raw.githubusercontent.com/{self.REPO_USER}/{self.REPO_NAME}/{self.BRANCH_NAME}/version.json"

    @property
    def REPO_URL(self) -> str:
        """Get main repository URL."""
        return f"https://github.com/{self.REPO_USER}/{self.REPO_NAME}/tree/{self.BRANCH_NAME}"

    ENGINEERING_DISCLAIMER: str = Field(
        default=(
            "MÜHENDİSLİK SORUMLULUK REDDİ (ENGINEERING DISCLAIMER): "
            "Bu yazılım, termodinamik modeller (CoolProp, AGA8/ISO 20765, NeqSim, "
            "Standing-Katz) kullanarak yalnızca hesaplamalı TAHMİNLER üretir. Sonuçlar; "
            "güvenlik sınıfı tasarım, yasal/sözleşmesel faturalama veya kritik endüstriyel "
            "karar için doğrudan kullanıma uygun DEĞİLDİR. Tüm değerler yetkili bir mühendis "
            "tarafından ilgili standartlara (ISO 6976, AGA 8, ISO 13443 vb.) göre "
            "doğrulanmalı ve onaylanmalıdır. Yazılım sağlayıcısı, sonuçların kullanımından "
            "doğacak her türlü kayıp veya zarardan sorumlu tutulamaz."
        ),
        description="Engineering disclaimer shown in reports and dialogs"
    )

    def get_available_backends(self) -> List[str]:
        """Return available backends filtered by NeqSim availability.

        When Java/NeqSim is not available, NeqSim backends are hidden
        from the UI to keep the interface clean.
        """
        try:
            from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE
        except ImportError:
            NEQSIM_AVAILABLE = False
        if NEQSIM_AVAILABLE:
            return list(self.AVAILABLE_BACKENDS)
        return [b for b in self.AVAILABLE_BACKENDS if not b.startswith("neqsim-")]

    model_config = ConfigDict(validate_assignment=True, frozen=False)


# Global configuration instance
config = AppConfig()
