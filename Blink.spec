# -*- mode: python ; coding: utf-8 -*-

# ⚠️ ALWAYS build with: pyinstaller Blink.spec
# Do NOT use: pyinstaller main.py — it ignores all pywin32 bundling logic!

from PyInstaller.utils.hooks import collect_all

# Collect pywin32 files
win32_all = collect_all('win32')
pywin32_all = collect_all('pywin32')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')] + win32_all[0] + pywin32_all[0],
    hiddenimports=[
        'win32clipboard',
        'win32api',
        'win32gui',
        'win32con',
        'pywintypes',
        'pythoncom',
        'win32.lib',
        'win32.lib.win32con',
        'win32com',
        'win32com.client',
        'psutil',
        'win32',
    ],
    hookspath=['.'],
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
    name='Blink',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
