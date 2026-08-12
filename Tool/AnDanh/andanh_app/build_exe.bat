@echo off
title Dang build AnDanhTool.exe...
echo ==============================
echo  DANG CAI THU VIEN (neu chua co)
echo ==============================
pip install -r requirements.txt
pip install pyinstaller

echo.
echo ==============================
echo  DANG BUILD FILE .EXE...
echo ==============================
python -m PyInstaller --onefile --name "AnDanhTool" --add-data "templates;templates" --add-data "static;static" --hidden-import docx --hidden-import lxml app.py

echo.
echo ==============================
echo  DON DEP FILE TAM...
echo ==============================
rmdir /s /q build 2>nul
del AnDanhTool.spec 2>nul

echo.
echo ==============================
echo  HOAN TAT!
echo  File .exe nam trong thu muc: %CD%\dist\AnDanhTool.exe
echo  Coppy file nay sang may khac la dung duoc (khong can Python)
echo ==============================
pause
