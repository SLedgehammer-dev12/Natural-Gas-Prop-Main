# -*- mode: python ; coding: utf-8 -*-

import os
import pathlib
import sys
import re
import customtkinter
customtkinter_path = pathlib.Path(customtkinter.__file__).parent

# Read version from version_info.txt for output naming. The version is always
# appended to the executable/app name (with a pyproject.toml fallback).
_script_dir = pathlib.Path(globals().get('SPECPATH') or os.getcwd())
_version = "unknown"
_version_info_path = _script_dir / "version_info.txt"
if _version_info_path.exists():
    _vtext = _version_info_path.read_text(encoding="utf-8")
    _m = re.search(r"FileVersion',\s*'([^']+)'", _vtext)
    if _m:
        _version = _m.group(1)
    else:
        _m = re.search(r"filevers=\((\d+),\s*(\d+),\s*(\d+)", _vtext)
        if _m:
            _version = f"v{_m.group(1)}.{_m.group(2)}.{_m.group(3)}"
if _version == "unknown":
    try:
        import tomllib
        _pp = tomllib.loads((_script_dir / "pyproject.toml").read_text(encoding="utf-8"))
        _version = f"v{_pp['project']['version']}"
    except Exception:
        _version = "v0.0.0"

_exe_name = f"Natural Gas Prop Main {_version}"

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[(str(customtkinter_path), 'customtkinter/')],
    hiddenimports=[
        'neqsim',
        'CoolProp',
        'CoolProp.CoolProp',
        'CoolProp.State',
        'CoolProp.constants',
        'CoolProp.HumidAirProp',
        'matplotlib.backends.backend_tkagg',
        'PIL',
        'fpdf',
        'pyaga8',
        'customtkinter',
        'packaging',
        'pydantic',
        'certifi',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'CoolProp.tests',
        'CoolProp.Plots',
        'CoolProp.GUI',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,
        name=_exe_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=_exe_name,
    )
    app = BUNDLE(
        coll,
        name=f'{_exe_name}.app',
        icon='assets/NaturalGasProp.icns',
        bundle_identifier='com.kompresorpompa.naturalgasprop',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.8.2',
            'CFBundleVersion': '1.8.2.0',
            'CFBundleName': 'Natural Gas Prop Main',
            'CFBundleDisplayName': 'Natural Gas Prop Main',
            'LSMinimumSystemVersion': '10.15',
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,
        name=_exe_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        version='version_info.txt',
        icon='assets/NaturalGasProp.ico',
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=_exe_name,
    )
