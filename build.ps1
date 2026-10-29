# sesten build script (Windows, PowerShell)
#
# Requirements:
#   - Python 3.13 (64-bit, with tkinter)
#   - Inno Setup 6 (optional: only needed for the installer)
#
# IMPORTANT: keep the folder path SHORT (for example C:\mt). With long paths onnxruntime fails with
# "File name too long" and the build breaks.
#
# Usage:   .\build.ps1            -> dist\sesten.exe and sesten-setup.exe
#          .\build.ps1 -ExeOnly   -> dist\sesten.exe only
param([switch]$ExeOnly)
# Note: "Stop" is not used. In Windows PowerShell 5.1 PyInstaller's info lines (stderr) are wrongly treated as errors.
# Instead, the success of every command is checked through its exit code.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Check($name) { if ($LASTEXITCODE -ne 0) { throw "$name failed (exit code $LASTEXITCODE)." } }

if ($PSScriptRoot.Length -gt 60) {
    Write-Warning "The folder path is long ($($PSScriptRoot.Length) characters). Move the project to a shorter path (for example C:\mt)."
}

if (-not (Test-Path .\venv)) { py -3.13 -m venv venv; Check "Creating the virtual environment (is Python 3.13 installed?)" }
.\venv\Scripts\python.exe -m pip install --upgrade pip
Check "Updating pip"
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Check "Installing packages"

# On some installations the virtual environment cannot find tkinter's Tcl files; point to them by hand if needed.
$base = & .\venv\Scripts\python.exe -c "import sys; print(sys.base_prefix)"
if (-not $env:TCL_LIBRARY -and (Test-Path "$base\tcl\tcl8.6")) {
    $env:TCL_LIBRARY = "$base\tcl\tcl8.6"
    $env:TK_LIBRARY = "$base\tcl\tk8.6"
}

Remove-Item dist, build -Recurse -Force -ErrorAction SilentlyContinue
.\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name sesten `
    --icon app.ico --add-data "app.ico;." `
    --collect-all faster_whisper --collect-all ctranslate2 --collect-all onnxruntime `
    --collect-all tkinterdnd2 --collect-all customtkinter --collect-all av `
    --collect-all docx --collect-all fpdf --hidden-import tkinter app.py
Check "PyInstaller"
Write-Host "Done: dist\sesten.exe"

if (-not $ExeOnly) {
    $iscc = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($iscc) {
        & $iscc kurulum.iss
        Check "Inno Setup"
        Write-Host "Done: sesten-setup.exe"
    } else {
        Write-Warning "Inno Setup not found, the installer was not built. https://jrsoftware.org/isinfo.php"
    }
}
