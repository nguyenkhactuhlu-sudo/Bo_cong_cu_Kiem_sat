# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('../../static/logo_moi.png', 'static'),
    ],
    hiddenimports=[
        'engine', 'docx_processor', 'offline_server', 'word_converter',
        'pythoncom', 'pywintypes', 'win32com', 'win32com.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'pandas', 'PIL', 'matplotlib', 'scipy', 'Cython',
        'cryptography', 'bcrypt', 'psutil', 'pygments', 'bs4', 'html5lib',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RaSoatChinhTa',
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
