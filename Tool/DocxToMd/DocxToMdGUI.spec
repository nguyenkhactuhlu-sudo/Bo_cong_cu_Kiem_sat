# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['docx_to_md_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[('convert_doc_to_md.py', '.'), ('../auto_install.py', '.')],
    hiddenimports=['flask', 'docx'],
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
    name='DocxToMdGUI',
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
)