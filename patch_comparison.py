import os

filepath = "natural_gas_main/models/calculator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _calculate_z_factor_comparison
old_func = """    def _calculate_z_factor_comparison(
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

new_func = """    def _calculate_z_factor_comparison(
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
                    method=method, 
                    z_factor=res.compressibility_factor, 
                    density=res.density,
                    molar_mass=res.molar_mass,
                    enthalpy=res.enthalpy,
                    entropy=res.entropy,
                    cp=res.cp,
                    cv=res.cv,
                    ppr=ppr, tpr=tpr, valid=True, warning=None
                ))
            except Exception as e: 
                pass
            
        # 3. Add HEOS, SRK, PR
        for method in ["HEOS", "SRK", "PR"]:
            try:
                if method == "HEOS" and mixture.check_heos_compatibility(): continue
                state = self._create_state(mixture, temperature_k, pressure_pa, method)
                res = self._calculate_actual_conditions(state)
                comparisons.append(ZFactorComparison(
                    method=method, 
                    z_factor=res.compressibility_factor, 
                    density=res.density,
                    molar_mass=res.molar_mass,
                    enthalpy=res.enthalpy,
                    entropy=res.entropy,
                    cp=res.cp,
                    cv=res.cv,
                    ppr=ppr, tpr=tpr, valid=True, warning=None
                ))
            except Exception as e: 
                pass
            
        return comparisons"""

if old_func in content:
    content = content.replace(old_func, new_func)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched calculator for full backend comparison.")
else:
    print("Could not find the function to patch.")
