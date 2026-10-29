; Medya - Text Dönüştürücü kurulum betiği (Inno Setup 6)
#define AppName "Medya - Text Dönüştürücü"
#define AppExe "MedyaText.exe"
#define AppVersion "1.0.0"

[Setup]
AppId={{B7C3E1A4-5D2F-4C8A-9E61-3F0A7D2B8C15}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\MedyaText
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=MedyaTextKurulum
SetupIconFile=app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
UninstallDisplayIcon={app}\{#AppExe}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol ekle"; GroupDescription: "Ek görevler:"

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{#AppName} uygulamasını şimdi aç"; Flags: nowait postinstall skipifsilent
