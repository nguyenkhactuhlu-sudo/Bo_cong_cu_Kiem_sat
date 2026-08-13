# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

base = Path(SPECPATH)
payload = base / "stage" / "payload"

datas = [(str(item), str(item.relative_to(payload).parent)) for item in payload.rglob("*") if item.is_file()]

a = Analysis(
    [str(base / "main.py")],
    pathex=[str(base)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "flask", "werkzeug", "webview", "webview.platforms.edgechromium",
        "clr", "pythonnet", "docx", "lxml", "pandas", "openpyxl",
        "fitz", "PIL", "pythoncom", "pywintypes", "win32com", "win32com.client",
    ],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "cefpython3"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="BoCongCuOffline",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(base / "vendor" / "app.ico"),
    disable_windowed_traceback=False,
)
