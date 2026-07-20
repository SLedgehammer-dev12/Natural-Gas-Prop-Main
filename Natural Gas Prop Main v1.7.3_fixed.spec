# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules

binaries = []
hiddenimports = ['CoolProp', 'CoolProp.CoolProp', 'CoolProp.State', 'CoolProp.constants', 'CoolProp.HumidAirProp']
binaries += collect_dynamic_libs('CoolProp')
hiddenimports += collect_submodules('CoolProp')


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=[('C:\\Users\\omere\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\customtkinter', 'customtkinter/')],
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['neqsim', 'CoolProp.tests', 'CoolProp.Plots', 'CoolProp.GUI'],
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
    name='Natural Gas Prop Main v1.7.3_fixed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)
