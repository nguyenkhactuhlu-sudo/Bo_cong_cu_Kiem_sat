# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

base = Path(SPECPATH)
project = base.parents[1]
vendor = project / "DesktopOffline" / "vendor"

datas = [
    (str(project / "Tool" / "auto_install.py"), "."),
    (str(project / "static" / "logo_moi.png"), "static"),
    (str(project / "DesktopOffline" / "brand.css"), "assets/brand"),
    (str(vendor / "brand" / "fonts"), "assets/brand/fonts"),
    (str(vendor / "fontawesome"), "assets/fontawesome"),
]

a = Analysis(
    [str(base / "portable_browser.py")],
    pathex=[str(base), str(project / "Tool")],
    binaries=[],
    datas=datas,
    hiddenimports=["flask", "werkzeug"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "webview", "pythonnet", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="FileRenamerPortable",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
