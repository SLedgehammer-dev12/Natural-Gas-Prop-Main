import os

filepath = "natural_gas_main/models/calculator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: _calculate_heating_values should pass 'HEOS' (or SRK) if backend is AGA8
old_hv = """    def _calculate_heating_values(
        self,
        mixture: GasMixture,
        rho_std: float,
        sg: float,
        backend: str,
        T_ref: float,
        P_ref: float
    ) -> Optional[HeatingValues]:"""

new_hv = """    def _calculate_heating_values(
        self,
        mixture: GasMixture,
        rho_std: float,
        sg: float,
        backend: str,
        T_ref: float,
        P_ref: float
    ) -> Optional[HeatingValues]:
        # CoolProp API requires CoolProp backends
        if backend in ["GERG-2008", "AGA8-Detail"]:
            backend = "HEOS" if not mixture.check_heos_compatibility() else "SRK"
"""

content = content.replace(old_hv, new_hv)

# Fix 2: _calculate_volume_conversion should also use a valid CoolProp backend
old_vc = """        if volume_m3 is not None:
            volume_results = self._calculate_volume_conversion(
                volume_m3,
                actual_results.density,
                standard_results.density_std,
                mixture,
                backend
            )"""

new_vc = """        if volume_m3 is not None:
            cp_backend = backend
            if cp_backend in ["GERG-2008", "AGA8-Detail"]:
                cp_backend = "HEOS" if not mixture.check_heos_compatibility() else "SRK"
                
            volume_results = self._calculate_volume_conversion(
                volume_m3,
                actual_results.density,
                standard_results.density_std,
                mixture,
                cp_backend
            )"""

content = content.replace(old_vc, new_vc)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched calculator for CoolProp fallbacks.")
