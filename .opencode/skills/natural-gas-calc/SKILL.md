---
name: natural-gas-calc
description: "Expert skill for the Natural Gas Prop Main thermodynamic calculation engine. Covers CoolProp backends (HEOS/SRK/PR), AGA8 (GERG-2008/AGA8-Detail via pyaga8), standing-Katz Z-factor estimators (ANN10/ANN5/DAK), heating value calculation (3-stage fallback: built-in → component-based → reference DB), phase envelope generation, and volume conversion. USE FOR: modifying calculator.py, fixing calculation bugs, adding new thermodynamic backends, working with CoolProp AbstractState, Z-factor comparison logic, heating value (HHV/LHV) fallback chain, phase envelope debugging, AGA8/pyaga8 integration, understanding ThermoCalculator architecture. DO NOT USE FOR: UI changes (hand off to natural-gas-ui), writing tests (hand off to natural-gas-test), build/release tasks (hand off to natural-gas-build)."
license: Proprietary - Kompresör Pompa
metadata:
  author: Kompresör Pompa
  version: "1.4.0"
---

# Natural Gas Thermodynamic Calculator

Core thermodynamic calculation engine for natural gas mixtures. Uses CoolProp for equation-of-state calculations with multi-backend fallback, and pyaga8 for AGA8 reference calculations.

## Quick Reference

| Property | Description |
|----------|-------------|
| **Purpose** | Thermodynamic property calculation for natural gas mixtures |
| **Backends** | HEOS, SRK, PR (CoolProp), GERG-2008, AGA8-Detail (pyaga8) |
| **Fallback** | Standing-Katz ANN10 Z-only fallback when all backends fail |
| **Heating** | 3-stage HHV/LHV: CoolProp built-in → component-based → reference DB |
| **Key class** | `ThermoCalculator` in `calculator.py` (1125 lines) |

## When to Use This Skill

- ✅ Modifying `calculator.py` — the 1125-line core engine
- ✅ Understanding the fallback chain: HEOS → SRK → PR → GERG-2008 → AGA8-Detail → ANN10
- ✅ Fixing Z-factor, density, enthalpy, or heating value calculation bugs
- ✅ Working with `aga8_calculator.py` or pyaga8 integration
- ✅ Debugging CoolProp state creation/update failures (`StateUpdateError`)
- ✅ Working with the 3-stage heating value fallback system
- ✅ Modifying `z_factor.py` (ANN10/ANN5/DAK estimators) or `heating_value_db.py`
- ✅ Refactoring `_compute_aga8()`, `_compute_coolprop()`, `_finalize_result()`

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `natural_gas_main/models/calculator.py` | Main ThermoCalculator class | 1125 |
| `natural_gas_main/models/aga8_calculator.py` | pyaga8 wrapper for GERG/AGA8 | 135 |
| `natural_gas_main/models/z_factor.py` | ANN10/ANN5/DAK Z estimators | 221 |
| `natural_gas_main/models/gas_data.py` | GasComponent, GasMixture models | 227 |
| `natural_gas_main/models/heating_value_db.py` | Reference heating value database | varies |
| `natural_gas_main/models/calculation_result.py` | Result models (dataclasses/Pydantic) | varies |
| `natural_gas_main/core/exceptions.py` | Custom exception hierarchy | 152 |
| `natural_gas_main/core/converters.py` | Unit conversion (T, P, V) | 249 |
| `natural_gas_main/core/validators.py` | Input validation utilities | 240 |
| `natural_gas_main/config/settings.py` | AppConfig with all constants | 231 |

## Architecture

```
ThermoCalculator
├── calculate_properties()          # Single-backend entry
├── calculate_with_fallback()       # Multi-backend fallback (never returns None)
│   ├── _get_backend_order()        # Priority: [preferred, GERG, AGA8, HEOS, SRK, PR]
│   ├── _calculate_with_backend()   # Dispatcher
│   │   ├── _compute_aga8()         # AGA8 path (GERG-2008 / AGA8-Detail)
│   │   └── _compute_coolprop()     # CoolProp path (HEOS / SRK / PR)
│   └── _calculate_z_only_fallback() # ANN10 Z-only when all fail
├── _finalize_result()              # Heating + volume + Z-comparison packaging
├── _calculate_z_factor_comparison() # Cross-backend Z comparison
├── _calculate_heating_values()      # 3-stage HHV/LHV fallback
│   ├── _calculate_heating_values_builtin()
│   ├── _calculate_heating_values_component_based()
│   └── _calculate_heating_values_reference()
├── _create_state()                  # CoolProp AbstractState factory
├── _calculate_actual_conditions()   # Extract properties from state
├── _calculate_standard_conditions() # At reference T/P
├── _calculate_phase_envelope()      # Phase envelope data
└── _calculate_volume_conversion()   # Actual → Standard → Normal
```

## Exception Handling Rules

1. **NEVER use bare `except:`** — always specify Exception type
2. **Silent failures must log** — `except ...: pass` is forbidden, use `self.logger.debug()` at minimum
3. **Fallback loops filter critical exceptions** — only catch `StateUpdateError`, `ThermoCalculationError`, `ValueError`, `RuntimeError`
4. **`calculate_with_fallback` never returns `None`** — raises `ThermoCalculationError` on total failure

## Pseudo-Critical Cache

`StandingKatzZFactor._props_cache` is a module-level dict that caches `(Tcrit, pcrit, M)` per CoolProp fluid name. First call queries CoolProp, subsequent calls reuse cached values. Cache lives for the lifetime of the `StandingKatzZFactor` instance.

## Handoff

- **UI display issues** → [natural-gas-ui](../natural-gas-ui/SKILL.md)
- **Writing/running tests** → [natural-gas-test](../natural-gas-test/SKILL.md)
- **Build & release** → [natural-gas-build](../natural-gas-build/SKILL.md)
