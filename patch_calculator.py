import os

filepath = "natural_gas_main/models/calculator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add pyaga8 import
import_str = """
try:
    import pyaga8
    PYAGA8_AVAILABLE = True
    logging.info("pyaga8 başarıyla yüklendi")
except ImportError as e:
    logging.error(f"pyaga8 içe aktarılamadı: {e}")
    PYAGA8_AVAILABLE = False
"""
if "import pyaga8" not in content:
    content = content.replace('try:\n    import CoolProp.CoolProp as CP', import_str + '\ntry:\n    import CoolProp.CoolProp as CP')

# 2. Update _select_backend and _get_backend_order
old_order = """        # Skip HEOS if incompatible
        incompatible = mixture.check_heos_compatibility()
        if incompatible and preferred == "HEOS":
            backends = ["SRK", "PR"]
        else:
            # Add fallbacks
            for fallback in ["SRK", "PR"]:
                if fallback not in backends:
                    backends.append(fallback)
        
        return backends"""

new_order = """        # Check compatibility
        heos_incompatible = mixture.check_heos_compatibility()
        if heos_incompatible and preferred == "HEOS":
            backends = []
            
        # Add fallbacks in order of preference
        all_fallbacks = ["GERG-2008", "AGA8-Detail", "HEOS", "SRK", "PR"]
        for fallback in all_fallbacks:
            if fallback == "HEOS" and heos_incompatible:
                continue
            if fallback not in backends:
                backends.append(fallback)
        
        return backends"""

content = content.replace(old_order, new_order)


# 3. Add _calculate_aga8 method before _create_state
aga8_method = """    def _calculate_aga8(self, mixture, temperature_k, pressure_pa, method="GERG-2008") -> ActualConditionResults:
        if not PYAGA8_AVAILABLE:
            raise BackendNotAvailableError(method)
            
        comp = pyaga8.Composition()
        
        aga8_mapping = {
            'methane': 'methane', 'ethane': 'ethane', 'n-propane': 'propane', 'propane': 'propane',
            'n-butane': 'n_butane', 'isobutane': 'isobutane', 'n-pentane': 'n_pentane',
            'isopentane': 'isopentane', 'n-hexane': 'hexane', 'n-heptane': 'heptane',
            'n-octane': 'octane', 'n-nonane': 'nonane', 'n-decane': 'decane',
            'hydrogen': 'hydrogen', 'oxygen': 'oxygen', 'carbonmonoxide': 'carbon_monoxide',
            'water': 'water', 'hydrogensulfide': 'hydrogen_sulfide', 'helium': 'helium',
            'argon': 'argon', 'carbondioxide': 'carbon_dioxide', 'nitrogen': 'nitrogen'
        }
        
        for gas in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
            aga8_name = aga8_mapping.get(coolprop_name)
            if aga8_name:
                setattr(comp, aga8_name, gas.fraction / 100.0)
            else:
                self.logger.warning(f"Bileşen {gas.name} AGA8 standardında desteklenmiyor. Yoksayılıyor.")
                
        engine = pyaga8.Gerg2008() if method == "GERG-2008" else pyaga8.Detail()
        engine.set_composition(comp)
        engine.temperature = temperature_k
        engine.pressure = pressure_pa / 1000.0
        
        engine.calc_density(0)
        engine.calc_properties()
        
        density_kg_m3 = engine.d * engine.mm               
        enthalpy_kj_kg = engine.h / engine.mm              
        entropy_kj_kg_k = engine.s / engine.mm             
        internal_energy_kj_kg = engine.u / engine.mm       
        cp_kj_kg_k = engine.cp / engine.mm                 
        cv_kj_kg_k = engine.cv / engine.mm                 
        
        return ActualConditionResults(
            temperature=temperature_k,
            pressure=pressure_pa,
            density=density_kg_m3,
            molar_mass=engine.mm / 1000.0,
            compressibility_factor=engine.z,
            internal_energy=internal_energy_kj_kg,
            enthalpy=enthalpy_kj_kg,
            entropy=entropy_kj_kg_k,
            cp=cp_kj_kg_k,
            cv=cv_kj_kg_k,
            isentropic_exponent=engine.kappa,
            speed_of_sound=engine.w
        )

    def _create_state"""
content = content.replace("    def _create_state", aga8_method)


# 4. Update _calculate_with_backend to route to AGA8
old_calc_backend = """        # Create CoolProp state
        state = self._create_state(mixture, temperature_k, pressure_pa, backend)
        
        # Calculate actual condition properties
        actual_results = self._calculate_actual_conditions(state)"""

new_calc_backend = """        if backend in ["GERG-2008", "AGA8-Detail"]:
            actual_results = self._calculate_aga8(mixture, temperature_k, pressure_pa, backend)
            # Standart conditions
            standard_results = StandardConditionResults(
                density_std=1.0, specific_gravity=1.0, reference_temperature=standard_T, reference_pressure=standard_P, standard_name=standard_name
            )
            try:
                std_res = self._calculate_aga8(mixture, standard_T, standard_P, backend)
                standard_results.density_std = std_res.density
                
                # Air density calculation using ideal gas
                rho_air = standard_P / (287.058 * standard_T)
                try:
                    rho_air = CP.PropsSI('D', 'T', standard_T, 'P', standard_P, 'Air')
                except: pass
                
                standard_results.specific_gravity = std_res.density / rho_air
            except Exception as e:
                self.logger.warning(f"Standard condition calculation failed with {backend}: {e}")
                
            state = None
            phase_envelope = None
            # Fallback to HEOS/SRK for phase envelope
            try:
                state = self._create_state(mixture, temperature_k, pressure_pa, "HEOS" if not mixture.check_heos_compatibility() else "SRK")
                phase_envelope = self._calculate_phase_envelope(state, "HEOS" if not mixture.check_heos_compatibility() else "SRK")
            except:
                pass
                
        else:
            # Create CoolProp state
            state = self._create_state(mixture, temperature_k, pressure_pa, backend)
            
            # Calculate actual condition properties
            actual_results = self._calculate_actual_conditions(state)
            
            # Calculate standard condition properties
            standard_results = self._calculate_standard_conditions(
                mixture, backend, standard_T, standard_P, standard_name
            )
            
            # Calculate Phase Envelope
            phase_envelope = self._calculate_phase_envelope(state, backend)"""

content = content.replace(old_calc_backend, new_calc_backend)

# Replace the remainder of standard/heating logic in _calculate_with_backend
old_std_heat = """        # Calculate standard condition properties
        standard_results = self._calculate_standard_conditions(
            mixture, backend, standard_T, standard_P, standard_name
        )
        
        # Calculate heating values"""
content = content.replace(old_std_heat, "        # Calculate heating values")

old_phase = """        # Calculate Phase Envelope
        phase_envelope = self._calculate_phase_envelope(state, backend)
        
        # Package results"""
content = content.replace(old_phase, "        # Package results")


# 5. Add all backends to Z-factor comparison
old_z_comp = """    def _calculate_z_factor_comparison(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float
    ) -> List[ZFactorComparison]:
        \"\"\"Return optional Standing-Katz/DAK Z estimates for display.\"\"\"
        try:
            estimates = self.z_factor_estimator.estimates(
                mixture,
                temperature_k,
                pressure_pa
            )
            return [
                ZFactorComparison(
                    method=estimate.method,
                    z_factor=estimate.z_factor,
                    ppr=estimate.ppr,
                    tpr=estimate.tpr,
                    valid=estimate.valid,
                    warning=estimate.warning
                )
                for estimate in estimates
            ]
        except Exception as e:
            self.logger.info(f"Standing-Katz/DAK Z comparison unavailable: {e}")
            return []"""

new_z_comp = """    def _calculate_z_factor_comparison(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float
    ) -> List[ZFactorComparison]:
        \"\"\"Return comprehensive Z-factor comparisons across all backends.\"\"\"
        comparisons = []
        
        # 1. Standing-Katz and DAK
        try:
            estimates = self.z_factor_estimator.estimates(mixture, temperature_k, pressure_pa)
            for est in estimates:
                comparisons.append(ZFactorComparison(
                    method=est.method,
                    z_factor=est.z_factor,
                    ppr=est.ppr,
                    tpr=est.tpr,
                    valid=est.valid,
                    warning=est.warning
                ))
        except Exception as e:
            self.logger.info(f"Standing-Katz/DAK Z comparison unavailable: {e}")
            
        # Helper to get pseudo criticals for valid flag
        try:
            pseudo = self.z_factor_estimator.pseudo_critical(mixture)
            ppr = pressure_pa / pseudo.pc_pa
            tpr = temperature_k / pseudo.tc_k
        except:
            ppr, tpr = 1.0, 1.0
            
        # 2. Add GERG-2008 & AGA8-Detail
        for method in ["GERG-2008", "AGA8-Detail"]:
            try:
                res = self._calculate_aga8(mixture, temperature_k, pressure_pa, method)
                comparisons.append(ZFactorComparison(
                    method=method, z_factor=res.compressibility_factor, ppr=ppr, tpr=tpr, valid=True, warning=None
                ))
            except: pass
            
        # 3. Add HEOS, SRK, PR
        for method in ["HEOS", "SRK", "PR"]:
            try:
                if method == "HEOS" and mixture.check_heos_compatibility(): continue
                state = self._create_state(mixture, temperature_k, pressure_pa, method)
                comparisons.append(ZFactorComparison(
                    method=method, z_factor=state.compressibility_factor(), ppr=ppr, tpr=tpr, valid=True, warning=None
                ))
            except: pass
            
        return comparisons"""

content = content.replace(old_z_comp, new_z_comp)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {filepath}")
