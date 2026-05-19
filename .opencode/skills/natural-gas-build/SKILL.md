---
name: natural-gas-build
description: "Expert skill for building, versioning, and releasing the Natural Gas Prop Main application. Covers version bumping across all reference files, PyInstaller .exe packaging, wheel builds via python -m build, GitHub release creation via gh CLI, version.json management, .spec file updates, and MANIFEST.in/maintenance. USE FOR: bumping version, building .exe, creating GitHub releases, updating changelog, managing dist/ artifacts, fixing build errors, version synchronization across files. DO NOT USE FOR: code changes (hand off to natural-gas-calc or natural-gas-ui), writing tests (hand off to natural-gas-test)."
license: Proprietary - Kompresör Pompa
metadata:
  author: Kompresör Pompa
  version: "1.4.0"
---

# Natural Gas Prop Build & Release

End-to-end build pipeline: version bump → wheel build → PyInstaller .exe → GitHub release.

## Quick Reference

| Property | Description |
|----------|-------------|
| **Build system** | setuptools (build_meta backend) |
| **Wheel output** | `dist/natural_gas_prop_main-X.Y-py3-none-any.whl` |
| **Exe output** | `dist/Natural Gas Prop Main.exe` (~59 MB) |
| **PyInstaller** | 6.12+ with custom .spec file |
| **GitHub** | `gh` CLI authenticated as `SLedgehammer-dev12` |
| **Repo** | `SLedgehammer-dev12/Natural-Gas-Prop-Main` |

## When to Use This Skill

- ✅ Bumping version number (v1.4 → v1.5)
- ✅ Building the .exe with PyInstaller
- ✅ Building the wheel with `python -m build`
- ✅ Creating a GitHub release with `gh release create`
- ✅ Uploading release assets (.exe, .whl)
- ✅ Updating `version.json` (product, version, date, changelog, download_url)
- ✅ Fixing build errors (backend not found, package discovery, license deprecation)
- ✅ Updating `version_info.txt` for Windows EXE metadata
- ✅ Maintaining `pyproject.toml` build configuration

## Version Files (All Must Be Updated)

When bumping version, update ALL of these files:

| File | Line/Key | Example |
|------|----------|---------|
| `pyproject.toml` | `version = "X.Y"` | `version = "1.4"` |
| `natural_gas_main/__init__.py` | `__version__ = "vX.Y"`, docstring | `__version__ = "v1.4"` |
| `natural_gas_main/config/settings.py` | `APP_VERSION`, `WINDOW_TITLE` | `default="v1.4"` |
| `natural_gas_main/ui/dialogs.py` | About text, new features title/body | `"Sürüm v1.4"` |
| `tests/test_release_readiness.py` | Version assertions | `assert __version__ == "v1.4"` |
| `version.json` | `version`, `date`, `changelog`, `download_url` | `"version": "v1.4"` |
| `version_info.txt` | `filevers`, `prodvers`, `FileVersion`, `ProductVersion` | `(1, 4, 0, 0)` |

## Build Pipeline

### Step 1: Version Bump

Update all 7 files listed above. Use semantic versioning: `v1.4.0` or `v1.4`.

### Step 2: Wheel Build

```bash
cd "Natural Gas Prop Main"
python -m build --wheel
```

Verify: `dist/natural_gas_prop_main-X.Y-py3-none-any.whl` (~72 KB)

**Troubleshooting:**
- `BackendUnavailable` → fix `build-backend` in pyproject.toml: use `setuptools.build_meta`
- `Multiple top-level packages` → add `[tool.setuptools.packages.find]` with `include`
- License table deprecation → use `license = "string"` instead of `license = { text = "..." }`

### Step 3: Exe Build

```bash
Remove-Item -LiteralPath "dist\Natural Gas Prop Main.exe" -Force
pyinstaller "Natural Gas Prop Main.spec" --clean
```

Verify: `dist/Natural Gas Prop Main.exe` (~59 MB)

**Key .spec settings:**
- Entry point: `run_app.py`
- Datas: customtkinter + natural_gas_main directory
- Console: False (windowed app)
- Version info: `version_info.txt`

### Step 4: GitHub Release

```bash
gh release create vX.Y --repo SLedgehammer-dev12/Natural-Gas-Prop-Main \
  --title "Natural Gas Prop vX.Y" \
  --notes "changelog content"

# Upload assets
gh release upload vX.Y --repo SLedgehammer-dev12/Natural-Gas-Prop-Main \
  "dist/Natural Gas Prop Main.exe" --clobber

gh release upload vX.Y --repo SLedgehammer-dev12/Natural-Gas-Prop-Main \
  "dist/natural_gas_prop_main-X.Y-py3-none-any.whl" --clobber
```

### Step 5: Verify

```bash
gh release view vX.Y --repo SLedgehammer-dev12/Natural-Gas-Prop-Main --json name,tagName,assets,url
```

## Changelog Format

`version.json` changelog uses Turkish, one-line-per-feature format:

```json
{
  "changelog": "- Ozellik 1.\n- Ozellik 2.\n- Duzenleme 3."
}
```

## Prerequisites

- **build** package: `pip install build`
- **pyinstaller**: `pip install pyinstaller` (v6.12+)
- **gh CLI**: v2.89+ authenticated with `repo` scope
- **setuptools**: ≥68.0

## Handoff

- **Code changes before build** → [natural-gas-calc](../natural-gas-calc/SKILL.md) or [natural-gas-ui](../natural-gas-ui/SKILL.md)
- **Running tests before release** → [natural-gas-test](../natural-gas-test/SKILL.md)
