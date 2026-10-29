# Medya - Text Dönüştürücü derleme betiği (Windows, PowerShell)
#
# Gerekenler:
#   - Python 3.13 (64 bit, tkinter dahil)
#   - Inno Setup 6 (isteğe bağlı: sadece kurulum dosyası için)
#
# ÖNEMLİ: Klasör yolu KISA olmalı (örneğin C:\mt). Uzun yollarda onnxruntime "Dosya adı çok uzun"
# hatası verir ve derleme başarısız olur.
#
# Kullanım:   .\build.ps1            -> dist\MedyaText.exe ve MedyaTextKurulum.exe
#             .\build.ps1 -SadeceExe -> yalnızca dist\MedyaText.exe
param([switch]$SadeceExe)
# Not: "Stop" kullanılmıyor. Windows PowerShell 5.1'de PyInstaller'ın bilgi satırları (stderr) yanlışlıkla hata sayılıyor.
# Bunun yerine her komutun başarısı çıkış koduyla kontrol edilir.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Kontrol($ad) { if ($LASTEXITCODE -ne 0) { throw "$ad başarısız oldu (çıkış kodu $LASTEXITCODE)." } }

if ($PSScriptRoot.Length -gt 60) {
    Write-Warning "Klasör yolu uzun ($($PSScriptRoot.Length) karakter). Daha kısa bir yola taşıyın (örneğin C:\mt)."
}

if (-not (Test-Path .\venv)) { py -3.13 -m venv venv; Kontrol "Sanal ortam oluşturma (Python 3.13 kurulu mu?)" }
.\venv\Scripts\python.exe -m pip install --upgrade pip
Kontrol "pip güncelleme"
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Kontrol "Paket kurulumu"

# Bazı kurulumlarda sanal ortam tkinter'ın Tcl dosyalarını bulamaz; gerekirse elle gösteriyoruz.
$base = & .\venv\Scripts\python.exe -c "import sys; print(sys.base_prefix)"
if (-not $env:TCL_LIBRARY -and (Test-Path "$base\tcl\tcl8.6")) {
    $env:TCL_LIBRARY = "$base\tcl\tcl8.6"
    $env:TK_LIBRARY = "$base\tcl\tk8.6"
}

Remove-Item dist, build -Recurse -Force -ErrorAction SilentlyContinue
.\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name MedyaText `
    --icon app.ico --add-data "app.ico;." `
    --collect-all faster_whisper --collect-all ctranslate2 --collect-all onnxruntime `
    --collect-all tkinterdnd2 --collect-all customtkinter --collect-all av `
    --collect-all docx --collect-all fpdf --hidden-import tkinter app.py
Kontrol "PyInstaller"
Write-Host "Hazır: dist\MedyaText.exe"

if (-not $SadeceExe) {
    $iscc = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($iscc) {
        & $iscc kurulum.iss
        Kontrol "Inno Setup"
        Write-Host "Hazır: MedyaTextKurulum.exe"
    } else {
        Write-Warning "Inno Setup bulunamadı, kurulum dosyası oluşturulmadı. https://jrsoftware.org/isinfo.php"
    }
}
