; sesten kurulum betiği (Inno Setup 6) / Installer script
#define AppName "sesten"
#define AppExe "sesten.exe"
#define AppVersion "1.2.0"

[Setup]
; AppId eski sürümle aynı kalır: yeni kurulum eski sürümün üstüne (güncelleme olarak) kurulur.
AppId={{B7C3E1A4-5D2F-4C8A-9E61-3F0A7D2B8C15}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\sesten
UsePreviousAppDir=no
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=sesten-setup
SetupIconFile=app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
; Windows'un dili Türkçe ya da İngilizce ise soru sormadan seçer; başka bir dilde sorar.
ShowLanguageDialog=auto
LanguageDetectionMethod=uilanguage

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
turkish.DesktopIcon=Masaüstüne kısayol ekle
english.DesktopIcon=Create a desktop shortcut
turkish.TasksGroup=Ek görevler:
english.TasksGroup=Additional tasks:
turkish.LaunchApp={#AppName} uygulamasını şimdi aç
english.LaunchApp=Launch {#AppName} now

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:TasksGroup}"

; Programın önceki adıyla kurulmuş bir sürüm varsa onun dosyalarını ve kısayollarını kaldırır.
[InstallDelete]
Type: files; Name: "{app}\MedyaText.exe"
Type: files; Name: "{autoprograms}\Medya - Text Dönüştürücü.lnk"
Type: files; Name: "{autodesktop}\Medya - Text Dönüştürücü.lnk"
Type: filesandordirs; Name: "{autopf}\MedyaText"

; Kullanıcının seçtiği simge kısayollar için buraya kopyalanır; kaldırırken silinir (ayarlar kalır).
[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\sesten\icons"

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent
