import os

filepath = "natural_gas_main/models/calculator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_comp = """        for gas in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
            aga8_name = aga8_mapping.get(coolprop_name)
            if aga8_name:
                setattr(comp, aga8_name, gas.fraction / 100.0)
            else:
                self.logger.warning(f"Bileşen {gas.name} AGA8 standardında desteklenmiyor. Yoksayılıyor.")
                
        engine = pyaga8.Gerg2008() if method == "GERG-2008" else pyaga8.Detail()
        engine.set_composition(comp)"""

new_comp = """        sum_fractions = 0.0
        for gas in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
            aga8_name = aga8_mapping.get(coolprop_name)
            if aga8_name:
                val = gas.fraction / 100.0
                setattr(comp, aga8_name, val)
                sum_fractions += val
            else:
                self.logger.warning(f"Bileşen {gas.name} AGA8 standardında desteklenmiyor. Yoksayılıyor.")
                
        if sum_fractions < 0.99:
            raise ValueError(f"AGA8 için geçerli gazların toplamı {sum_fractions} (< 0.99). AGA8 desteklenmiyor.")
            
        # Normalize just in case of float precision issues
        if abs(sum_fractions - 1.0) > 1e-5:
            # We must normalize to exactly 1.0 for pyaga8 to avoid BadSum panic
            for gas in mixture.components:
                coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
                aga8_name = aga8_mapping.get(coolprop_name)
                if aga8_name:
                    current = getattr(comp, aga8_name)
                    setattr(comp, aga8_name, current / sum_fractions)
                    
        engine = pyaga8.Gerg2008() if method == "GERG-2008" else pyaga8.Detail()
        try:
            engine.set_composition(comp)
        except Exception as e:
            raise ValueError(f"AGA8 set_composition hatası: {e}")"""

content = content.replace(old_comp, new_comp)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched BadSum panic.")
