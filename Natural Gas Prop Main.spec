# -*- mode: python ; coding: utf-8 -*-

import os
import pathlib
import sys
import re
import customtkinter
customtkinter_path = pathlib.Path(customtkinter.__file__).parent

# --- CoolProp explicit collection ---
import CoolProp
_coolprop_dir = os.path.dirname(CoolProp.__file__)
_coolprop_binaries = []
_coolprop_datas = []
for _f in os.listdir(_coolprop_dir):
    _fp = os.path.join(_coolprop_dir, _f)
    if os.path.isfile(_fp):
        if _f.endswith(('.pyd', '.dll', '.so')):
            _coolprop_binaries.append((_fp, 'CoolProp'))
        elif _f.endswith('.py') and not _f.startswith('test'):
            _coolprop_datas.append((_fp, 'CoolProp'))

# Read version from version_info.txt for output naming
_version = "unknown"
_version_info_path = pathlib.Path("version_info.txt")
if _version_info_path.exists():
    _vtext = _version_info_path.read_text(encoding="utf-8")
    _m = re.search(r"FileVersion',\s*'([^']+)'", _vtext)
    if _m:
        _version = _m.group(1)
    else:
        _m = re.search(r"filevers=\((\d+),\s*(\d+),\s*(\d+)", _vtext)
        if _m:
            _version = f"v{_m.group(1)}.{_m.group(2)}.{_m.group(3)}"

_exe_name = f"Natural Gas Prop Main {_version}" if _version != "unknown" else "Natural Gas Prop Main"

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=_coolprop_binaries,
    datas=[(str(customtkinter_path), 'customtkinter/')] + _coolprop_datas,
    hiddenimports=[
        'CoolProp',
        'CoolProp.CoolProp',
        'CoolProp.State',
        'CoolProp.constants',
        'CoolProp.HumidAirProp',
        'CoolProp.Plots',
        'matplotlib.backends.backend_tkagg',
        'PIL',
        'fpdf',
        'pyaga8',
        'customtkinter',
        'packaging',
        'pydantic',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['neqsim'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
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
    app = BUNDLE(
        exe,
        name=f'{_exe_name}.app',
        icon=None,
        bundle_identifier='com.kompresorpompa.naturalgasprop',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.7.3',
            'CFBundleVersion': '1.7.3.0',
            'CFBundleName': 'Natural Gas Prop Main',
            'CFBundleDisplayName': 'Natural Gas Prop Main',
            'LSMinimumSystemVersion': '10.15',
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
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
    )
