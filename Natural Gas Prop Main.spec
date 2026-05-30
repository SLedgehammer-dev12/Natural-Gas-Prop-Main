# -*- mode: python ; coding: utf-8 -*-

import pathlib
import customtkinter

customtkinter_path = pathlib.Path(customtkinter.__file__).parent

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[(str(customtkinter_path), 'customtkinter/')],
    hiddenimports=[
        'CoolProp.CoolProp',
        'matplotlib.backends.backend_tkagg',
        'PIL',
        'fpdf',
        'pyaga8',
        'customtkinter',
        'packaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Natural Gas Prop Main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    version='version_info.txt',
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='Natural Gas Prop Main.app',
    icon=None,
    bundle_identifier='com.kompresorpompa.naturalgasprop',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.5.0',
        'CFBundleVersion': '1.5.0.0',
        'CFBundleName': 'Natural Gas Prop Main',
        'CFBundleDisplayName': 'Natural Gas Prop Main',
        'LSMinimumSystemVersion': '10.15',
    },
)
