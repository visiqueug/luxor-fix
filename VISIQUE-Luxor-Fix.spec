# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['luxor_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('tools/upx.exe', 'tools'), ('dgvoodoo/D3D8.dll', 'dgvoodoo'), ('dgvoodoo/dgVoodoo.conf', 'dgvoodoo'), ('cursorfix/visique_cursor.dll', 'cursorfix')],
    hiddenimports=[],
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
    name='VISIQUE-Luxor-Fix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # Bundled assets are hash-verified at runtime and must stay byte-identical.
    upx_exclude=['visique_cursor.dll', 'D3D8.dll', 'upx.exe'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
