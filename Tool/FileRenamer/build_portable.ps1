$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ToolRoot)
$Python = Join-Path $ProjectRoot "DesktopOffline\.build-venv\Scripts\python.exe"
$Work = Join-Path $ToolRoot "build"
$Dist = Join-Path $ToolRoot "dist"
$Package = Join-Path $Dist "FileRenamerPortable"
$Zip = Join-Path $ToolRoot "FileRenamer.zip"

if (-not (Test-Path -LiteralPath $Python)) { throw "Thiếu môi trường build: $Python" }

& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Work (Join-Path $ToolRoot "FileRenamerGUI.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build thất bại." }

if (Test-Path -LiteralPath $Package) {
    $ResolvedPackage = [IO.Path]::GetFullPath($Package)
    $ResolvedDist = [IO.Path]::GetFullPath($Dist)
    if (-not $ResolvedPackage.StartsWith($ResolvedDist + "\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "Thư mục đóng gói nằm ngoài dist: $ResolvedPackage"
    }
    Remove-Item -LiteralPath $ResolvedPackage -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $Package | Out-Null
Move-Item -LiteralPath (Join-Path $Dist "FileRenamerPortable.exe") -Destination (Join-Path $Package "FileRenamerPortable.exe") -Force
Copy-Item -LiteralPath (Join-Path $ToolRoot "HuongDanSuDung.txt") -Destination (Join-Path $Package "HUONG_DAN_SU_DUNG.txt")

if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip -Force }
Compress-Archive -LiteralPath $Package -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "PORTABLE SUCCESS: $Zip" -ForegroundColor Green
