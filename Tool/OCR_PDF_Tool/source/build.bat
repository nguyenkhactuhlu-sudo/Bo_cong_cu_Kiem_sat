@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo ============================================
echo   OCR PDF Tool - Build Portable (Web App)
echo ============================================
echo.

set APP_NAME=OCR_PDF_Tool
set MAIN_FILE=main.py
set DIST_DIR=..\dist
set OUTPUT_DIR=%DIST_DIR%\%APP_NAME%
set VENV_DIR=build_venv

echo [1/7] Dang tim Python...
set PYTHON=
rem Try py -3 first (Windows Python launcher)
py -3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON=py -3
    goto :found_python
)
rem Try python
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON=python
    goto :found_python
)
echo [LOI] Khong tim thay Python! Hay cai Python 3.9+ truoc.
pause
exit /b 1

:found_python
echo         Tim thay: !PYTHON!
!PYTHON! --version
echo.

if not exist "%MAIN_FILE%" (
    echo [LOI] Khong tim thay %MAIN_FILE%!
    pause
    exit /b 1
)
echo         %MAIN_FILE%: OK
echo.

echo [2/7] Tao virtual environment sach...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
!PYTHON! -m venv "%VENV_DIR%"
if !errorlevel! neq 0 (
    echo [LOI] Khong tao duoc virtual environment!
    pause
    exit /b 1
)
echo         Done

rem Activate venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe

echo.
echo [3/7] Cai dat dependencies vao venv...
!VENV_PIP! install --upgrade pip >nul 2>&1
!VENV_PIP! install flask PyMuPDF Pillow python-docx pyinstaller
if !errorlevel! neq 0 (
    echo [LOI] Khong cai duoc dependencies!
    pause
    exit /b 1
)
echo         Done
echo.

echo [4/7] Dang don dep build cu...
if exist build rmdir /s /q build
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"
echo         Done
echo.

echo [5/7] Dang build voi PyInstaller --onedir (mat 2-4 phut)...
!VENV_PYTHON! -m PyInstaller ^
    --onedir ^
    --windowed ^
    --name "%APP_NAME%" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import flask ^
    --hidden-import fitz ^
    --hidden-import docx ^
    --hidden-import PIL ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module scipy ^
    --exclude-module matplotlib ^
    --exclude-module torch ^
    --exclude-module tensorflow ^
    --exclude-module sklearn ^
    --exclude-module cv2 ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module pytest ^
    --exclude-module sympy ^
    --clean ^
    --noconfirm ^
    --distpath "%DIST_DIR%" ^
    %MAIN_FILE%

if !errorlevel! neq 0 (
    echo.
    echo [LOI] Build that bai! Kiem tra log o tren.
    pause
    exit /b 1
)
echo         Done
echo.

echo [6/7] Dang sao chep Tesseract-OCR...
if not exist "%OUTPUT_DIR%\Tesseract-OCR" (
    xcopy "..\OCR_PDF_Tool\Tesseract-OCR" "%OUTPUT_DIR%\Tesseract-OCR\" /E /I /Q /Y >nul
    echo         Done
) else (
    echo         Thu muc Tesseract-OCR da ton tai
)

echo.
echo [7/7] Dang sao chep VC++ runtime DLLs...
set VC_FOUND=0
if exist "%SYSTEMROOT%\System32\VCRUNTIME140.dll" (
    copy /Y "%SYSTEMROOT%\System32\VCRUNTIME140.dll" "%OUTPUT_DIR%\" >nul
    echo         VCRUNTIME140.dll -^> thu muc goc
    set VC_FOUND=1
)
if exist "%SYSTEMROOT%\System32\vcruntime140_1.dll" (
    copy /Y "%SYSTEMROOT%\System32\vcruntime140_1.dll" "%OUTPUT_DIR%\" >nul
    echo         vcruntime140_1.dll -^> thu muc goc
)
if exist "%SYSTEMROOT%\System32\msvcp140.dll" (
    copy /Y "%SYSTEMROOT%\System32\msvcp140.dll" "%OUTPUT_DIR%\" >nul
    echo         msvcp140.dll -^> thu muc goc
)
rem Also copy to Tesseract-OCR folder
if exist "%OUTPUT_DIR%\VCRUNTIME140.dll" (
    copy /Y "%OUTPUT_DIR%\VCRUNTIME140.dll" "%OUTPUT_DIR%\Tesseract-OCR\" >nul
    copy /Y "%OUTPUT_DIR%\vcruntime140_1.dll" "%OUTPUT_DIR%\Tesseract-OCR\" >nul 2>&1
    copy /Y "%OUTPUT_DIR%\msvcp140.dll" "%OUTPUT_DIR%\Tesseract-OCR\" >nul 2>&1
    echo         Da copy vao Tesseract-OCR\
)
if !VC_FOUND! equ 0 (
    echo [CANH BAO] Khong tim thay VCRUNTIME140.dll tren may nay.
)
echo.

echo ============================================
echo   BUILD THANH CONG!
echo ============================================
echo.
echo   Thu muc Portable: %OUTPUT_DIR%
echo.
echo   Tao launcher...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo Dang khoi dong OCR PDF Tool...
echo start "" "%%~dp0OCR_PDF_Tool.exe"
) > "%OUTPUT_DIR%\Chay_OCR.bat"
echo         Chay_OCR.bat OK

echo.
echo   Tao HUONG_DAN.txt...
(
echo ============================================
echo   HUONG DAN TRIEN KHAI - OCR PDF TOOL
echo   Phien ban: 1.0.0
echo ============================================
echo.
echo [Cach su dung]
echo 1. Copy TOAN BO thu muc nay sang may tinh khac
echo    (USB, o cung di dong, mang LAN)
echo 2. Click dup "Chay_OCR.bat" de chay
echo 3. Trinh duyet tu dong mo, chon file PDF va OCR
echo.
echo [Yeu cau he thong]
echo - Windows 7 SP1 tro len (64-bit)
echo - KHONG can cai Python
echo - KHONG can cai Tesseract
echo - KHONG can ket noi Internet
echo.
echo [Neu gap loi]
echo - Loi "VCRUNTIME140.dll not found":
echo   Cai VC++ Redistributable tu:
echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
echo - Loi "api-ms-win-crt-runtime-l1-1-0.dll":
echo   Windows 7 can KB2999226. Win 8/10/11 co san.
echo.
echo [Cau truc thu muc]
echo   Chay_OCR.bat          ^<- Click de chay
echo   OCR_PDF_Tool.exe      ^<- Ung dung chinh
echo   _internal\            ^<- Thu vien Python
echo     ^+-- templates\     ^<- Giao dien web
echo     ^+-- static\        ^<- Logo
echo   Tesseract-OCR\        ^<- OCR engine
echo     ^+-- tesseract.exe
echo     ^+-- tessdata\ (vie, eng)
echo   VCRUNTIME140.dll      ^<- VC++ runtime
echo ============================================
) > "%OUTPUT_DIR%\HUONG_DAN.txt"
echo         HUONG_DAN.txt OK

echo.
echo ============================================
echo   HUONG DAN SU DUNG:
echo   1. Vao thu muc: %OUTPUT_DIR%
echo   2. Copy toan bo thu muc "%APP_NAME%" sang may khac
echo   3. Chay "Chay_OCR.bat" tren may dich
echo ============================================

rem Cleanup venv
echo.
echo   Dang don dep venv...
rmdir /s /q "%VENV_DIR%"

pause
