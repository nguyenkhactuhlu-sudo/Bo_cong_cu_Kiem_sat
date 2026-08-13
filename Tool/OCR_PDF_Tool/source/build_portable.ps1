$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$env:PYTHONUTF8 = "1"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ToolRoot = Split-Path -Parent $SourceRoot
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ToolRoot)
$Python = Join-Path $ProjectRoot "DesktopOffline\.build-venv\Scripts\python.exe"
$Dist = Join-Path $SourceRoot "dist"
$Build = Join-Path $SourceRoot "build"
$AppDist = Join-Path $Dist "OCR_PDF_Tool"
$Tesseract = Join-Path $ToolRoot "OCR_PDF_Tool\Tesseract-OCR"
$Guide = Join-Path $ToolRoot "HuongDanSuDung.txt"
$Zip = Join-Path $ToolRoot "OCR_PDF_Tool.zip"

& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Build (Join-Path $SourceRoot "OCR_PDF_Tool.spec")
if ($LASTEXITCODE -ne 0) { throw "Build OCR thất bại." }
$TesseractTarget = Join-Path $AppDist "Tesseract-OCR"
if (Test-Path -LiteralPath $TesseractTarget) { Remove-Item -LiteralPath $TesseractTarget -Recurse -Force }
Copy-Item -LiteralPath $Tesseract -Destination $TesseractTarget -Recurse
Copy-Item -LiteralPath $Guide -Destination (Join-Path $AppDist "HuongDanSuDung.txt")
if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip -Force }
Compress-Archive -LiteralPath $AppDist -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "PORTABLE SUCCESS: $Zip" -ForegroundColor Green
