#define AppName "Bộ công cụ Kiểm sát Offline"
#define AppVersion "1.1.0"
#define AppExeName "BoCongCuOffline.exe"

[Setup]
AppId={{B847E098-FFB1-45EE-A3DE-840D4322BC7D}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\BoCongCuKiemSatOffline
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=BoCongCuKiemSat_Offline_Setup
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
SetupIconFile=vendor\app.ico

[Files]
Source: "dist\app\BoCongCuOffline.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\app\Tesseract-OCR\*"; DestDir: "{app}\Tesseract-OCR"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "vendor\WebView2Runtime\*"; DestDir: "{app}\runtime\WebView2"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{sys}\icacls.exe"; Parameters: """{app}\runtime\WebView2"" /grant *S-1-15-2-2:(OI)(CI)(RX) /grant *S-1-15-2-1:(OI)(CI)(RX)"; StatusMsg: "Đang cấu hình thành phần hiển thị Offline..."; Flags: runhidden waituntilterminated
Filename: "{app}\{#AppExeName}"; Description: "Mở {#AppName}"; Flags: nowait postinstall skipifsilent

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"
