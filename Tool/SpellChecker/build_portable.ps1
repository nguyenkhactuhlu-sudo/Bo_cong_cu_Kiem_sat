$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$env:PYTHONUTF8 = "1"
$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ToolRoot)
$Python = Join-Path $ProjectRoot "DesktopOffline\.build-venv\Scripts\python.exe"
$Dist = Join-Path $ToolRoot "dist"
$Build = Join-Path $ToolRoot "build"
$Zip = Join-Path $ToolRoot "RaSoatChinhTa.zip"
& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Build (Join-Path $ToolRoot "SpellChecker.spec")
if ($LASTEXITCODE -ne 0) { throw "Build SpellChecker thất bại." }
if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip -Force }
Compress-Archive -LiteralPath (Join-Path $Dist "RaSoatChinhTa.exe"),(Join-Path $ToolRoot "HuongDanSuDung.txt") -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "PORTABLE SUCCESS: $Zip" -ForegroundColor Green
