param(
    [Parameter(Mandatory = $true)][string]$Output,
    [string]$Tool = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class BcksWindowCapture {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
}
"@

$exe = Join-Path $PSScriptRoot "dist\app\BoCongCuOffline.exe"
if (-not (Test-Path -LiteralPath $exe)) { throw "Missing desktop executable: $exe" }
$before = @(Get-Process BoCongCuOffline -ErrorAction SilentlyContinue | ForEach-Object Id)
$arguments = if ($Tool) { @("--tool", $Tool) } else { @() }
$started = if ($arguments.Count) {
    Start-Process -FilePath $exe -ArgumentList $arguments -PassThru
} else {
    Start-Process -FilePath $exe -PassThru
}

try {
    $window = $null
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        Start-Sleep -Milliseconds 500
        $window = Get-Process BoCongCuOffline -ErrorAction SilentlyContinue |
            Where-Object { $_.Id -notin $before -and $_.MainWindowHandle -ne 0 } |
            Sort-Object StartTime -Descending |
            Select-Object -First 1
        if ($window) { break }
    }
    if (-not $window) { throw "Desktop window did not appear." }
    [void][BcksWindowCapture]::SetForegroundWindow($window.MainWindowHandle)
    # PyInstaller one-file cần thời gian bung payload và WebView2 cần tải font cục bộ.
    Start-Sleep -Milliseconds 8000
    $rect = New-Object BcksWindowCapture+RECT
    if (-not [BcksWindowCapture]::GetWindowRect($window.MainWindowHandle, [ref]$rect)) {
        throw "Could not read desktop window bounds."
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 800 -or $height -lt 500) { throw "Unexpected window size: ${width}x${height}" }
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $hdc = $graphics.GetHdc()
        try {
            if (-not [BcksWindowCapture]::PrintWindow($window.MainWindowHandle, $hdc, 2)) {
                throw "PrintWindow could not capture the desktop window."
            }
        } finally {
            $graphics.ReleaseHdc($hdc)
        }
        $target = [IO.Path]::GetFullPath($Output)
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
        $bitmap.Save($target, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Output "$($window.MainWindowTitle)|${width}x${height}|$target"
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
} finally {
    Get-Process BoCongCuOffline -ErrorAction SilentlyContinue |
        Where-Object { $_.Id -notin $before } |
        Stop-Process -Force -ErrorAction SilentlyContinue
}
