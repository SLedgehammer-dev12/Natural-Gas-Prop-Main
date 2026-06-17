"""
Gas data models and mixture handling.

Defines Pydantic models for gas components and mixtures with validation.
"""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator, computed_field
import re
import difflib

from natural_gas_main.config.settings import config
from natural_gas_main.core.exceptions import ValidationError


COOLPROP_NAME_MAP = {
    # Industry standard abbreviations (chromatography / GPA 2145)
    'co2': 'CarbonDioxide',
    'h2s': 'HydrogenSulfide',
    'n2': 'Nitrogen',
    'o2': 'Oxygen',
    'h2': 'Hydrogen',
    'h2o': 'Water',
    'he': 'Helium',
    'ar': 'Argon',
    'co': 'CarbonMonoxide',
    'c1': 'Methane',
    'c2': 'Ethane',
    'c3': 'n-Propane',
    'ic4': 'IsoButane',
    'nc4': 'n-Butane',
    'ic5': 'Isopentane',
    'nc5': 'n-Pentane',
    'c6': 'n-Hexane',
    'c7': 'n-Heptane',
    'c8': 'n-Octane',
    'c9': 'n-Nonane',
    'c10': 'n-Decane',
    'c11': 'n-Undecane',
    'c12': 'n-Dodecane',
    # Full names (original mappings)
    'methane': 'Methane',
    'ethane': 'Ethane',
    'propane': 'n-Propane',
    'npropane': 'n-Propane',
    'n-propane': 'n-Propane',
    'n-butane': 'n-Butane',
    'nbutane': 'n-Butane',
    'isobutane': 'IsoButane',
    'iso-butane': 'IsoButane',
    'nitrogen': 'Nitrogen',
    'carbondioxide': 'CarbonDioxide',
    'hydrogen': 'Hydrogen',
    'oxygen': 'Oxygen',
    'argon': 'Argon',
    'helium': 'Helium',
    'water': 'Water',
    'air': 'Air',
    'hydrogensulfide': 'HydrogenSulfide',
    'hydrogen-sulfide': 'HydrogenSulfide',
    'carbonmonoxide': 'CarbonMonoxide',
    'carbonylsulfide': 'CarbonylSulfide',
    'carbonyl-sulfide': 'CarbonylSulfide',
    'sulfurdioxide': 'SulfurDioxide',
    'sulfur-dioxide': 'SulfurDioxide',
    'n-pentane': 'n-Pentane',
    'npentane': 'n-Pentane',
    'isopentane': 'Isopentane',
    'neopentane': 'Neopentane',
    'n-hexane': 'n-Hexane',
    'nhexane': 'n-Hexane',
    'isohexane': 'Isohexane',
    'n-heptane': 'n-Heptane',
    'nheptane': 'n-Heptane',
    'n-octane': 'n-Octane',
    'noctane': 'n-Octane',
    'n-nonane': 'n-Nonane',
    'nnonane': 'n-Nonane',
    'n-decane': 'n-Decane',
    'ndecane': 'n-Decane',
    'n-undecane': 'n-Undecane',
    'nundecane': 'n-Undecane',
    'n-dodecane': 'n-Dodecane',
    'ndodecane': 'n-Dodecane',
    'ethylene': 'Ethylene',
    'propylene': 'Propylene',
    '1-butene': '1-Butene',
    '1butene': '1-Butene',
    'isobutene': 'IsoButene',
    'cis-2-butene': 'cis-2-Butene',
    'cis2butene': 'cis-2-Butene',
    'trans-2-butene': 'trans-2-Butene',
    'trans2butene': 'trans-2-Butene',
    'cyclopropane': 'CycloPropane',
    'cyclopentane': 'Cyclopentane',
    'cyclohexane': 'CycloHexane',
    'ammonia': 'Ammonia',
    'neon': 'Neon',
    'krypton': 'Krypton',
    'xenon': 'Xenon',
    # Hydrate inhibitors (for NeqSim CPA path)
    'methanol': 'Methanol',
    'meg': 'MEG',
    'teg': 'TEG',
    'mdea': 'MDEA',
    'dea': 'DEA',
    'mea': 'MEA',
    'r134a': 'R134a',
    'r22': 'R22',
    'r410a': 'R410A',
}


class GasComponent(BaseModel):
    """
    Represents a single gas component in a mixture.
    
    Attributes:
        name: Gas name (e.g., "Methane", "Ethane")
        fraction: Mole or mass fraction in percent (0-100)
    """
    
    name: str = Field(..., min_length=1, description="Gas component name")
    fraction: float = Field(..., gt=0, le=100, description="Fraction percentage (0-100)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean gas name."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Gas name cannot be empty")
        return cleaned
    
    @field_validator('fraction')
    @classmethod
    def validate_fraction(cls, v: float) -> float:
        """Validate fraction is in valid range."""
        if v <= 0 or v > 100:
            raise ValueError(f"Fraction must be between 0 and 100, got {v}")
        return v
    
    def to_decimal(self) -> float:
        """Convert percentage to decimal (0-1 range)."""
        return self.fraction / 100.0
    
    model_config = {"frozen": False, "validate_assignment": True}


class GasMixture(BaseModel):
    """
    Represents a mixture of multiple gas components.
    
    Attributes:
        components: List of gas components
        fraction_type: Type of fractions ("molar" or "mass")
    """
    
    components: List[GasComponent] = Field(..., min_length=1, max_length=20)
    fraction_type: Literal["molar", "mass"] = Field(default="molar")
    
    @field_validator('components')
    @classmethod
    def validate_components(cls, v: List[GasComponent]) -> List[GasComponent]:
        """Validate component list."""
        if not v:
            raise ValueError("At least one gas component is required")
        
        if len(v) > config.MAX_COMPONENTS:
            raise ValueError(
                f"Maximum {config.MAX_COMPONENTS} components allowed, got {len(v)}"
            )
        
        # Check for duplicate gas names (case-insensitive)
        names = [comp.name.lower() for comp in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate gas names are not allowed")
        
        return v
    
    @computed_field
    @property
    def total_fraction(self) -> float:
        """Calculate total fraction percentage."""
        return sum(comp.fraction for comp in self.components)
    
    def validate_total(self, tolerance: float = 1e-4) -> None:
        """
        Validate that fractions sum to 100%.

        Args:
            tolerance: Acceptable deviation from 100%

        Raises:
            ValidationError: If sum is not 100% within tolerance
        """
        total = self.total_fraction

        if abs(total - 100.0) > tolerance:
            raise ValidationError(
                "Gaz Kompozisyonu",
                f"Yüzdelerin toplamı 100 olmalıdır.  Mevcut toplam: {total:.4f}%"
            )

    def normalize_fractions(self) -> "GasMixture":
        """
        Scale all fractions so they sum to exactly 100%.

        Returns:
            A new GasMixture with normalized fractions (original is unchanged).
        
        Raises:
            ValidationError: If total is zero or negative (no valid fractions to scale).
        """
        total = self.total_fraction
        if total <= 0:
            raise ValidationError(
                "Gaz Kompozisyonu",
                "Toplam yüzde sıfır veya negatif olduğu için normalleştirme yapılamıyor."
            )
        scale = 100.0 / total
        normalized = [
            GasComponent(name=c.name, fraction=round(c.fraction * scale, 6))
            for c in self.components
        ]
        return GasMixture(components=normalized, fraction_type=self.fraction_type)
    
    def get_decimal_fractions(self) -> List[float]:
        """Get fractions as decimal values (0-1 range)."""
        return [comp.to_decimal() for comp in self.components]
    
    def get_gas_names(self) -> List[str]:
        """Get list of gas names."""
        return [comp.name for comp in self.components]
    
    def to_coolprop_string(self) -> str:
        """
        Convert mixture to CoolProp format string.
        
        Returns:
            Mixture string in format "Gas1&Gas2&Gas3"
            
        Examples:
            >>> mixture.to_coolprop_string()
            "Methane&Ethane&Propane"
        """
        formatted_names = [
            self._format_gas_name_for_coolprop(comp.name)
            for comp in self.components
        ]
        return '&'.join(formatted_names)
    
    @staticmethod
    def _format_gas_name_for_coolprop(gas_name: str) -> str:
        """
        Format gas name for CoolProp compatibility.

        Args:
            gas_name: Original gas name

        Returns:
            CoolProp-compatible gas name
        """
        clean_name = re.sub(r'\s+', '', gas_name.strip()).lower()
        return COOLPROP_NAME_MAP.get(clean_name, GasMixture._fuzzy_match_gas_name(clean_name))

    @staticmethod
    def _fuzzy_match_gas_name(clean_name: str) -> str:
        """
        Attempt fuzzy-matched gas name when exact mapping is not found.

        Uses difflib to find the closest known gas name. If no match
        exceeds a similarity threshold, returns the original name as-is.

        Args:
            clean_name: Lowercase, space-removed input name.

        Returns:
            Fuzzy-matched CoolProp name, or original name if no good match.
        """
        ratios = [
            (name, difflib.SequenceMatcher(None, clean_name, name).ratio())
            for name in COOLPROP_NAME_MAP
        ]
        best = max(ratios, key=lambda x: x[1])
        if best[1] >= 0.65:
            return COOLPROP_NAME_MAP[best[0]]
        return clean_name
    
    def check_heos_compatibility(self) -> List[str]:
        """
        Check which gases are incompatible with HEOS backend.
        
        Returns:
            List of incompatible gas names (empty if all compatible)
        """
        heos_compatible = [g.lower() for g in config.HEOS_COMPATIBLE_GASES]
        incompatible = [
            comp.name for comp in self.components
            if self._format_gas_name_for_coolprop(comp.name).lower() not in heos_compatible
        ]
        return incompatible
    
    model_config = {"frozen": False, "validate_assignment": True}
