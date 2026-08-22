$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$ModuleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ModuleRoot
$Vendor = Join-Path $ModuleRoot "vendor"
$Cache = Join-Path $ModuleRoot ".build-cache"
$BuildVenv = Join-Path $ModuleRoot ".build-venv"
$Dist = Join-Path $ModuleRoot "dist"
$Work = Join-Path $ModuleRoot "build"

function Get-RequiredFile([string]$Url, [string]$Target, [long]$MinimumBytes = 1024) {
    if ((Test-Path -LiteralPath $Target) -and (Get-Item -LiteralPath $Target).Length -ge $MinimumBytes) { return }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    Write-Host "Download: $Url"
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Target
    if ((Get-Item -LiteralPath $Target).Length -lt $MinimumBytes) {
        throw "Downloaded file is invalid: $Target"
    }
}

New-Item -ItemType Directory -Force -Path $Vendor,$Cache,$Dist,$Work | Out-Null

# CSS/JS are downloaded on the build machine and bundled locally.
Get-RequiredFile "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" (Join-Path $Vendor "bootstrap\bootstrap.min.css")
Get-RequiredFile "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" (Join-Path $Vendor "bootstrap\bootstrap.bundle.min.js")

# Trang chào mừng dùng cùng giao diện Tailwind với bản phát hành GitHub. Tải
# runtime một lần trên máy build rồi đóng gói cục bộ để máy đích không cần mạng.
Get-RequiredFile "https://cdn.tailwindcss.com" (Join-Path $Vendor "tailwind\tailwind.js") 100000

# Font Unicode tiếng Việt được nhúng trong ứng dụng; không cài vào Windows.
$FontRoot = Join-Path $Vendor "brand\fonts"
Get-RequiredFile "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-Regular.ttf" (Join-Path $FontRoot "BeVietnamPro-Regular.ttf") 100000
Get-RequiredFile "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-SemiBold.ttf" (Join-Path $FontRoot "BeVietnamPro-SemiBold.ttf") 100000
Get-RequiredFile "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/BeVietnamPro-Bold.ttf" (Join-Path $FontRoot "BeVietnamPro-Bold.ttf") 100000
Get-RequiredFile "https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro/OFL.txt" (Join-Path $FontRoot "OFL.txt") 1000

$FaZip = Join-Path $Cache "fontawesome.zip"
if (-not (Test-Path -LiteralPath (Join-Path $Vendor "fontawesome\css\all.min.css"))) {
    Get-RequiredFile "https://github.com/FortAwesome/Font-Awesome/releases/download/6.5.1/fontawesome-free-6.5.1-web.zip" $FaZip
    $FaExtract = Join-Path $Cache "fontawesome"
    if (Test-Path -LiteralPath $FaExtract) { Remove-Item -LiteralPath $FaExtract -Recurse -Force }
    Expand-Archive -LiteralPath $FaZip -DestinationPath $FaExtract
    $FaRoot = Get-ChildItem -LiteralPath $FaExtract -Directory | Select-Object -First 1
    New-Item -ItemType Directory -Force -Path (Join-Path $Vendor "fontawesome") | Out-Null
    Copy-Item -LiteralPath (Join-Path $FaRoot.FullName "css") -Destination (Join-Path $Vendor "fontawesome\css") -Recurse
    Copy-Item -LiteralPath (Join-Path $FaRoot.FullName "webfonts") -Destination (Join-Path $Vendor "fontawesome\webfonts") -Recurse
}

$BiZip = Join-Path $Cache "bootstrap-icons.zip"
if (-not (Test-Path -LiteralPath (Join-Path $Vendor "bootstrap-icons\bootstrap-icons.min.css"))) {
    Get-RequiredFile "https://github.com/twbs/icons/releases/download/v1.11.3/bootstrap-icons-1.11.3.zip" $BiZip
    $BiExtract = Join-Path $Cache "bootstrap-icons"
    if (Test-Path -LiteralPath $BiExtract) { Remove-Item -LiteralPath $BiExtract -Recurse -Force }
    Expand-Archive -LiteralPath $BiZip -DestinationPath $BiExtract
    $BiRoot = Get-ChildItem -LiteralPath $BiExtract -Directory | Select-Object -First 1
    New-Item -ItemType Directory -Force -Path (Join-Path $Vendor "bootstrap-icons") | Out-Null
    Copy-Item -LiteralPath (Join-Path $BiRoot.FullName "font\bootstrap-icons.min.css") -Destination (Join-Path $Vendor "bootstrap-icons\bootstrap-icons.min.css")
    Copy-Item -LiteralPath (Join-Path $BiRoot.FullName "font\fonts") -Destination (Join-Path $Vendor "bootstrap-icons\fonts") -Recurse
}

# Bundle the latest Microsoft Fixed Version x64 runtime. Unlike the small
# bootstrapper, this runtime is fully self-contained and never downloads files.
$WebViewRuntime = Join-Path $Vendor "WebView2Runtime"
if (-not (Test-Path -LiteralPath (Join-Path $WebViewRuntime "msedgewebview2.exe"))) {
    $WebViewPage = (Invoke-WebRequest -UseBasicParsing "https://developer.microsoft.com/en-us/microsoft-edge/webview2").Content
    $CabMatch = [regex]::Match($WebViewPage, 'https:\\u002F\\u002F[^" ]+Microsoft\.WebView2\.FixedVersionRuntime\.[^" ]+\.x64\.cab')
    if (-not $CabMatch.Success) { throw "Could not resolve the official WebView2 Fixed Version x64 package." }
    $CabUrl = $CabMatch.Value -replace '\\u002F','/'
    $WebViewCab = Join-Path $Cache "WebView2FixedVersionX64.cab"
    Get-RequiredFile $CabUrl $WebViewCab 100000000
    $WebViewExtract = Join-Path $Cache "WebView2FixedVersionX64"
    if (Test-Path -LiteralPath $WebViewExtract) { Remove-Item -LiteralPath $WebViewExtract -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $WebViewExtract | Out-Null
    & expand.exe $WebViewCab -F:* $WebViewExtract | Out-Null
    $WebViewExe = Get-ChildItem -LiteralPath $WebViewExtract -Filter msedgewebview2.exe -Recurse | Select-Object -First 1
    if (-not $WebViewExe) { throw "The WebView2 package does not contain msedgewebview2.exe." }
    if (Test-Path -LiteralPath $WebViewRuntime) { Remove-Item -LiteralPath $WebViewRuntime -Recurse -Force }
    Copy-Item -LiteralPath $WebViewExe.Directory.FullName -Destination $WebViewRuntime -Recurse
}
if ((Get-ChildItem -LiteralPath $WebViewRuntime -Recurse -File | Measure-Object -Property Length -Sum).Sum -lt 100000000) {
    throw "WebView2 Fixed Version runtime is incomplete."
}

$Python = Join-Path $BuildVenv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    if (Test-Path -LiteralPath $BuildVenv) { Remove-Item -LiteralPath $BuildVenv -Recurse -Force }
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $PyLauncher) { throw "Python Launcher (py.exe) with Python 3.12 is required on the build machine." }
    & py -3.12 -m venv $BuildVenv
    if (-not (Test-Path -LiteralPath $Python)) { throw "Could not create the isolated build environment." }
}
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ModuleRoot "requirements-build.txt")
& $Python (Join-Path $ModuleRoot "make_icon.py")
& $Python (Join-Path $ModuleRoot "prepare_payload.py")

$AppDist = Join-Path $Dist "app"
if (Test-Path -LiteralPath $AppDist) { Remove-Item -LiteralPath $AppDist -Recurse -Force }
New-Item -ItemType Directory -Force -Path $AppDist | Out-Null
& $Python -m PyInstaller --noconfirm --clean --distpath $AppDist --workpath $Work (Join-Path $ModuleRoot "BoCongCuOffline.spec")

$TesseractSource = Join-Path $ProjectRoot "Tool\OCR_PDF_Tool\OCR_PDF_Tool\Tesseract-OCR"
if (-not (Test-Path -LiteralPath (Join-Path $TesseractSource "tesseract.exe"))) {
    throw "Tesseract portable was not found: $TesseractSource"
}
Copy-Item -LiteralPath $TesseractSource -Destination (Join-Path $AppDist "Tesseract-OCR") -Recurse

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $Iscc) {
    $UninstallKeys = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    $Inno = Get-ItemProperty $UninstallKeys -ErrorAction SilentlyContinue |
        Where-Object { $_.PSObject.Properties["DisplayName"] -and $_.DisplayName -like "Inno Setup*" } |
        Select-Object -First 1
    if ($Inno -and $Inno.InstallLocation) {
        $RegistryIscc = Join-Path $Inno.InstallLocation "ISCC.exe"
        if (Test-Path -LiteralPath $RegistryIscc) { $Iscc = $RegistryIscc }
    }
}
if (-not $Iscc) { throw "Inno Setup 6 is required on the build machine." }
Push-Location $ModuleRoot
try { & $Iscc (Join-Path $ModuleRoot "installer.iss") } finally { Pop-Location }

$Setup = Join-Path $Dist "BoCongCuKiemSat_Offline_Setup.exe"
if (-not (Test-Path -LiteralPath $Setup)) { throw "Installer was not created: $Setup" }
Write-Host "BUILD SUCCESS: $Setup" -ForegroundColor Green
