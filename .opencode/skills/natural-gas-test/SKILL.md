---
name: natural-gas-test
description: "Expert skill for writing and running tests in the Natural Gas Prop Main project. Covers pytest configuration, test file conventions, coverage targets, known test categories (smoke, unit, integration, accuracy), test data fixtures, mocking CoolProp, skipping GUI tests in headless environments, and adding new test categories. USE FOR: writing new tests, fixing failing tests, increasing coverage, adding test fixtures, understanding test structure, running specific test suites, interpreting coverage reports, adding edge case tests. DO NOT USE FOR: modifying calculator logic (hand off to natural-gas-calc), UI changes (hand off to natural-gas-ui), build/release (hand off to natural-gas-build)."
license: Proprietary - Kompresör Pompa
metadata:
  author: Kompresör Pompa
  version: "1.4.0"
---

# Natural Gas Prop Testing

Pytest-based test suite with 133 tests covering core logic, models, converters, Z-factor estimators, heating values, AGA8 integration, serialization, and report generation.

## Quick Reference

| Property | Description |
|----------|-------------|
| **Framework** | pytest 7.0+ with pytest-cov |
| **Test count** | 133 (GUI tests skipped headless) |
| **Coverage target** | ≥50% (configurable in pyproject.toml) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` |
| **Test location** | `tests/` directory (12 test files) |
| **Fixtures dir** | `tests/fixtures/` (contains `deneme.ngp`) |

## When to Use This Skill

- ✅ Writing new test files or test functions
- ✅ Fixing failing tests after code changes
- ✅ Running specific test suites: `pytest tests/test_calculator_smoke.py -v`
- ✅ Understanding what each test file covers
- ✅ Adding test data fixtures to `tests/fixtures/`
- ✅ Interpreting coverage reports
- ✅ Testing edge cases (empty inputs, boundary values, invalid data)
- ✅ Mocking CoolProp for unit tests (see FakeCoolProp pattern)
- ✅ Configuring test skips for headless/GUI environments

## Test File Map

| Test File | Category | Tests | What It Covers |
|-----------|----------|-------|----------------|
| `test_core.py` | Unit | ~25 | GasComponent, GasMixture validators |
| `test_models.py` | Unit | ~17 | Model creation, serialization |
| `test_calculator_smoke.py` | Integration | 5 | ThermoCalculator with real CoolProp |
| `test_backend_fallback.py` | Integration | 1 | HEOS→SRK fallback chain |
| `test_z_factor_accuracy.py` | Accuracy | ~10 | ANN10/ANN5/DAK validation |
| `test_z_factor_fallback.py` | Fallback | 2 | Z-only fallback path |
| `test_z_factor_unit.py` | Unit | 12 | ANN10/ANN5/DAK with FakeCoolProp |
| `test_heating_values.py` | Unit/Integration | 8 | 3-stage HHV/LHV fallback |
| `test_aga8.py` | Integration | 8 | GERG-2008/AGA8-Detail (pyaga8) |
| `test_converters.py` | Unit | 27 | T/P/V unit converters |
| `test_serializer.py` | Unit | ~5 | Save/load .ngp files |
| `test_report_generator.py` | Unit | ~4 | PDF/text report generation |
| `test_gas_catalog.py` | Integration | 3 | CoolProp gas list loading |
| `test_release_readiness.py` | Release | 3 | Version, constants, version.json |
| `test_gui_smoke.py` | GUI | 4 | ThermoApp/widget creation (headless skip) |

## Running Tests

```bash
# Full suite (excluding GUI)
pytest tests/ --ignore=tests/test_gui_smoke.py -v

# Specific category
pytest tests/test_calculator_smoke.py -v

# With coverage
pytest tests/ --ignore=tests/test_gui_smoke.py --cov=natural_gas_main --cov-report=term

# Quick check (stop on first failure)
pytest tests/ -x -q
```

## Mock CoolProp Pattern

For unit tests that don't need real CoolProp:

```python
@pytest.fixture
def estimator():
    class FakeCoolProp:
        @staticmethod
        def PropsSI(key, fluid):
            props = {
                ("Tcrit", "Methane"): 190.564,
                ("pcrit", "Methane"): 4599200.0,
                ("M", "Methane"): 0.0160428,
            }
            return props.get((key, fluid), 1.0)
    return StandingKatzZFactor(FakeCoolProp())
```

## GUI Test Skip Pattern

```python
def _tk_available() -> bool:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False

@pytest.mark.skipif(not _tk_available(), reason="No display available")
class TestGuiSmoke:
    ...
```

## Edge Case Test Patterns

- **Empty mixture:** `GasMixture(components=[], ...)` → `ValidationError`
- **Zero fraction:** `GasComponent(name="Methane", fraction=0)` → `ValidationError`
- **Negative values:** Validate converters accept but validators reject
- **Non-combustible mixture:** `Nitrogen + CO2` → heating values may be None or 0
- **Unknown gas name:** Reference DB returns `(0.0, 0.0)` for inerts, `None` for unknowns
- **Boundary extremes:** PPR=0, PPR=30, TPR=1.0, TPR=3.0

## Handoff

- **Calculation engine logic** → [natural-gas-calc](../natural-gas-calc/SKILL.md)
- **UI changes** → [natural-gas-ui](../natural-gas-ui/SKILL.md)
- **Build & release** → [natural-gas-build](../natural-gas-build/SKILL.md)
