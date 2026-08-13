$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$env:PYTHONUTF8 = "1"
$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = Join-Path $ToolRoot "andanh_app"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ToolRoot)
$Python = Join-Path $ProjectRoot "DesktopOffline\.build-venv\Scripts\python.exe"
$Dist = Join-Path $AppRoot "dist"
$Build = Join-Path $AppRoot "build"
$Zip = Join-Path $ToolRoot "AnDanhTool.zip"
& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Build (Join-Path $AppRoot "AnDanhTool.spec")
if ($LASTEXITCODE -ne 0) { throw "Build AnDanh thất bại." }
if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip -Force }
Compress-Archive -LiteralPath (Join-Path $Dist "AnDanhTool.exe"),(Join-Path $ToolRoot "HuongDanSuDung.txt") -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "PORTABLE SUCCESS: $Zip" -ForegroundColor Green
