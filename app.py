"""sesten: ses ve videoları yazıya çeviren, tamamen çevrimdışı çalışan masaüstü uygulaması."""
import ctypes
import json
import math
import mimetypes
import os
import queue
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

# Pencereli (konsolsuz) exe'de stdout/stderr None olur; tqdm/huggingface çökmesin diye.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import customtkinter as ctk
from PIL import Image, ImageDraw
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

LANG = "tr"          # arayüz dili: "tr" (varsayılan), "en", "de" ya da "it"
LANGS = [("tr", "Türkçe"), ("en", "English"), ("de", "Deutsch"), ("it", "Italiano")]

APP_VERSION = "1.2.0"
REPO = "mhmtkochan/sesten"
UPDATE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
UPDATE_URL = f"https://github.com/{REPO}/releases/latest/download/sesten-setup.exe"

# Türkçe metin anahtar, İngilizce karşılığı değer. İngilizce seçilince metin buradan bulunur.
EN = {
    # üst bar, tema
    "Ses ve videodan yazıya": "Audio and video to text",
    "Tema": "Theme", "TEMA": "THEME", "RENK": "COLOR",
    "Otomatik": "Automatic", "Açık": "Light", "Koyu": "Dark",
    "Yumuşak": "Soft", "Karamel": "Caramel", "Bal": "Honey", "Adaçayı": "Sage",
    "Okyanus": "Ocean", "Nergis": "Daffodil", "Lavanta": "Lavender",
    "SİMGE": "ICON", "Mavi": "Blue", "Gökyüzü": "Sky", "Bakır": "Copper", "Mor": "Purple",
    "Limon": "Lemon", "Yeşil": "Green",
    # giriş ekranı
    "Ses veya video dosyasının bağlantısını yapıştırın": "Paste a link to an audio or video file",
    "Yükle": "Load",
    "veya": "or",
    "Dosyaları buraya sürükleyebilirsiniz": "You can drag your files here",
    "ya da buraya tıklayıp bir veya birden fazla dosya seçebilirsiniz": "or click here to choose one or more files",
    "MP3 · WAV · M4A · MP4 · MKV · MOV ve daha fazlası": "MP3 · WAV · M4A · MP4 · MKV · MOV and more",
    "Ses veya video dosyası seç": "Choose an audio or video file",
    "Ses ve video dosyaları": "Audio and video files",
    "Tüm dosyalar": "All files",
    "Klasör seçildi": "Folder selected",
    "Lütfen klasör yerine ses veya video dosyaları seçin.":
        "Please choose audio or video files instead of a folder.",
    "Bu dosya açılamadı.\n\nDosyanın yerinde olduğundan ve başka bir program tarafından kullanılmadığından emin olun.":
        "This file could not be opened.\n\nMake sure the file is in place and not in use by another program.",
    "Bağlantı girilmedi": "No link entered",
    "Lütfen bir ses veya video dosyasının bağlantısını yapıştırın.": "Please paste a link to an audio or video file.",
    "Geçersiz bağlantı": "Invalid link",
    "Bağlantı http:// veya https:// ile başlamalıdır.": "The link must start with http:// or https://.",
    "Bağlantı kontrol ediliyor…": "Checking the link…",
    # bağlantı indirme hataları
    "Sunucu dosyayı vermedi (hata kodu {code}).\n\nBağlantının herkese açık ve doğru olduğundan emin olun.":
        "The server did not provide the file (error code {code}).\n\nMake sure the link is public and correct.",
    "Bağlantıya ulaşılamadı.\n\nİnternet bağlantınızı ve adresi kontrol edin.\n\n({err})":
        "The link could not be reached.\n\nCheck your internet connection and the address.\n\n({err})",
    "Dosya alınamadı.\n\n({err})": "The file could not be fetched.\n\n({err})",
    "Bu bağlantı bir ses veya video dosyası değil, bir web sayfası.\n\nYalnızca doğrudan dosya bağlantıları desteklenir (örneğin .mp3 veya .mp4 ile biten adresler). Video sitelerindeki sayfa bağlantıları desteklenmez. Dosyanız bilgisayarınızda varsa doğrudan ana ekrandaki alana sürükleyebilirsiniz.":
        "This link is not an audio or video file, it is a web page.\n\nOnly direct file links are supported (for example addresses ending in .mp3 or .mp4). Page links from video sites are not supported. If you have the file on your computer, you can drag it into the area on the main screen.",
    "Bağlantıdan veri gelmedi. Adresi kontrol edin.": "No data came from the link. Check the address.",
    "dosya": "file",
    # seçenekler
    "Süre: {dur}": "Duration: {dur}",
    "süre okunamadı": "duration unavailable",
    "Değiştir": "Change",
    "Çevirme Hızı": "Transcription speed",
    "Tahmini süre": "Estimated time",
    "Konuşma dili": "Spoken language",
    "Transkripti başlat": "Start transcription",
    "Hızlı": "Fast", "Dengeli": "Balanced", "Güvenli": "Accurate",
    "Dosyaya göre en uygununu seçer": "Picks the best option for your file",
    "En hızlı, günlük kayıtlar için": "Fastest, good for everyday recordings",
    "Hız ve doğruluk bir arada": "Speed and accuracy together",
    "En yüksek doğruluk, daha yavaş": "Highest accuracy, slower",
    "Otomatik: {title} seçildi": "Automatic: {title} selected",
    "İlk kullanımda ek dosyalar indirilir (yaklaşık {size}, internet gerekir)":
        "Extra files (about {size}) are downloaded on first use. Internet required.",
    "~1,6 GB": "~1.6 GB",
    "~1 dk'dan az": "under 1 min",
    # ilerleme
    "Hazırlanıyor…": "Preparing…",
    "İptal": "Cancel",
    "İptal ediliyor…": "Cancelling…",
    "İlk kullanım için gerekli dosyalar indiriliyor…\nBu işlem yalnızca bir kez yapılır ve internet bağlantısı gerekir.":
        "Downloading the files needed for first use…\nThis happens only once and needs an internet connection.",
    "Dönüştürme işlemi hazırlanıyor…": "Getting the transcription ready…",
    "Dosya indiriliyor…": "Downloading the file…",
    "Hesaplanıyor…": "Calculating…",
    "Tahmini kalan süre: {t}": "Estimated time left: {t}",
    "Transkript çıkarılamadı.\n\n{err}": "The transcript could not be created.\n\n{err}",
    # sonuç
    "Transkript hazır": "Transcript ready",
    "{t} sürdü": "took {t}",
    "Düz metin": "Plain text",
    "Zaman damgalı": "With timestamps",
    "(Konuşma bulunamadı)": "(No speech found)",
    "İlk {n} satır gösteriliyor (toplam {total} satır). İndirilen dosya tamamını içerir.":
        "Showing the first {n} lines (of {total}). The downloaded file contains everything.",
    "Yeni dosya": "New file",
    "İndir": "Download",
    "Dosya biçimi": "File format",
    "Kopyala": "Copy",
    "Kopyalandı ✓": "Copied ✓",
    "Bir metin seçin": "Select a text",
    "2 dosyayı indir": "Download 2 files",
    "Sadece zaman damgalı seçildi (altyazı biçimi)": "Only timestamped selected (subtitle format)",
    "İkisi de seçildi": "Both selected",
    "Sadece düz metin seçildi": "Only plain text selected",
    "Sadece zaman damgalı seçildi": "Only timestamped selected",
    "İndirmek istediklerinizi işaretleyin": "Tick what you want to download",
    "Word belgesi": "Word document",
    "Metin dosyası": "Text file",
    "Altyazı": "Subtitles",
    "Düzenlemek için en uygunu": "Best for editing",
    "Paylaşmak ve yazdırmak için": "For sharing and printing",
    "En sade, her cihazda açılır": "Plainest, opens anywhere",
    "Videoya altyazı eklemek için": "For adding subtitles to a video",
    "{stem} (zaman damgalı)": "{stem} (timestamped)",
    "Kaydet": "Save",
    "Dosyaların kaydedileceği klasörü seçin": "Choose a folder to save the files in",
    "Şu dosyalar zaten var, üzerine yazılsın mı?\n\n{files}": "These files already exist. Overwrite them?\n\n{files}",
    "Dosya kaydedilemedi.\n\nSeçtiğiniz konuma yazılamadı. Başka bir klasör deneyin.\n({err})":
        "The file could not be saved.\n\nCould not write to the chosen location. Try another folder.\n({err})",
    "Dosya indirme işlemi tamamlandı.": "File download complete.",
    "Tamam": "OK",
    # kuyruk
    "Dönüştürme kuyruğu": "Transcription queue",
    "{m} seçili": "{m} selected",
    "{m} dönüştürülüyor": "{m} in progress",
    "Tümünü seç": "Select all",
    "+ Dosya ekle": "+ Add files",
    "Hepsine uygula": "Apply to all",
    "Hız": "Speed",
    "Dil": "Language",
    "İndirme biçimi": "Download format",
    "Listeyi temizle": "Clear list",
    "Kuyruğu durdur": "Stop queue",
    "Seçilenleri dönüştür ({n})": "Transcribe selected ({n})",
    "Dönüştürülüyor…": "Transcribing…",
    "Tahmini toplam süre ({files})": "Estimated total time ({files})",
    "Tahmini toplam süre": "Estimated total time",
    "Tahmini kalan süre ({files})": "Estimated time left ({files})",
    "Tamamlandı": "Completed",
    "Hazır": "Ready",
    "Sırada · {n}": "Queued · {n}",
    "Hata": "Error",
    "Okunamadı": "Unreadable",
    "sıra bekliyor": "waiting in queue",
    "dönüştürülüyor": "in progress",
    "tamamlandı": "completed",
    "tahmini {t}": "est. {t}",
    "Görüntüle": "View",
    "kalan {t}": "{t} left",
    "birkaç saniye kaldı": "a few seconds left",
    "Ses bulunamadı": "No audio found",
    "Dosya bozuk ya da desteklenmiyor": "File is damaged or not supported",
    "Dönüştürülemedi": "Could not be transcribed",
    "Gerekli dosyalar indiriliyor…": "Downloading required files…",
    "{done}/{tot} dosya tamamlandı": "{done}/{tot} completed",
    "Hepsi tamamlandı": "All completed",
    "{n} transkript hazır": "{n} ready",
    "{n} transkript hazır · {e} hata": "{n} ready · {e} failed",
    "Tahmini kalan süre {t}": "Estimated time left {t}",
    "Sıradaki dosya dönüştürülüyor · {i}/{n}": "Transcribing next file · {i}/{n}",
    "Tüm dosyalar tamamlandı · {n}/{n}": "All files completed · {n}/{n}",
    "Transkriptlere kuyruk ekranından ulaşabilirsiniz": "You can reach the transcripts from the queue screen",
    "Kuyruğa git": "Go to queue",
    "← Geri": "← Back",
    "{name} tamamlandı · sıradaki dosya başladı": "{name} completed · next file started",
    "{name} tamamlandı": "{name} completed",
    "{name} dönüştürülemedi": "{name} could not be transcribed",
    "Kuyruk durduruldu. Çalışan dosya tamamlanınca durur.": "Queue stopped. It will stop once the running file finishes.",
    "Zaten kuyrukta": "Already in the queue",
    "Seçtiğiniz dosyalar listede var.": "The files you chose are already in the list.",
    "Kuyruk dolu": "Queue is full",
    "Kuyruğa en fazla {n} dosya eklenebilir.": "The queue can hold at most {n} files.",
    "Yeni dosya seçilsin mi?": "Start with a new file?",
    "Kuyruk temizlenir; indirmediğiniz transkriptler kaybolur.":
        "The queue will be cleared and transcripts you have not downloaded will be lost.",
    "Çalışan dönüştürme de durdurulur.": "The running transcription will also be stopped.",
    "Evet, temizle": "Yes, clear",
    "Vazgeç": "Cancel",
    "Üzerine yaz": "Overwrite",
    "Yeni sürüm var: {v}": "New version available: {v}",
}

DE = {
    "Ses ve videodan yazıya": "Audio und Video in Text",
    "Tema": "Design",
    "TEMA": "DESIGN",
    "RENK": "FARBE",
    "Otomatik": "Automatisch",
    "Açık": "Hell",
    "Koyu": "Dunkel",
    "Yumuşak": "Sanft",
    "Karamel": "Karamell",
    "Bal": "Honig",
    "Adaçayı": "Salbei",
    "Okyanus": "Ozean",
    "Nergis": "Narzisse",
    "Lavanta": "Lavendel",
    "SİMGE": "SYMBOL",
    "Mavi": "Blau",
    "Gökyüzü": "Himmel",
    "Bakır": "Kupfer",
    "Mor": "Lila",
    "Limon": "Zitrone",
    "Yeşil": "Grün",
    "Ses veya video dosyasının bağlantısını yapıştırın": "Link zu einer Audio- oder Videodatei einfügen",
    "Yükle": "Laden",
    "veya": "oder",
    "Dosyaları buraya sürükleyebilirsiniz": "Sie können Ihre Dateien hierher ziehen",
    "ya da buraya tıklayıp bir veya birden fazla dosya seçebilirsiniz": "oder hier klicken, um eine oder mehrere Dateien auszuwählen",
    "MP3 · WAV · M4A · MP4 · MKV · MOV ve daha fazlası": "MP3 · WAV · M4A · MP4 · MKV · MOV und mehr",
    "Ses veya video dosyası seç": "Audio- oder Videodatei auswählen",
    "Ses ve video dosyaları": "Audio- und Videodateien",
    "Tüm dosyalar": "Alle Dateien",
    "Klasör seçildi": "Ordner ausgewählt",
    "Lütfen klasör yerine ses veya video dosyaları seçin.": "Bitte wählen Sie Audio- oder Videodateien statt eines Ordners aus.",
    "Bu dosya açılamadı.\n\nDosyanın yerinde olduğundan ve başka bir program tarafından kullanılmadığından emin olun.": "Diese Datei konnte nicht geöffnet werden.\n\nStellen Sie sicher, dass die Datei vorhanden ist und nicht von einem anderen Programm verwendet wird.",
    "Bağlantı girilmedi": "Kein Link eingegeben",
    "Lütfen bir ses veya video dosyasının bağlantısını yapıştırın.": "Bitte fügen Sie den Link zu einer Audio- oder Videodatei ein.",
    "Geçersiz bağlantı": "Ungültiger Link",
    "Bağlantı http:// veya https:// ile başlamalıdır.": "Der Link muss mit http:// oder https:// beginnen.",
    "Bağlantı kontrol ediliyor…": "Link wird geprüft…",
    "Sunucu dosyayı vermedi (hata kodu {code}).\n\nBağlantının herkese açık ve doğru olduğundan emin olun.": "Der Server hat die Datei nicht bereitgestellt (Fehlercode {code}).\n\nStellen Sie sicher, dass der Link öffentlich und korrekt ist.",
    "Bağlantıya ulaşılamadı.\n\nİnternet bağlantınızı ve adresi kontrol edin.\n\n({err})": "Der Link ist nicht erreichbar.\n\nPrüfen Sie Ihre Internetverbindung und die Adresse.\n\n({err})",
    "Dosya alınamadı.\n\n({err})": "Die Datei konnte nicht abgerufen werden.\n\n({err})",
    "Bu bağlantı bir ses veya video dosyası değil, bir web sayfası.\n\nYalnızca doğrudan dosya bağlantıları desteklenir (örneğin .mp3 veya .mp4 ile biten adresler). Video sitelerindeki sayfa bağlantıları desteklenmez. Dosyanız bilgisayarınızda varsa doğrudan ana ekrandaki alana sürükleyebilirsiniz.": "Dieser Link ist keine Audio- oder Videodatei, sondern eine Webseite.\n\nUnterstützt werden nur direkte Dateilinks (zum Beispiel Adressen, die auf .mp3 oder .mp4 enden). Seitenlinks von Videoportalen werden nicht unterstützt. Wenn Sie die Datei auf Ihrem Computer haben, können Sie sie in den Bereich auf dem Startbildschirm ziehen.",
    "Bağlantıdan veri gelmedi. Adresi kontrol edin.": "Vom Link kamen keine Daten. Prüfen Sie die Adresse.",
    "dosya": "Datei",
    "Süre: {dur}": "Dauer: {dur}",
    "süre okunamadı": "Dauer nicht verfügbar",
    "Değiştir": "Ändern",
    "Çevirme Hızı": "Transkriptionstempo",
    "Tahmini süre": "Geschätzte Dauer",
    "Konuşma dili": "Gesprochene Sprache",
    "Transkripti başlat": "Transkription starten",
    "Hızlı": "Schnell",
    "Dengeli": "Ausgewogen",
    "Güvenli": "Genau",
    "Dosyaya göre en uygununu seçer": "Wählt automatisch die beste Option",
    "En hızlı, günlük kayıtlar için": "Am schnellsten, für Alltagsaufnahmen",
    "Hız ve doğruluk bir arada": "Tempo und Genauigkeit in einem",
    "En yüksek doğruluk, daha yavaş": "Höchste Genauigkeit, langsamer",
    "Otomatik: {title} seçildi": "Automatisch: {title} gewählt",
    "İlk kullanımda ek dosyalar indirilir (yaklaşık {size}, internet gerekir)": "Beim ersten Mal werden zusätzliche Dateien (etwa {size}) heruntergeladen. Internet erforderlich.",
    "~1,6 GB": "~1,6 GB",
    "~1 dk'dan az": "unter 1 Min.",
    "Hazırlanıyor…": "Wird vorbereitet…",
    "İptal": "Abbrechen",
    "İptal ediliyor…": "Wird abgebrochen…",
    "İlk kullanım için gerekli dosyalar indiriliyor…\nBu işlem yalnızca bir kez yapılır ve internet bağlantısı gerekir.": "Die für die erste Nutzung nötigen Dateien werden heruntergeladen…\nDas geschieht nur einmal und erfordert eine Internetverbindung.",
    "Dönüştürme işlemi hazırlanıyor…": "Transkription wird vorbereitet…",
    "Dosya indiriliyor…": "Datei wird heruntergeladen…",
    "Hesaplanıyor…": "Wird berechnet…",
    "Tahmini kalan süre: {t}": "Geschätzte Restzeit: {t}",
    "Transkript çıkarılamadı.\n\n{err}": "Das Transkript konnte nicht erstellt werden.\n\n{err}",
    "Transkript hazır": "Transkript fertig",
    "{t} sürdü": "dauerte {t}",
    "Düz metin": "Nur Text",
    "Zaman damgalı": "Mit Zeitstempeln",
    "(Konuşma bulunamadı)": "(Keine Sprache gefunden)",
    "İlk {n} satır gösteriliyor (toplam {total} satır). İndirilen dosya tamamını içerir.": "Angezeigt werden die ersten {n} Zeilen (von {total}). Die heruntergeladene Datei enthält alles.",
    "Yeni dosya": "Neue Datei",
    "İndir": "Download",
    "Dosya biçimi": "Dateiformat",
    "Kopyala": "Kopieren",
    "Kopyalandı ✓": "Kopiert ✓",
    "Bir metin seçin": "Text auswählen",
    "2 dosyayı indir": "2 Dateien laden",
    "Sadece zaman damgalı seçildi (altyazı biçimi)": "Nur mit Zeitstempeln gewählt (Untertitelformat)",
    "İkisi de seçildi": "Beide gewählt",
    "Sadece düz metin seçildi": "Nur Text gewählt",
    "Sadece zaman damgalı seçildi": "Nur mit Zeitstempeln gewählt",
    "İndirmek istediklerinizi işaretleyin": "Markieren Sie, was Sie herunterladen möchten",
    "Word belgesi": "Word-Dokument",
    "Metin dosyası": "Textdatei",
    "Altyazı": "Untertitel",
    "Düzenlemek için en uygunu": "Am besten zum Bearbeiten",
    "Paylaşmak ve yazdırmak için": "Zum Teilen und Drucken",
    "En sade, her cihazda açılır": "Am einfachsten, öffnet überall",
    "Videoya altyazı eklemek için": "Untertitel für Videos",
    "{stem} (zaman damgalı)": "{stem} (mit Zeitstempeln)",
    "Kaydet": "Speichern",
    "Dosyaların kaydedileceği klasörü seçin": "Ordner zum Speichern der Dateien wählen",
    "Şu dosyalar zaten var, üzerine yazılsın mı?\n\n{files}": "Diese Dateien existieren bereits. Überschreiben?\n\n{files}",
    "Dosya kaydedilemedi.\n\nSeçtiğiniz konuma yazılamadı. Başka bir klasör deneyin.\n({err})": "Die Datei konnte nicht gespeichert werden.\n\nAn den gewählten Ort konnte nicht geschrieben werden. Versuchen Sie einen anderen Ordner.\n({err})",
    "Dosya indirme işlemi tamamlandı.": "Download der Datei abgeschlossen.",
    "Tamam": "OK",
    "Dönüştürme kuyruğu": "Transkriptions-Warteschlange",
    "{m} seçili": "{m} ausgewählt",
    "{m} dönüştürülüyor": "{m} in Bearbeitung",
    "Tümünü seç": "Alle auswählen",
    "+ Dosya ekle": "+ Dateien hinzufügen",
    "Hepsine uygula": "Auf alle anwenden",
    "Hız": "Tempo",
    "Dil": "Sprache",
    "İndirme biçimi": "Download-Format",
    "Listeyi temizle": "Liste leeren",
    "Kuyruğu durdur": "Warteschlange stoppen",
    "Seçilenleri dönüştür ({n})": "Ausgewählte transkribieren ({n})",
    "Dönüştürülüyor…": "Wird transkribiert…",
    "Tahmini toplam süre ({files})": "Geschätzte Gesamtdauer ({files})",
    "Tahmini toplam süre": "Geschätzte Gesamtdauer",
    "Tahmini kalan süre ({files})": "Geschätzte Restzeit ({files})",
    "Tamamlandı": "Abgeschlossen",
    "Hazır": "Bereit",
    "Sırada · {n}": "Wartet · {n}",
    "Hata": "Fehler",
    "Okunamadı": "Nicht lesbar",
    "sıra bekliyor": "wartet in der Schlange",
    "dönüştürülüyor": "in Bearbeitung",
    "tamamlandı": "abgeschlossen",
    "tahmini {t}": "ca. {t}",
    "Görüntüle": "Ansehen",
    "kalan {t}": "noch {t}",
    "birkaç saniye kaldı": "noch wenige Sekunden",
    "Ses bulunamadı": "Kein Audio gefunden",
    "Dosya bozuk ya da desteklenmiyor": "Datei ist beschädigt oder wird nicht unterstützt",
    "Dönüştürülemedi": "Konnte nicht transkribiert werden",
    "Gerekli dosyalar indiriliyor…": "Erforderliche Dateien werden heruntergeladen…",
    "{done}/{tot} dosya tamamlandı": "{done}/{tot} abgeschlossen",
    "Hepsi tamamlandı": "Alle abgeschlossen",
    "{n} transkript hazır": "{n} fertig",
    "{n} transkript hazır · {e} hata": "{n} fertig · {e} fehlgeschlagen",
    "Tahmini kalan süre {t}": "Geschätzte Restzeit {t}",
    "Sıradaki dosya dönüştürülüyor · {i}/{n}": "Nächste Datei wird transkribiert · {i}/{n}",
    "Tüm dosyalar tamamlandı · {n}/{n}": "Alle Dateien abgeschlossen · {n}/{n}",
    "Transkriptlere kuyruk ekranından ulaşabilirsiniz": "Die Transkripte finden Sie in der Warteschlange",
    "Kuyruğa git": "Zur Warteschlange",
    "← Geri": "← Zurück",
    "{name} tamamlandı · sıradaki dosya başladı": "{name} abgeschlossen · nächste Datei gestartet",
    "{name} tamamlandı": "{name} abgeschlossen",
    "{name} dönüştürülemedi": "{name} konnte nicht transkribiert werden",
    "Kuyruk durduruldu. Çalışan dosya tamamlanınca durur.": "Warteschlange gestoppt. Sie hält an, sobald die laufende Datei fertig ist.",
    "Zaten kuyrukta": "Bereits in der Warteschlange",
    "Seçtiğiniz dosyalar listede var.": "Die gewählten Dateien sind bereits in der Liste.",
    "Kuyruk dolu": "Warteschlange ist voll",
    "Kuyruğa en fazla {n} dosya eklenebilir.": "Die Warteschlange fasst höchstens {n} Dateien.",
    "Yeni dosya seçilsin mi?": "Mit einer neuen Datei beginnen?",
    "Kuyruk temizlenir; indirmediğiniz transkriptler kaybolur.": "Die Warteschlange wird geleert und nicht heruntergeladene Transkripte gehen verloren.",
    "Çalışan dönüştürme de durdurulur.": "Die laufende Transkription wird ebenfalls gestoppt.",
    "Evet, temizle": "Ja, leeren",
    "Vazgeç": "Abbrechen",
    "Üzerine yaz": "Überschreiben",
    "Yeni sürüm var: {v}": "Neue Version verfügbar: {v}",
}

IT = {
    "Ses ve videodan yazıya": "Da audio e video a testo",
    "Tema": "Tema",
    "TEMA": "TEMA",
    "RENK": "COLORE",
    "Otomatik": "Automatico",
    "Açık": "Chiaro",
    "Koyu": "Scuro",
    "Yumuşak": "Morbido",
    "Karamel": "Caramello",
    "Bal": "Miele",
    "Adaçayı": "Salvia",
    "Okyanus": "Oceano",
    "Nergis": "Narciso",
    "Lavanta": "Lavanda",
    "SİMGE": "ICONA",
    "Mavi": "Blu",
    "Gökyüzü": "Cielo",
    "Bakır": "Rame",
    "Mor": "Viola",
    "Limon": "Limone",
    "Yeşil": "Verde",
    "Ses veya video dosyasının bağlantısını yapıştırın": "Incolla il link a un file audio o video",
    "Yükle": "Carica",
    "veya": "oppure",
    "Dosyaları buraya sürükleyebilirsiniz": "Puoi trascinare i tuoi file qui",
    "ya da buraya tıklayıp bir veya birden fazla dosya seçebilirsiniz": "oppure clicca qui per scegliere uno o più file",
    "MP3 · WAV · M4A · MP4 · MKV · MOV ve daha fazlası": "MP3 · WAV · M4A · MP4 · MKV · MOV e altri",
    "Ses veya video dosyası seç": "Scegli un file audio o video",
    "Ses ve video dosyaları": "File audio e video",
    "Tüm dosyalar": "Tutti i file",
    "Klasör seçildi": "Cartella selezionata",
    "Lütfen klasör yerine ses veya video dosyaları seçin.": "Scegli file audio o video invece di una cartella.",
    "Bu dosya açılamadı.\n\nDosyanın yerinde olduğundan ve başka bir program tarafından kullanılmadığından emin olun.": "Impossibile aprire questo file.\n\nAssicurati che il file sia al suo posto e non sia in uso da un altro programma.",
    "Bağlantı girilmedi": "Nessun link inserito",
    "Lütfen bir ses veya video dosyasının bağlantısını yapıştırın.": "Incolla il link a un file audio o video.",
    "Geçersiz bağlantı": "Link non valido",
    "Bağlantı http:// veya https:// ile başlamalıdır.": "Il link deve iniziare con http:// o https://.",
    "Bağlantı kontrol ediliyor…": "Controllo del link…",
    "Sunucu dosyayı vermedi (hata kodu {code}).\n\nBağlantının herkese açık ve doğru olduğundan emin olun.": "Il server non ha fornito il file (codice errore {code}).\n\nAssicurati che il link sia pubblico e corretto.",
    "Bağlantıya ulaşılamadı.\n\nİnternet bağlantınızı ve adresi kontrol edin.\n\n({err})": "Impossibile raggiungere il link.\n\nControlla la connessione a internet e l'indirizzo.\n\n({err})",
    "Dosya alınamadı.\n\n({err})": "Impossibile scaricare il file.\n\n({err})",
    "Bu bağlantı bir ses veya video dosyası değil, bir web sayfası.\n\nYalnızca doğrudan dosya bağlantıları desteklenir (örneğin .mp3 veya .mp4 ile biten adresler). Video sitelerindeki sayfa bağlantıları desteklenmez. Dosyanız bilgisayarınızda varsa doğrudan ana ekrandaki alana sürükleyebilirsiniz.": "Questo link non è un file audio o video, ma una pagina web.\n\nSono supportati solo link diretti ai file (ad esempio indirizzi che terminano con .mp3 o .mp4). I link alle pagine dei siti video non sono supportati. Se hai il file sul computer, puoi trascinarlo nell'area della schermata principale.",
    "Bağlantıdan veri gelmedi. Adresi kontrol edin.": "Dal link non sono arrivati dati. Controlla l'indirizzo.",
    "dosya": "file",
    "Süre: {dur}": "Durata: {dur}",
    "süre okunamadı": "durata non disponibile",
    "Değiştir": "Cambia",
    "Çevirme Hızı": "Velocità di trascrizione",
    "Tahmini süre": "Tempo stimato",
    "Konuşma dili": "Lingua parlata",
    "Transkripti başlat": "Avvia la trascrizione",
    "Hızlı": "Veloce",
    "Dengeli": "Bilanciato",
    "Güvenli": "Accurato",
    "Dosyaya göre en uygununu seçer": "Sceglie l'opzione migliore",
    "En hızlı, günlük kayıtlar için": "Il più veloce, per l'uso quotidiano",
    "Hız ve doğruluk bir arada": "Velocità e precisione insieme",
    "En yüksek doğruluk, daha yavaş": "Massima precisione, più lento",
    "Otomatik: {title} seçildi": "Automatico: scelto {title}",
    "İlk kullanımda ek dosyalar indirilir (yaklaşık {size}, internet gerekir)": "Al primo utilizzo vengono scaricati file aggiuntivi (circa {size}). Serve internet.",
    "~1,6 GB": "~1,6 GB",
    "~1 dk'dan az": "meno di 1 min",
    "Hazırlanıyor…": "Preparazione…",
    "İptal": "Annulla",
    "İptal ediliyor…": "Annullamento…",
    "İlk kullanım için gerekli dosyalar indiriliyor…\nBu işlem yalnızca bir kez yapılır ve internet bağlantısı gerekir.": "Download dei file necessari al primo utilizzo…\nAvviene una sola volta e richiede una connessione a internet.",
    "Dönüştürme işlemi hazırlanıyor…": "Preparazione della trascrizione…",
    "Dosya indiriliyor…": "Download del file…",
    "Hesaplanıyor…": "Calcolo in corso…",
    "Tahmini kalan süre: {t}": "Tempo rimanente stimato: {t}",
    "Transkript çıkarılamadı.\n\n{err}": "Impossibile creare la trascrizione.\n\n{err}",
    "Transkript hazır": "Trascrizione pronta",
    "{t} sürdü": "ha richiesto {t}",
    "Düz metin": "Testo semplice",
    "Zaman damgalı": "Con timestamp",
    "(Konuşma bulunamadı)": "(Nessun parlato trovato)",
    "İlk {n} satır gösteriliyor (toplam {total} satır). İndirilen dosya tamamını içerir.": "Vengono mostrate le prime {n} righe (su {total}). Il file scaricato contiene tutto.",
    "Yeni dosya": "Nuovo file",
    "İndir": "Scarica",
    "Dosya biçimi": "Formato del file",
    "Kopyala": "Copia",
    "Kopyalandı ✓": "Copiato ✓",
    "Bir metin seçin": "Seleziona un testo",
    "2 dosyayı indir": "Scarica 2 file",
    "Sadece zaman damgalı seçildi (altyazı biçimi)": "Selezionato solo con timestamp (formato sottotitoli)",
    "İkisi de seçildi": "Entrambi selezionati",
    "Sadece düz metin seçildi": "Selezionato solo testo semplice",
    "Sadece zaman damgalı seçildi": "Selezionato solo con timestamp",
    "İndirmek istediklerinizi işaretleyin": "Seleziona ciò che vuoi scaricare",
    "Word belgesi": "Documento Word",
    "Metin dosyası": "File di testo",
    "Altyazı": "Sottotitoli",
    "Düzenlemek için en uygunu": "Ideale per modificare",
    "Paylaşmak ve yazdırmak için": "Per condividere e stampare",
    "En sade, her cihazda açılır": "Il più semplice, si apre ovunque",
    "Videoya altyazı eklemek için": "Per sottotitolare un video",
    "{stem} (zaman damgalı)": "{stem} (con timestamp)",
    "Kaydet": "Salva",
    "Dosyaların kaydedileceği klasörü seçin": "Scegli la cartella in cui salvare i file",
    "Şu dosyalar zaten var, üzerine yazılsın mı?\n\n{files}": "Questi file esistono già. Vuoi sovrascriverli?\n\n{files}",
    "Dosya kaydedilemedi.\n\nSeçtiğiniz konuma yazılamadı. Başka bir klasör deneyin.\n({err})": "Impossibile salvare il file.\n\nImpossibile scrivere nella posizione scelta. Prova un'altra cartella.\n({err})",
    "Dosya indirme işlemi tamamlandı.": "Download del file completato.",
    "Tamam": "OK",
    "Dönüştürme kuyruğu": "Coda di trascrizione",
    "{m} seçili": "{m} selezionati",
    "{m} dönüştürülüyor": "{m} in corso",
    "Tümünü seç": "Seleziona tutto",
    "+ Dosya ekle": "+ Aggiungi file",
    "Hepsine uygula": "Applica a tutti",
    "Hız": "Velocità",
    "Dil": "Lingua",
    "İndirme biçimi": "Formato di download",
    "Listeyi temizle": "Svuota elenco",
    "Kuyruğu durdur": "Ferma la coda",
    "Seçilenleri dönüştür ({n})": "Trascrivi i selezionati ({n})",
    "Dönüştürülüyor…": "Trascrizione in corso…",
    "Tahmini toplam süre ({files})": "Tempo totale stimato ({files})",
    "Tahmini toplam süre": "Tempo totale stimato",
    "Tahmini kalan süre ({files})": "Tempo rimanente stimato ({files})",
    "Tamamlandı": "Completato",
    "Hazır": "Pronto",
    "Sırada · {n}": "In coda · {n}",
    "Hata": "Errore",
    "Okunamadı": "Illeggibile",
    "sıra bekliyor": "in attesa nella coda",
    "dönüştürülüyor": "in corso",
    "tamamlandı": "completato",
    "tahmini {t}": "circa {t}",
    "Görüntüle": "Visualizza",
    "kalan {t}": "{t} rimanenti",
    "birkaç saniye kaldı": "pochi secondi rimanenti",
    "Ses bulunamadı": "Nessun audio trovato",
    "Dosya bozuk ya da desteklenmiyor": "Il file è danneggiato o non supportato",
    "Dönüştürülemedi": "Impossibile trascrivere",
    "Gerekli dosyalar indiriliyor…": "Download dei file necessari…",
    "{done}/{tot} dosya tamamlandı": "{done}/{tot} completati",
    "Hepsi tamamlandı": "Tutti completati",
    "{n} transkript hazır": "{n} pronti",
    "{n} transkript hazır · {e} hata": "{n} pronti · {e} falliti",
    "Tahmini kalan süre {t}": "Tempo rimanente stimato {t}",
    "Sıradaki dosya dönüştürülüyor · {i}/{n}": "Trascrizione del file successivo · {i}/{n}",
    "Tüm dosyalar tamamlandı · {n}/{n}": "Tutti i file completati · {n}/{n}",
    "Transkriptlere kuyruk ekranından ulaşabilirsiniz": "Puoi raggiungere le trascrizioni dalla schermata della coda",
    "Kuyruğa git": "Vai alla coda",
    "← Geri": "← Indietro",
    "{name} tamamlandı · sıradaki dosya başladı": "{name} completato · avviato il file successivo",
    "{name} tamamlandı": "{name} completato",
    "{name} dönüştürülemedi": "Impossibile trascrivere {name}",
    "Kuyruk durduruldu. Çalışan dosya tamamlanınca durur.": "Coda fermata. Si fermerà al termine del file in corso.",
    "Zaten kuyrukta": "Già in coda",
    "Seçtiğiniz dosyalar listede var.": "I file scelti sono già nell'elenco.",
    "Kuyruk dolu": "La coda è piena",
    "Kuyruğa en fazla {n} dosya eklenebilir.": "La coda può contenere al massimo {n} file.",
    "Yeni dosya seçilsin mi?": "Ricominciare con un nuovo file?",
    "Kuyruk temizlenir; indirmediğiniz transkriptler kaybolur.": "La coda verrà svuotata e le trascrizioni non scaricate andranno perse.",
    "Çalışan dönüştürme de durdurulur.": "Anche la trascrizione in corso verrà interrotta.",
    "Evet, temizle": "Sì, svuota",
    "Vazgeç": "Annulla",
    "Üzerine yaz": "Sovrascrivi",
    "Yeni sürüm var: {v}": "Nuova versione disponibile: {v}",
}

TRANSLATIONS = {"en": EN, "de": DE, "it": IT}


def tr(text, **kw):
    """Arayüz metnini seçili dile çevirir; {alan} içeren metinlerde değerleri yerleştirir."""
    out = TRANSLATIONS[LANG].get(text, text) if LANG in TRANSLATIONS else text
    return out.format(**kw) if kw else out


def app_title():
    return "sesten"


def app_tagline():
    return tr("Ses ve videodan yazıya")


_APPDATA = Path(os.environ.get("APPDATA", Path.home()))
CONFIG_PATH = _APPDATA / "sesten" / "config.json"


def _migrate_old_settings():
    """Programın önceki adıyla kaydedilmiş ayar klasörünü yeni ada taşır (tek seferlik, hata olursa sessiz)."""
    old = _APPDATA / "MedyaTextDonusturucu"
    try:
        if old.is_dir() and not CONFIG_PATH.parent.exists():
            old.rename(CONFIG_PATH.parent)
    except Exception:
        pass


_migrate_old_settings()
FONT = "Segoe UI"

_MEDIA_PATTERN = "*.mp3 *.wav *.m4a *.aac *.ogg *.opus *.flac *.wma *.mp4 *.mkv *.mov *.avi *.webm *.wmv *.flv *.m4v *.3gp"


def media_types():
    return [(tr("Ses ve video dosyaları"), _MEDIA_PATTERN), (tr("Tüm dosyalar"), "*.*")]

# key: (başlık, whisper modeli, beam, tahmini işlem süresi / ses süresi (işlemci), indirme boyutu)
MODELS = {
    "fast": ("Hızlı", "small", 1, 0.10, "~500 MB"),
    "balanced": ("Dengeli", "turbo", 3, 0.30, "~1,6 GB"),
    "best": ("Güvenli", "large-v3", 5, 0.90, "~3 GB"),
}
SPEEDS = [
    ("auto", "Otomatik", "Dosyaya göre en uygununu seçer"),
    ("fast", "Hızlı", "En hızlı, günlük kayıtlar için"),
    ("balanced", "Dengeli", "Hız ve doğruluk bir arada"),
    ("best", "Güvenli", "En yüksek doğruluk, daha yavaş"),
]
FORMATS = {
    "docx": ("Word belgesi", ".docx", "Düzenlemek için en uygunu"),
    "pdf": ("PDF", ".pdf", "Paylaşmak ve yazdırmak için"),
    "txt": ("Metin dosyası", ".txt", "En sade, her cihazda açılır"),
    "srt": ("Altyazı", ".srt", "Videoya altyazı eklemek için"),
}

SPOKEN = [
    ("auto", None, "Otomatik algıla", "Auto-detect"), ("tr", "tr", "Türkçe", "Turkish"),
    ("en", "en", "İngilizce", "English"), ("de", "de", "Almanca", "German"), ("fr", "fr", "Fransızca", "French"),
    ("es", "es", "İspanyolca", "Spanish"), ("it", "it", "İtalyanca", "Italian"), ("pt", "pt", "Portekizce", "Portuguese"),
    ("ru", "ru", "Rusça", "Russian"), ("ar", "ar", "Arapça", "Arabic"), ("ja", "ja", "Japonca", "Japanese"),
    ("ko", "ko", "Korece", "Korean"), ("zh", "zh", "Çince", "Chinese"), ("nl", "nl", "Hollandaca", "Dutch"),
    ("pl", "pl", "Lehçe", "Polish"), ("uk", "uk", "Ukraynaca", "Ukrainian"), ("fa", "fa", "Farsça", "Persian"),
    ("hi", "hi", "Hintçe", "Hindi"),
]


SPOKEN_DE_IT = {
    "auto": ("Automatisch erkennen", "Rileva automaticamente"), "tr": ("Türkisch", "Turco"),
    "en": ("Englisch", "Inglese"), "de": ("Deutsch", "Tedesco"), "fr": ("Französisch", "Francese"),
    "es": ("Spanisch", "Spagnolo"), "it": ("Italienisch", "Italiano"), "pt": ("Portugiesisch", "Portoghese"),
    "ru": ("Russisch", "Russo"), "ar": ("Arabisch", "Arabo"), "ja": ("Japanisch", "Giapponese"),
    "ko": ("Koreanisch", "Coreano"), "zh": ("Chinesisch", "Cinese"), "nl": ("Niederländisch", "Olandese"),
    "pl": ("Polnisch", "Polacco"), "uk": ("Ukrainisch", "Ucraino"), "fa": ("Persisch", "Persiano"),
    "hi": ("Hindi", "Hindi"),
}


def spoken_label(key):
    for k, _, name_tr, name_en in SPOKEN:
        if k == key:
            if LANG in ("de", "it"):
                return SPOKEN_DE_IT[k][0 if LANG == "de" else 1]
            return name_en if LANG == "en" else name_tr
    return key


def spoken_code(key):
    return next((code for k, code, _, _ in SPOKEN if k == key), None)

PREVIEW_LINES = 3000         # ekranda gösterilecek en fazla satır; ölçümde 3000 satır bile 0,3 sn'den kısa sürdü

THEME_MODES = [("system", "Otomatik"), ("light", "Açık"), ("dark", "Koyu")]


def _p(bg, zone, dash, ink, muted, card, accent, on_accent, line):
    return dict(bg=bg, zone=zone, dash=dash, ink=ink, muted=muted, card=card,
                accent=accent, on_accent=on_accent, line=line)


# renk adı: (görünen ad, örnek nokta rengi, açık palet, koyu palet)
COLORS = {
    "yumusak": ("Yumuşak", "#8A94A6",
                _p("#F8F7F5", "#EEECE8", "#C4BFB5", "#2B2A28", "#7B766D", "#FDFDFC", "#6F7C8E", "#F8F7F4", "#E3E0DA"),
                _p("#1F2023", "#2A2B2F", "#55575E", "#E6E4DF", "#9A9AA0", "#333439", "#9AA7BA", "#1F2023", "#3A3B40")),
    "karamel": ("Karamel", "#B5763A",
                _p("#FBF6F0", "#F2E8DB", "#CDB08C", "#3B2A1D", "#8A7360", "#FEFBF7", "#A8672E", "#FFF7EC", "#EADCC8"),
                _p("#231B15", "#2F251D", "#6A5240", "#F0E4D6", "#A89480", "#3A2E24", "#D08F52", "#231B15", "#43362A")),
    "bal": ("Bal", "#D1A24F",
            _p("#FCF8F0", "#F5ECD8", "#DCC28A", "#3A2F1A", "#8A7B5C", "#FFFCF7", "#D1A24F", "#2E2411", "#EEE2C8"),
            _p("#211C14", "#2B251A", "#65553A", "#F2E8D3", "#A89B7E", "#342D20", "#D9AE64", "#211C14", "#3D3525")),
    "adacayi": ("Adaçayı", "#7C9A84",
                _p("#F7F9F6", "#EBF0E8", "#BCC8B6", "#25302A", "#6F7D72", "#FCFDFB", "#7C9A84", "#F8FAF6", "#E0E7DB"),
                _p("#1B211D", "#252C27", "#4C5A4F", "#E3EAE2", "#95A398", "#2E362F", "#9DB9A3", "#1B211D", "#343D36")),
    "okyanus": ("Okyanus", "#5F86B0",
                _p("#F5F8FB", "#E9EFF5", "#BCC9D8", "#222C38", "#6B7A8C", "#FBFCFD", "#5F86B0", "#F7F9FB", "#DEE6EE"),
                _p("#1A1F26", "#232A33", "#475466", "#E2E8F0", "#94A0B0", "#2C343F", "#86A9D1", "#1A1F26", "#333D4A")),
    "nergis": ("Nergis", "#CDB43A",
               _p("#FFFEF6", "#F8F4D8", "#D9CF8A", "#33300F", "#807B4A", "#FFFFFB", "#CDB43A", "#2F2B0B", "#EEE9C2"),
               _p("#1D1C12", "#27261A", "#615E33", "#F4F1D2", "#A9A675", "#302F20", "#E3CB57", "#1D1C12", "#3A3922")),
    "lavanta": ("Lavanta", "#8C7BB5",
                _p("#F9F7FB", "#EFEBF4", "#C7BED6", "#2B2535", "#7A6F8A", "#FDFCFE", "#8C7BB5", "#FAF8FC", "#E6E0EE"),
                _p("#1F1C26", "#292533", "#54496A", "#E8E3F0", "#A196B3", "#322D3E", "#AA9BD2", "#1F1C26", "#3B3548")),
}


# ---------------------------------------------------------------- yardımcılar
def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))     # BOM'lu dosyayı da okur
    except Exception:
        return {}


def save_config(cfg):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _units():
    return {"en": ("sec", "min", "h"), "de": ("Sek.", "Min.", "Std."), "it": ("sec", "min", "h")}.get(
        LANG, ("sn", "dk", "sa"))


def fmt_duration(seconds):
    sec_u, min_u, hour_u = _units()
    seconds = max(0, int(round(seconds)))
    if seconds < 60:
        return f"{seconds} {sec_u}"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m} {min_u} {s:02d} {sec_u}" if s else f"{m} {min_u}"
    h, m = divmod(m, 60)
    return f"{h} {hour_u} {m:02d} {min_u}"


def fmt_estimate(seconds):
    _, min_u, hour_u = _units()
    if seconds < 45:
        return tr("~1 dk'dan az")
    minutes = max(1, round(seconds / 60))
    if minutes < 60:
        return f"~{minutes} {min_u}"
    h, m = divmod(minutes, 60)
    return f"~{h} {hour_u} {m:02d} {min_u}"


def fmt_clock(t, srt=False):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def media_duration(path):
    try:
        import av
        with av.open(path) as container:
            if container.duration:
                return container.duration / 1_000_000
    except Exception:
        pass
    return None


def model_cached(model_name):
    try:
        from faster_whisper.utils import download_model
        download_model(model_name, local_files_only=True)
        return True
    except Exception:
        return False


def build_text(segments, timestamps):
    if timestamps:
        return "\n".join(f"[{fmt_clock(s)}] {t}" for s, _, t in segments)
    return "\n".join(t for _, _, t in segments)


def build_srt(segments):
    blocks = []
    for i, (start, end, text) in enumerate(segments, 1):
        blocks.append(f"{i}\n{fmt_clock(start, True)} --> {fmt_clock(end, True)}\n{text}\n")
    return "\n".join(blocks)


def write_docx(path, title, segments, timed):
    from docx import Document
    from docx.shared import Pt, RGBColor
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    doc.add_heading(title, level=1)
    for start, _, text in segments:
        para = doc.add_paragraph()
        para.paragraph_format.space_after = Pt(4)
        if timed:
            run = para.add_run(f"[{fmt_clock(start)}]  ")
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        para.add_run(text)
    doc.save(str(path))


def write_pdf(path, title, segments, timed):
    from fpdf import FPDF
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(True, 20)
    pdf.add_page()
    family, encode = "Helvetica", (lambda s: s.encode("latin-1", "replace").decode("latin-1"))
    for name in ("segoeui.ttf", "arial.ttf", "calibri.ttf"):      # Türkçe karakterler için sistem yazı tipi
        if (fonts / name).exists():
            pdf.add_font("Body", "", str(fonts / name))
            family, encode = "Body", (lambda s: s)
            break
    pdf.set_font(family, size=16)
    pdf.multi_cell(0, 9, encode(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font(family, size=11)
    for start, _, text in segments:
        line = f"[{fmt_clock(start)}]  {text}" if timed else text
        pdf.multi_cell(0, 6.2, encode(line), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)
    pdf.output(str(path))


def write_export(path, fmt, title, segments, timed):
    if fmt == "srt":
        Path(path).write_text(build_srt(segments), encoding="utf-8-sig")
    elif fmt == "txt":
        Path(path).write_text(build_text(segments, timed), encoding="utf-8-sig")
    elif fmt == "docx":
        write_docx(path, title, segments, timed)
    elif fmt == "pdf":
        write_pdf(path, title, segments, timed)


# ---------------------------------------------------------------- renk ve çizim yardımcıları
def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(h1, h2, t):
    a, b = _hex(h1), _hex(h2)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def rounded_polygon(verts, radii, steps=14):
    """Dik açılı köşeleri yuvarlatılmış çokgenin nokta listesi."""
    pts, n = [], len(verts)
    for i, (v, r) in enumerate(zip(verts, radii)):
        if r <= 0:
            pts.append(v)
            continue
        p, nx = verts[i - 1], verts[(i + 1) % n]
        u1 = ((p[0] - v[0]), (p[1] - v[1]))
        u2 = ((nx[0] - v[0]), (nx[1] - v[1]))
        l1, l2 = math.hypot(*u1), math.hypot(*u2)
        u1, u2 = (u1[0] / l1, u1[1] / l1), (u2[0] / l2, u2[1] / l2)
        c = (v[0] + (u1[0] + u2[0]) * r, v[1] + (u1[1] + u2[1]) * r)
        s = (v[0] + u1[0] * r, v[1] + u1[1] * r)
        e = (v[0] + u2[0] * r, v[1] + u2[1] * r)
        a0, a1 = math.atan2(s[1] - c[1], s[0] - c[0]), math.atan2(e[1] - c[1], e[0] - c[0])
        d = a1 - a0
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        for k in range(steps + 1):
            a = a0 + d * k / steps
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts


def dashed_line(draw, pts, on, off, width, fill):
    """Kapalı bir yol boyunca kesikli çizgi çizer."""
    pts = list(pts) + [pts[0]]
    cur, drawing, remain, seg = pts[0], True, on, [pts[0]]
    for nxt in pts[1:]:
        while True:
            dx, dy = nxt[0] - cur[0], nxt[1] - cur[1]
            length = math.hypot(dx, dy)
            if length < 1e-9:
                break
            step = min(remain, length)
            f = step / length
            cur = (cur[0] + dx * f, cur[1] + dy * f)
            if drawing:
                seg.append(cur)
            remain -= step
            if remain <= 1e-9:
                if drawing and len(seg) > 1:
                    draw.line(seg, fill=fill, width=width, joint="curve")
                drawing = not drawing
                remain = on if drawing else off
                seg = [cur] if drawing else []
    if drawing and len(seg) > 1:
        draw.line(seg, fill=fill, width=width, joint="curve")


def render_zone(w, h, pal, highlight=False):
    """Kesikli çerçeveli, ortasında saydam klasör ikonu olan sürükle-bırak alanı (w x h mantıksal px, 2x çıktı)."""
    S = 4
    W, H = w * S, h * S
    img = Image.new("RGB", (W, H), _hex(pal["bg"]))
    d = ImageDraw.Draw(img)
    radius, bw = 30 * S, int(2.5 * S)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=radius, fill=_hex(pal["zone"]))
    inset = bw / 2
    verts = [(inset, inset), (W - 1 - inset, inset), (W - 1 - inset, H - 1 - inset), (inset, H - 1 - inset)]
    outline = rounded_polygon(verts, [radius - inset] * 4, steps=28)
    dashed_line(d, outline, 10 * S, 7 * S, bw, _hex(pal["accent" if highlight else "dash"]))

    # klasör ikonu
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    k = min(150, h * 0.40) / 120 * S
    cx, cy = W / 2, h * 0.31 * S

    def tf(p):
        return (cx + (p[0] - 60) * k, cy + (p[1] - 66) * k)

    shape = [tf(p) for p in rounded_polygon(
        [(10, 25), (46, 25), (57, 37), (110, 37), (110, 107), (10, 107)], [9, 0, 0, 9, 9, 9], steps=10)]
    acc = _hex(pal["accent"])
    ld.polygon(shape, fill=acc + (45,))
    ld.line([tf((10, 53)), tf((110, 53))], fill=acc + (71,), width=int(3 * k))
    ld.line(shape + [shape[0]], fill=acc + (143,), width=int(3.5 * k), joint="curve")
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)


# Program simgeleri: icons/<anahtar>.png (arayüzde) ve .ico (pencere, kısayollar). Varsayılan mavi, .exe'nin simgesi de odur.
ICON_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "icons"
APP_ICONS = [("mavi", "Mavi"), ("gok", "Gökyüzü"), ("bal", "Bal"), ("bakir", "Bakır"),
             ("mor", "Mor"), ("limon", "Limon"), ("yesil", "Yeşil")]
DEFAULT_ICON = "mavi"


def load_app_icon(key, px):
    img = Image.open(ICON_DIR / f"{key}.png").convert("RGBA")
    return img.resize((px, px), Image.Resampling.LANCZOS)


class _GUID(ctypes.Structure):
    _fields_ = [("a", ctypes.c_ulong), ("b", ctypes.c_ushort), ("c", ctypes.c_ushort), ("d", ctypes.c_ubyte * 8)]


def _guid(text):
    g = _GUID()
    ctypes.OleDLL("ole32").CLSIDFromString(text, ctypes.byref(g))
    return g


def _vcall(obj, index, argtypes, *args, restype=ctypes.HRESULT):
    """COM nesnesinin sanal tablosundaki index. yöntemini çağırır (pywin32 olmadan)."""
    vtbl = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtbl[index])(obj, *args)


def _shell_folder(csidl):
    buf = ctypes.create_unicode_buffer(520)
    return buf.value if ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf) == 0 else ""


def _retarget_shortcuts(folders, exe, icon):
    """folders içindeki, exe'ye giden .lnk kısayollarının simgesini icon yapar. Değiştirilen sayısını döndürür."""
    ole32 = ctypes.OleDLL("ole32")
    clsid = _guid("{00021401-0000-0000-C000-000000000046}")        # ShellLink
    iid_link = _guid("{000214F9-0000-0000-C000-000000000046}")     # IShellLinkW
    iid_file = _guid("{0000010B-0000-0000-C000-000000000046}")     # IPersistFile
    want, changed = os.path.normcase(os.path.realpath(exe)), 0
    for folder in folders:
        if not folder or not os.path.isdir(folder):
            continue
        for entry in os.scandir(folder):
            if not entry.name.lower().endswith(".lnk"):
                continue
            link, pf = ctypes.c_void_p(), ctypes.c_void_p()
            try:
                ole32.CoCreateInstance(ctypes.byref(clsid), None, 1, ctypes.byref(iid_link), ctypes.byref(link))
                _vcall(link, 0, [ctypes.c_void_p, ctypes.c_void_p], ctypes.byref(iid_file), ctypes.byref(pf))
                _vcall(pf, 5, [ctypes.c_wchar_p, ctypes.c_ulong], entry.path, 2)         # Load, okuma+yazma
                target = ctypes.create_unicode_buffer(1024)
                _vcall(link, 3, [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong],
                       target, 1024, None, 0)
                if not target.value or os.path.normcase(os.path.realpath(target.value)) != want:
                    continue
                cur, idx = ctypes.create_unicode_buffer(1024), ctypes.c_int()
                _vcall(link, 16, [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)],
                       cur, 1024, ctypes.byref(idx))
                if os.path.normcase(cur.value) == os.path.normcase(icon) and idx.value == 0:
                    continue
                _vcall(link, 17, [ctypes.c_wchar_p, ctypes.c_int], icon, 0)               # SetIconLocation
                _vcall(pf, 6, [ctypes.c_wchar_p, ctypes.c_int], None, 1)                  # Save
                changed += 1
            except OSError:
                pass
            finally:
                for p in (pf, link):
                    if p.value:
                        _vcall(p, 2, [], restype=ctypes.c_ulong)                          # Release
    return changed


def sync_shortcut_icons(key):
    """Masaüstü, Başlat menüsü ve görev çubuğundaki sesten kısayollarının simgesini seçilen simgeye çevirir.
    Yalnızca kurulu .exe olarak çalışırken ve yalnızca bu programa giden kısayollara dokunur; hata olursa sessiz."""
    if not getattr(sys, "frozen", False):
        return
    try:
        if key == DEFAULT_ICON:
            icon = sys.executable
        else:
            dst = CONFIG_PATH.parent / "icons"
            dst.mkdir(parents=True, exist_ok=True)
            icon = str(dst / f"{key}.ico")
            shutil.copyfile(ICON_DIR / f"{key}.ico", icon)
        folders = [_shell_folder(0x10), _shell_folder(0x02),                                  # masaüstü, Başlat menüsü
                   os.path.join(_shell_folder(0x1A), "Microsoft", "Internet Explorer", "Quick Launch",
                                "User Pinned", "TaskBar")]
        ole32 = ctypes.OleDLL("ole32")
        try:
            ole32.CoInitializeEx(None, 2)
        except OSError:
            pass
        if _retarget_shortcuts(folders, sys.executable, icon):
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x1000, None, None)             # simge önbelleğini yenile
    except Exception:
        pass


def render_error_icon(color, px=64):
    """Kırmızı yuvarlak içinde beyaz çarpı."""
    S = 4
    N = px * S
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, N - 1, N - 1], fill=_hex(color))
    a, b, w = N * 0.33, N * 0.67, int(N * 0.085)
    for p, q in (((a, a), (b, b)), ((a, b), (b, a))):
        d.line([p, q], fill=(255, 255, 255), width=w)
        for x, y in (p, q):
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=(255, 255, 255))
    return img.resize((px, px), Image.Resampling.LANCZOS)


def render_flag(code, w=24, h=16):
    """Türkiye, İngiltere, Almanya ve İtalya bayrağı; köşeleri yuvarlatılmış küçük simge (2x çıktı)."""
    S = 8
    W, H = w * S, h * S
    white, red_uk = (255, 255, 255), (200, 16, 46)
    img = Image.new("RGB", (W, H), white)
    d = ImageDraw.Draw(img)
    if code == "tr":
        red = (227, 10, 23)
        d.rectangle([0, 0, W, H], fill=red)
        cx, cy, r1 = H * 0.5, H * 0.5, H * 0.25                      # hilal: büyük beyaz daire, içinde kırmızı daire
        d.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], fill=white)
        r2, cx2 = H * 0.2, cx + H * 0.0625
        d.ellipse([cx2 - r2, cy - r2, cx2 + r2, cy + r2], fill=red)
        sx, sr = H * 0.84, H * 0.125                                 # yıldız (bir ucu sola bakar)
        star = []
        for k in range(10):
            ang = math.pi + k * math.pi / 5
            rad = sr if k % 2 == 0 else sr * 0.382
            star.append((sx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        d.polygon(star, fill=white)
    elif code == "de":
        for i, col in enumerate(((0, 0, 0), (221, 0, 0), (255, 206, 0))):
            d.rectangle([0, H * i / 3, W, H * (i + 1) / 3], fill=col)
    elif code == "it":
        for i, col in enumerate(((0, 146, 70), white, (206, 43, 55))):
            d.rectangle([W * i / 3, 0, W * (i + 1) / 3, H], fill=col)
    else:
        blue = (1, 33, 105)
        d.rectangle([0, 0, W, H], fill=blue)
        for a, b in (((0, 0), (W, H)), ((0, H), (W, 0))):
            d.line([a, b], fill=white, width=int(H * 0.2))
            d.line([a, b], fill=red_uk, width=int(H * 0.07))
        d.rectangle([W / 2 - H * 0.17, 0, W / 2 + H * 0.17, H], fill=white)
        d.rectangle([0, H / 2 - H * 0.17, W, H / 2 + H * 0.17], fill=white)
        d.rectangle([W / 2 - H * 0.1, 0, W / 2 + H * 0.1, H], fill=red_uk)
        d.rectangle([0, H / 2 - H * 0.1, W, H / 2 + H * 0.1], fill=red_uk)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=3 * S, fill=255)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, W - 1, H - 1], radius=3 * S, outline=(0, 0, 0, 46), width=S // 2)
    return out.resize((w * 2, h * 2), Image.Resampling.LANCZOS)


def render_dot(color, px=28):
    S = 4
    img = Image.new("RGBA", (px * S, px * S), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([0, 0, px * S - 1, px * S - 1], fill=_hex(color))
    return img.resize((px, px), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------- kuyruk: dosya modeli, simgeler, işçi, satır
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wma"}
MAX_JOBS = 30                    # kuyrukta aynı anda en fazla dosya
SPEED_NAMES = {key: name for key, name, _ in SPEEDS}
DANGER = {"light": "#C0392B", "dark": "#E5675A"}


def fmt_pct(p):
    """Yüzde yazımı: Türkçede %37, diğer dillerde 37%."""
    n = int(p * 100)
    return f"%{n}" if LANG == "tr" else f"{n}%"


def fcount(n):
    if LANG == "en":
        return f"{n} file" if n == 1 else f"{n} files"
    if LANG == "de":
        return f"{n} Datei" if n == 1 else f"{n} Dateien"
    if LANG == "it":
        return f"{n} file"
    return f"{n} dosya"


def short_name(name, limit):
    return name if len(name) <= limit else name[:limit - 1] + "…"


def spoken_short(key):
    """Satırdaki küçük seçici için kısa dil adı."""
    return tr("Otomatik") if key == "auto" else spoken_label(key)


def probe_media(path):
    """(süre, tür, hata) döndürür. tür: 'audio' | 'video'. hata: kullanıcıya gösterilecek kısa metin (Türkçe anahtar) ya da None."""
    ext = Path(path).suffix.lower()
    kind = "audio" if ext in AUDIO_EXTS else "video"
    try:
        import av
        with av.open(path) as container:
            if not container.streams.audio:
                return None, kind, "Ses bulunamadı"
            if kind == "video" and not container.streams.video:
                kind = "audio"
            return (container.duration / 1_000_000 if container.duration else None), kind, None
    except Exception:  # noqa: BLE001
        return None, kind, "Dosya bozuk ya da desteklenmiyor"


class Job:
    """Kuyruktaki tek bir dosya ve onun ayarları / sonucu."""

    def __init__(self, path, duration, kind, speed, spoken, error=None):
        self.id = 0
        self.path, self.name = path, Path(path).name
        self.duration, self.kind = duration, kind
        self.speed, self.spoken = speed, spoken          # çevirme hızı ve konuşma dili (dosyaya özel)
        self.checked = error is None
        self.status = "error" if error else "ready"      # ready | queued | running | done | error
        self.err_kind = "read" if error else None        # read: dosya okunamadı, run: dönüştürme hatası
        self.note = error or ""                          # satırda gösterilen kısa not (hata ya da hazırlık)
        self.pct = 0.0
        self.segments, self.elapsed = [], 0.0
        self.t_start = None
        self.eta_text = ""
        self.model_key = None
        self.sel = False                                 # son çalıştırmaya dahil mi


def render_file_icon(kind, pal, size=46):
    """Temanın vurgu renginde sayfa ikonu (ses: dalga, video: oynat işareti), yuvarlak köşeli zemin üzerinde."""
    S = 6
    N = size * S
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, N - 1, N - 1], radius=int(14 / 46 * N), fill=_hex(pal["zone"]))
    acc = _hex(pal["accent"])
    u = N * (30 / 46) / 40                      # 40x40'lık çizim alanı karonun ortasındaki 30/46'lık bölgeye sığar
    off = (N - 40 * u) / 2

    def tf(p):
        return (off + p[0] * u, off + p[1] * u)

    page = [tf(p) for p in rounded_polygon([(8, 5), (24, 5), (32, 13), (32, 36), (8, 36)], [3, 0, 0, 3, 3], steps=8)]
    layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    w = max(2, int(2 * u))
    ld.polygon(page, fill=acc + (41,))
    ld.line(page + [page[0]], fill=acc + (191,), width=w, joint="curve")
    ld.line([tf(p) for p in [(24, 5), (24, 11), (26, 13), (32, 13)]], fill=acc + (191,), width=w, joint="curve")
    if kind == "audio":
        for x, y1, y2 in ((14, 24, 28), (18, 20, 32), (22, 22, 30), (26, 25, 27)):
            a, b = tf((x, y1)), tf((x, y2))
            bw = max(2, int(2.4 * u))
            ld.line([a, b], fill=acc + (217,), width=bw)
            for cx, cy in (a, b):
                ld.ellipse([cx - bw / 2, cy - bw / 2, cx + bw / 2, cy + bw / 2], fill=acc + (217,))
    else:
        tri = [tf(p) for p in [(16, 21.5), (16, 30.5), (24, 26)]]
        ld.polygon(tri, fill=acc + (217,))
        ld.line(tri + [tri[0]], fill=acc + (217,), width=max(2, int(1.6 * u)), joint="curve")
    img = Image.alpha_composite(img, layer)
    return img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)


def render_ring(color, k=None, px=24):
    """Dönen halka (k: 0-11. kare) ya da, k=None ise, onay işaretli tam halka."""
    S = 6
    N = px * S
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, w = _hex(color), int(N * 0.13)
    box = [w / 2, w / 2, N - w / 2 - 1, N - w / 2 - 1]
    if k is None:
        d.ellipse(box, outline=c + (255,), width=w)
        d.line([(N * 0.30, N * 0.52), (N * 0.45, N * 0.67), (N * 0.72, N * 0.36)], fill=c + (255,), width=w, joint="curve")
    else:
        d.ellipse(box, outline=c + (70,), width=w)
        d.arc(box, k * 30, k * 30 + 100, fill=c + (255,), width=w)
    return img.resize((px * 2, px * 2), Image.Resampling.LANCZOS)


def render_info_icon(color, fg, px=64):
    """Vurgu renginde yuvarlak içinde 'i' (onay pencereleri için)."""
    S = 4
    N = px * S
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, N - 1, N - 1], fill=_hex(color))
    w, cx, fg = int(N * 0.095), N / 2, _hex(fg)
    d.ellipse([cx - w * 0.75, N * 0.27 - w * 0.75, cx + w * 0.75, N * 0.27 + w * 0.75], fill=fg)
    d.line([(cx, N * 0.43), (cx, N * 0.72)], fill=fg, width=w)
    d.ellipse([cx - w / 2, N * 0.72 - w / 2, cx + w / 2, N * 0.72 + w / 2], fill=fg)
    return img.resize((px, px), Image.Resampling.LANCZOS)


class QueueWorker(threading.Thread):
    """Seçili dosyaları sırayla çevirir. Çeviri motoru bir kere yüklenir ve kuyruk boyunca kullanılır."""

    def __init__(self, run_id, specs, out_queue):
        super().__init__(daemon=True)
        self.run_id, self.specs, self.q = run_id, specs, out_queue
        self.cancel = threading.Event()            # hemen iptal (pencere kapanırken, kuyruk silinirken)
        self.stop_after = threading.Event()        # çalışan dosya bitince dur

    def put(self, *msg):
        self.q.put((msg[0], self.run_id) + msg[1:])

    def run(self):
        model, model_name = None, None
        try:
            from faster_whisper import WhisperModel
            for spec in self.specs:
                if self.cancel.is_set() or self.stop_after.is_set():
                    break
                jid = spec["id"]
                self.put("q_start", jid)
                try:
                    _, name, beam, _, _ = MODELS[spec["model_key"]]
                    if name != model_name:
                        model = None                # eski modeli bırak, sonra yenisini yükle
                        self.put("q_loading", jid, not model_cached(name))
                        model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
                        model_name = name
                    started = time.time()
                    segments_iter, info = model.transcribe(
                        spec["path"], language=spec["language"], beam_size=beam, vad_filter=True)
                    total = info.duration or 1
                    self.put("q_began", jid, total)
                    result = []
                    for seg in segments_iter:
                        if self.cancel.is_set():
                            return
                        text = seg.text.strip()
                        if text:
                            result.append((seg.start, seg.end, text))
                        self.put("q_progress", jid, min(seg.end / total, 1.0))
                    self.put("q_done", jid, result, time.time() - started, total)
                except Exception as exc:  # noqa: BLE001      # bir dosyanın hatası kuyruğu durdurmaz
                    self.put("q_error", jid, f"{type(exc).__name__}: {exc}")
            self.put("q_finished")
        except Exception as exc:  # noqa: BLE001
            self.put("q_failed", f"{type(exc).__name__}: {exc}")


class Chip:
    """Satırdaki küçük seçici: 'Hız  Otomatik ▾'. Tıklanınca on_click(chip) çağrılır."""

    def __init__(self, app, parent, label, big=False):
        self.app, self.locked, self.on_click = app, False, None
        h = 36 if big else 30
        self.frame = ctk.CTkFrame(parent, height=h, corner_radius=h // 2, fg_color=app.T("zone"), cursor="hand2")
        self.k = ctk.CTkLabel(self.frame, text=label, text_color=app.T("muted"), font=app.font(12.5, True), height=h - 6)
        self.v = ctk.CTkLabel(self.frame, text="", text_color=app.tone(), font=app.font(12.5, True), height=h - 6)
        self.k.pack(side="left", padx=(13, 6))
        self.v.pack(side="left", padx=(0, 12))
        bind_tree(self.frame, "<Button-1>", lambda e: self._click())
        bind_tree(self.frame, "<Enter>", lambda e: None if self.locked else self.frame.configure(fg_color=app.T("line")))
        self.frame.bind("<Leave>", lambda e: self.frame.configure(fg_color=app.T("zone")), add="+")

    def set(self, value, locked=False):
        self.locked = locked
        self.v.configure(text=value if locked else value + "  ▾",
                         text_color=self.app.T("muted") if locked else self.app.tone())
        for w in (self.frame, self.k, self.v):
            w.configure(cursor="arrow" if locked else "hand2")

    def _click(self):
        if not self.locked and self.on_click:
            self.on_click(self)


class QRow:
    """Kuyruk ekranındaki tek satır: onay kutusu, ikon, ad, hız/dil seçicileri, durum ve butonlar."""

    def __init__(self, app, parent, job):
        self.app, self.job = app, job
        T = app.T
        self.frame = ctk.CTkFrame(parent, fg_color=T("card"), border_width=2, border_color=T("line"), corner_radius=18)
        self.frame.pack(fill="x", pady=(0, 10), padx=(0, 8))
        f = self.frame
        f.grid_columnconfigure(2, weight=1)
        f.grid_columnconfigure(3, minsize=150)
        f.grid_columnconfigure(4, minsize=190)

        self.var = ctk.BooleanVar(value=job.checked)
        self.cb = ctk.CTkCheckBox(
            f, text="", variable=self.var, command=self._on_check, width=22, checkbox_width=22, checkbox_height=22,
            corner_radius=7, border_width=2, fg_color=T("accent"), hover_color=app.TT("accent", "ink", 0.12),
            checkmark_color=T("on_accent"), border_color=T("dash"))
        self.cb.grid(row=0, column=0, padx=(18, 4), pady=14)
        self.icon = ctk.CTkLabel(f, text="", image=app.file_icon(job.kind))
        self.icon.grid(row=0, column=1, padx=(8, 0))

        info = ctk.CTkFrame(f, fg_color="transparent")
        info.grid(row=0, column=2, sticky="w", padx=(14, 6), pady=12)
        ctk.CTkLabel(info, text=short_name(job.name, 34), text_color=T("ink"), font=app.font(14.5, True),
                     anchor="w").pack(fill="x")
        self.meta = ctk.CTkLabel(info, text="", text_color=T("muted"), font=app.font(12), anchor="w")
        self.meta.pack(fill="x")
        self.chips = ctk.CTkFrame(info, fg_color="transparent")
        self.chips.pack(anchor="w", pady=(8, 0))
        self.chip_speed = Chip(app, self.chips, tr("Hız"))
        self.chip_speed.frame.pack(side="left", padx=(0, 8))
        self.chip_lang = Chip(app, self.chips, tr("Dil"))
        self.chip_lang.frame.pack(side="left")
        self.chip_speed.on_click = lambda c: app.pick_speed(job, c.frame)
        self.chip_lang.on_click = lambda c: app.pick_spoken(job, c.frame)

        self.status = ctk.CTkFrame(f, fg_color="transparent")
        self.status.grid(row=0, column=3, padx=6, sticky="e")
        self.tag = ctk.CTkFrame(self.status, corner_radius=13, fg_color=T("zone"))
        self.tag_lbl = ctk.CTkLabel(self.tag, text="", font=app.font(12, True), text_color=T("muted"), height=24)
        self.tag_lbl.pack(padx=12, pady=1)
        self.stat = ctk.CTkFrame(self.status, fg_color="transparent")
        self.pct = ctk.CTkLabel(self.stat, text="", text_color=T("ink"), font=app.font(19, True), anchor="e")
        self.pct.pack(fill="x")
        self.bar = ctk.CTkProgressBar(self.stat, width=120, height=8, corner_radius=4, fg_color=T("zone"),
                                      progress_color=T("accent"))
        self.bar.pack(pady=(3, 3))
        self.sub = ctk.CTkLabel(self.stat, text="", text_color=T("muted"), font=app.font(12), anchor="e")
        self.sub.pack(fill="x")

        self.actions = ctk.CTkFrame(f, fg_color="transparent", width=1, height=1)   # boşken 200 px yer kaplamasın
        self.actions.grid(row=0, column=4, padx=(6, 18), sticky="e")
        self.btn_x = ctk.CTkButton(self.actions, text="✕", width=32, height=32, corner_radius=16, fg_color="transparent",
                                   hover_color=T("zone"), text_color=T("muted"), font=app.font(15),
                                   command=lambda: app._remove_job(job))
        self.btn_view = ctk.CTkButton(self.actions, text=tr("Görüntüle"), width=app.bw(tr("Görüntüle"), 96, 12), height=32, corner_radius=16,
                                      fg_color=T("zone"), hover_color=T("line"), text_color=app.tone(),
                                      font=app.font(12, True), command=lambda: app.view_job(job))
        self.btn_dl = ctk.CTkButton(self.actions, text=tr("İndir"), width=app.bw(tr("İndir"), 76, 12), height=32, corner_radius=16,
                                    fg_color=T("accent"), hover_color=app.TT("accent", "ink", 0.12),
                                    text_color=T("on_accent"), font=app.font(12, True),
                                    command=lambda: app._download_job(job))
        self.update()

    def destroy(self):
        self.frame.destroy()

    def _on_check(self):
        self.job.checked = self.var.get()
        self.update()
        self.app._refresh_queue_ui()

    def _show_tag(self, text, kind="plain"):
        a = self.app
        self.stat.pack_forget()
        colors = {"plain": (a.T("zone"), a.T("muted")),
                  "queued": (a.TT("card", "accent", 0.22), a.tone()),
                  "error": (tuple(mix(a.pal(m)["card"], DANGER[m], 0.16) for m in ("light", "dark")),
                            (DANGER["light"], DANGER["dark"]))}
        bg, fg = colors[kind]
        self.tag.configure(fg_color=bg)
        self.tag_lbl.configure(text=text, text_color=fg)
        self.tag.pack(anchor="e")

    def update(self):
        if not self.frame.winfo_exists():
            return
        j, a = self.job, self.app
        T = a.T
        locked = j.status != "ready"
        self.var.set(j.checked)
        self.cb.configure(state="disabled" if locked else "normal")
        running = j.status == "running"
        self.frame.configure(
            border_color=T("accent") if running else a.TT("line", "accent", 0.45) if (j.checked and not locked)
            else T("line"),
            fg_color=a.TT("card", "accent", 0.06) if running else T("card"))

        dur = fmt_duration(j.duration) if j.duration else "—"
        if j.status == "error":
            meta = j.note
        elif j.status == "queued":
            meta = f"{dur} · {tr('sıra bekliyor')}"
        elif running:
            meta = f"{dur} · {tr('dönüştürülüyor')}"
        elif j.status == "done":
            meta = f"{dur} · {tr('tamamlandı')}"
        else:
            est = a.est_seconds(a.model_for(j), j.duration)
            meta = dur + (f" · {tr('tahmini {t}', t=fmt_estimate(est))}" if est else "")
        self.meta.configure(text=meta)

        if j.status == "error":
            self.chips.pack_forget()
        else:
            self.chips.pack(anchor="w", pady=(8, 0))
            self.chip_speed.set(tr(SPEED_NAMES[j.speed]), locked)
            self.chip_lang.set(spoken_short(j.spoken), locked)

        if j.status == "ready":
            self._show_tag(tr("Hazır"))
        elif j.status == "queued":
            n = [x for x in a.jobs if x.status == "queued"].index(j) + 1
            self._show_tag(tr("Sırada · {n}", n=n), "queued")
        elif j.status == "error":
            self._show_tag(tr("Okunamadı") if j.err_kind == "read" else tr("Hata"), "error")
        else:
            self.tag.pack_forget()
            self.stat.pack(anchor="e")
            self.update_progress()

        for w in (self.btn_x, self.btn_view, self.btn_dl):
            w.pack_forget()
        if j.status in ("ready", "error"):
            self.btn_x.pack()
        elif j.status == "done":
            self.btn_view.pack(side="left", padx=(0, 8))
            self.btn_dl.pack(side="left")

    def update_progress(self):
        j = self.job
        if j.status == "running":
            began = j.t_start is not None
            self.pct.configure(text=fmt_pct(j.pct) if began else "—")
            self.bar.set(j.pct)
            self.sub.configure(text=(j.eta_text or tr("Hesaplanıyor…")) if began else j.note)
        elif j.status == "done":
            self.pct.configure(text=fmt_pct(1))
            self.bar.set(1)
            self.sub.configure(text=tr("Tamamlandı"))


# ---------------------------------------------------------------- arka plan işçisi
class Worker(threading.Thread):
    def __init__(self, path, model_key, language, out_queue):
        super().__init__(daemon=True)
        self.path, self.model_key, self.language, self.q = path, model_key, language, out_queue
        self.cancel = threading.Event()

    def run(self):
        try:
            from faster_whisper import WhisperModel
            _, model_name, beam, _, _ = MODELS[self.model_key]
            self.q.put(("loading", not model_cached(model_name)))
            model = WhisperModel(model_name, device="cpu", compute_type="int8",
                                 cpu_threads=os.cpu_count() or 4)
            if self.cancel.is_set():
                return self.q.put(("cancelled",))

            started = time.time()
            segments_iter, info = model.transcribe(
                self.path, language=self.language, beam_size=beam, vad_filter=True)
            total = info.duration or 1
            self.q.put(("started", total, info.language))

            result = []
            for seg in segments_iter:
                if self.cancel.is_set():
                    return self.q.put(("cancelled",))
                text = seg.text.strip()
                if text:
                    result.append((seg.start, seg.end, text))
                self.q.put(("progress", min(seg.end / total, 1.0)))
            self.q.put(("done", result, time.time() - started, total))
        except Exception as exc:  # noqa: BLE001
            self.q.put(("error", f"{type(exc).__name__}: {exc}"))


MEDIA_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".wma",
              ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv", ".m4v", ".3gp"}


class LinkError(Exception):
    """Kullanıcıya olduğu gibi gösterilebilecek bağlantı hatası."""


class LinkWorker(threading.Thread):
    """Doğrudan ses/video dosyası bağlantısını geçici klasöre indirir."""

    def __init__(self, url, folder, out_queue):
        super().__init__(daemon=True)
        self.url, self.folder, self.q = url, folder, out_queue
        self.cancel = threading.Event()

    @staticmethod
    def _clean_name(name):
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", urllib.parse.unquote(name)).strip(". ")
        stem, ext = os.path.splitext(name)
        return (stem[:90] or tr("dosya")) + ext

    def run(self):
        try:
            self._download()
        except LinkError as exc:
            self.q.put(("dl_error", str(exc)))
        except urllib.error.HTTPError as exc:
            self.q.put(("dl_error", tr("Sunucu dosyayı vermedi (hata kodu {code}).\n\n"
                                       "Bağlantının herkese açık ve doğru olduğundan emin olun.", code=exc.code)))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if self.cancel.is_set():
                self.q.put(("dl_cancelled",))
            else:
                self.q.put(("dl_error", tr("Bağlantıya ulaşılamadı.\n\nİnternet bağlantınızı ve adresi kontrol edin.\n\n"
                                           "({err})", err=type(exc).__name__)))
        except Exception as exc:  # noqa: BLE001
            self.q.put(("dl_error", tr("Dosya alınamadı.\n\n({err})", err=f"{type(exc).__name__}: {exc}")))

    def _download(self):
        req = urllib.request.Request(self.url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) sesten"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            ctype = (resp.headers.get_content_type() or "").lower()
            fname = resp.headers.get_filename() or os.path.basename(urllib.parse.urlparse(resp.geturl()).path)
            ext = os.path.splitext(fname)[1].lower()
            is_media = ctype.startswith(("audio/", "video/")) or ext in MEDIA_EXTS
            if ctype in ("text/html", "application/xhtml+xml") or not is_media:
                raise LinkError(tr(
                    "Bu bağlantı bir ses veya video dosyası değil, bir web sayfası.\n\n"
                    "Yalnızca doğrudan dosya bağlantıları desteklenir (örneğin .mp3 veya .mp4 ile biten "
                    "adresler). Video sitelerindeki sayfa bağlantıları desteklenmez. Dosyanız bilgisayarınızda "
                    "varsa doğrudan ana ekrandaki alana sürükleyebilirsiniz."))
            name = self._clean_name(fname or tr("dosya"))
            if os.path.splitext(name)[1].lower() not in MEDIA_EXTS:
                name += mimetypes.guess_extension(ctype) or ".mp3"
            path = os.path.join(self.folder, name)
            total = int(resp.headers.get("Content-Length") or 0)
            done, last = 0, 0.0
            self.q.put(("dl_progress", None))
            with open(path, "wb") as fh:
                while True:
                    if self.cancel.is_set():
                        self.q.put(("dl_cancelled",))
                        return
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
                    done += len(chunk)
                    if total and time.time() - last > 0.25:
                        last = time.time()
                        self.q.put(("dl_progress", min(done / total, 1.0)))
        if done == 0:
            raise LinkError(tr("Bağlantıdan veri gelmedi. Adresi kontrol edin."))
        self.q.put(("dl_done", path, name))


def version_tuple(tag):
    return tuple(int(x) for x in re.findall(r"\d+", tag)[:4])


class UpdateChecker(threading.Thread):
    """Açılışta GitHub'daki son sürüm numarasına bakar; daha yeniyse haber verir. Hata olursa sessiz kalır."""

    def __init__(self, out_queue):
        super().__init__(daemon=True)
        self.q = out_queue

    def run(self):
        try:
            req = urllib.request.Request(UPDATE_API, headers={
                "User-Agent": f"sesten/{APP_VERSION}", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                tag = json.loads(resp.read().decode("utf-8")).get("tag_name", "")
            if tag and version_tuple(tag) > version_tuple(APP_VERSION):
                self.q.put(("upd_found", tag))
        except Exception:  # noqa: BLE001      # internet yok, sürüm yok, sunucu yanıt vermedi: önemli değil
            pass


# ---------------------------------------------------------------- açılır liste
def bind_tree(widget, sequence, func):
    """Bir parçaya ve içindekilere aynı olayı bağlar. CustomTkinter etiketleri içlerine de bağladığı için
    aynı tıklama iki kez gelebilir (menü açılıp hemen kapanırdı); aynı olay ikinci kez işlenmez."""
    seen = []

    def once(event):
        key = (event.serial, event.time, str(event.widget))
        if seen and seen[0] == key:
            return None
        seen[:] = [key]
        return func(event)

    def attach(w):
        w.bind(sequence, once, add="+")
        for child in w.winfo_children():
            attach(child)

    attach(widget)


class Dropdown:
    """Çevirme hızı / dosya biçimi gibi açıklamalı seçim listesi."""

    def __init__(self, app, parent, width, items_fn, value_fn, on_select, up=False):
        self.app, self.width, self.up = app, width, up
        self.items_fn, self.value_fn, self.on_select = items_fn, value_fn, on_select
        self.btn = ctk.CTkFrame(parent, width=width, height=48, corner_radius=16, fg_color=app.T("card"),
                                border_width=2, border_color=app.T("line"), cursor="hand2")
        self.btn.pack_propagate(False)
        self.name = ctk.CTkLabel(self.btn, text="", text_color=app.T("ink"), font=app.font(14, True))
        self.name.pack(side="left", padx=(16, 0))
        ctk.CTkLabel(self.btn, text="▾", text_color=app.T("muted"), font=app.font(13)).pack(side="right", padx=(6, 14))
        self.extra = ctk.CTkLabel(self.btn, text="", text_color=app.T("muted"), font=app.font(12))
        self.extra.pack(side="right")
        bind_tree(self.btn, "<Button-1>", lambda e: self.toggle())
        self.refresh()

    def refresh(self):
        cur = self.value_fn()
        for it in self.items_fn():
            if it["key"] == cur:
                self.name.configure(text=it["name"])
                self.extra.configure(text=it.get("right", ""))

    def toggle(self):
        if self.app.overlay and self.app.overlay[3] is self:
            self.app.close_overlay()
        else:
            self.open()

    def open(self):
        app = self.app
        pop = ctk.CTkFrame(app, fg_color=app.T("card"), border_width=1, border_color=app.T("line"), corner_radius=16)
        cur = self.value_fn()
        items = self.items_fn()
        for i, it in enumerate(items):
            selected = it["key"] == cur
            base = app.TT("card", "accent", 0.18) if selected else "transparent"
            row = ctk.CTkFrame(pop, corner_radius=11, fg_color=base, cursor="hand2")
            row.pack(fill="x", padx=8, pady=(8 if i == 0 else 0, 8 if i == len(items) - 1 else 2))
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=(12, 6), pady=7)
            ctk.CTkLabel(left, text=it["name"], text_color=app.T("ink"), font=app.font(14, True),
                         anchor="w").pack(fill="x")
            ctk.CTkLabel(left, text=it["desc"], text_color=app.T("muted"), font=app.font(11.5),
                         anchor="w").pack(fill="x")
            if it.get("right"):
                ctk.CTkLabel(row, text=it["right"], text_color=app.T("ink"), font=app.font(12.5, True)).pack(
                    side="right", padx=12)
            hover = app.T("zone")
            bind_tree(row, "<Enter>", lambda e, r=row, h=hover: r.configure(fg_color=h))
            row.bind("<Leave>", lambda e, r=row, b=base: self._leave(r, b, e), add="+")
            bind_tree(row, "<Button-1>", lambda e, k=it["key"]: self._pick(k))
        pop.update_idletasks()
        ph = app.lg(pop.winfo_reqheight())
        pop.pack_propagate(False)                 # genişliği kutunun genişliğine sabitle
        pop.configure(width=self.width, height=ph)
        bx = app.lg(self.btn.winfo_rootx() - app.winfo_rootx())
        by = app.lg(self.btn.winfo_rooty() - app.winfo_rooty())
        y = by - ph - 6 if self.up else by + 54
        pop.place(x=bx, y=y)
        pop.lift()
        self.btn.configure(border_color=app.T("accent"))
        app.set_overlay(pop, [self.btn], self, on_close=lambda: self.btn.winfo_exists() and self.btn.configure(
            border_color=app.T("line")))

    @staticmethod
    def _leave(row, base, event):
        w = row.winfo_containing(event.x_root, event.y_root)
        if w is not None and str(w).startswith(str(row)):
            return
        row.configure(fg_color=base)

    def _pick(self, key):
        def apply():
            self.app.close_overlay()
            self.on_select(key)
            self.refresh()
        self.app.after(10, apply)      # tıklama olayı bitmeden pencereyi yok etmeyelim


# ---------------------------------------------------------------- hata penceresi
class ErrorDialog(ctk.CTkToplevel):
    """Uygulamanın temasına uyan pencere: kırmızı simgeli hata (kind="error") ya da onay sorusu (kind="info")."""

    def __init__(self, app, message, kind="error", buttons=None):
        super().__init__(app)
        self.app, self.result = app, None
        self.withdraw()
        self.title(app_title())
        self.resizable(False, False)
        self.configure(fg_color=app.T("bg"))

        buttons = buttons or [(tr("Tamam"), True, True)]        # (yazı, sonuç, ana düğme mi)
        self.default = next((value for _, value, primary in buttons if primary), None)
        self.escape = False if len(buttons) > 1 else self.default
        head, _, body = message.strip().partition("\n\n")
        if kind == "info":
            pl, pd = app.pal("light"), app.pal("dark")
            icon = ctk.CTkImage(light_image=render_info_icon(pl["accent"], pl["on_accent"]),
                                dark_image=render_info_icon(pd["accent"], pd["on_accent"]), size=(44, 44))
        else:
            icon = ctk.CTkImage(light_image=render_error_icon("#D14343"), dark_image=render_error_icon("#E5675A"),
                                size=(44, 44))
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=28, pady=(26, 8))
        ctk.CTkLabel(wrap, image=icon, text="").pack(side="left", anchor="n", padx=(0, 18))
        text = ctk.CTkFrame(wrap, fg_color="transparent")
        text.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(text, text=head, text_color=app.T("ink"), font=app.font(15, True), anchor="w", justify="left",
                     wraplength=380).pack(fill="x")
        if body:
            ctk.CTkLabel(text, text=body, text_color=app.T("muted"), font=app.font(13), anchor="w", justify="left",
                         wraplength=380).pack(fill="x", pady=(10, 0))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(side="bottom", anchor="e", padx=28, pady=(8, 24))
        for label, value, primary in buttons:
            width = max(120, 9 * len(label) + 44)
            if primary:
                b = app._primary_button(row, label, lambda v=value: self.close(v), width=width)
            else:
                b = app._soft_button(row, label, lambda v=value: self.close(v), width=width)
            b.configure(height=40, corner_radius=20, font=app.font(14, True))
            b.pack(side="left", padx=(10, 0))

        self.update_idletasks()
        w, h = app.lg(self.winfo_reqwidth()), app.lg(self.winfo_reqheight())
        x = app.lg(app.winfo_rootx()) + (app.lg(app.winfo_width()) - w) // 2
        y = app.lg(app.winfo_rooty()) + (app.lg(app.winfo_height()) - h) // 3
        self.geometry(f"{int(w)}x{int(h)}+{int(max(x, 0))}+{int(max(y, 0))}")
        self.transient(app)
        self.deiconify()
        self.bind("<Return>", lambda e: self.close(self.default))
        self.bind("<Escape>", lambda e: self.close(self.escape))
        self.protocol("WM_DELETE_WINDOW", lambda: self.close(self.escape))
        self.after(60, self._modal)
        self.after(300, self._icon)

    def _modal(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _icon(self):
        ico = ICON_DIR / f"{self.app.icon_key}.ico"
        try:
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    def close(self, result=None):
        self.result = result
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if self.app.error_dialog is self:
            self.app.error_dialog = None


# ---------------------------------------------------------------- uygulama
class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        global LANG
        self.cfg = load_config()
        LANG = self.cfg.get("ui_lang", "tr")
        if LANG not in dict(LANGS):
            LANG = "tr"
        self.theme_mode = self.cfg.get("theme", "system")
        if self.theme_mode not in [m for m, _ in THEME_MODES]:
            self.theme_mode = "system"
        self.color = self.cfg.get("color", "yumusak")
        if self.color not in COLORS:
            self.color = "yumusak"
        self.icon_key = self.cfg.get("icon", DEFAULT_ICON)
        if self.icon_key not in dict(APP_ICONS):
            self.icon_key = DEFAULT_ICON
        ctk.set_appearance_mode(self.theme_mode)

        self.title(app_title())
        self.geometry("920x700")
        self.minsize(860, 640)
        self.configure(fg_color=self.T("bg"))

        self.file_path = None
        self.display_name = None          # bağlantıdan inen dosyanın görünen adı
        self.file_duration = None
        self.tmp_dir = None
        self.error_dialog = None
        self.link_worker = None
        self.stack = None
        self.t_start = None
        self.speed = self.cfg.get("speed", "auto")
        if self.speed not in [s[0] for s in SPEEDS]:
            self.speed = "auto"
        self.fmt = self.cfg.get("format", "docx")
        if self.fmt not in FORMATS:
            self.fmt = "docx"
        self.spoken = self.cfg.get("spoken")
        if self.spoken not in [s[0] for s in SPOKEN]:             # eski sürüm ayarında Türkçe ad saklanıyordu
            old = self.cfg.get("language")
            self.spoken = next((s[0] for s in SPOKEN if old in (s[2], s[3])), "auto")

        self.busy = False
        self.worker = None
        self.msg_queue = queue.Queue()
        self.model_key = "balanced"
        self.page = "home"
        self.overlay = None
        self.notice = None
        self.zone_frame = None
        self.zone_size = None
        self.zone_hl = False
        self._zone_cache = {}
        self._zone_job = None
        self._mode_seen = ctk.get_appearance_mode()

        # kuyruk (birden fazla dosya)
        self.jobs, self.qrows, self.qpage = [], {}, None
        self.next_id, self.run_id = 0, 0
        self.qworker, self.queue_running = None, False
        self.done_order, self.auto_jumped = [], False
        self.view, self.queue_mode = None, False                 # sonuç ekranında gösterilen dosya
        self.banner, self.nav_prev = None, None
        self._icon_cache, self._spin_cache = {}, {}
        self._spin_job, self._spin_k = None, 0
        self.update_tag, self.update_bar = None, None            # GitHub'da daha yeni sürüm var mı

        self._build_header()
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40, pady=(0, 30))
        self.container.bind("<Configure>", lambda e: self._layout_zone())

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)
        self.dnd_bind("<<DropEnter>>", self._on_drag_enter)
        self.dnd_bind("<<DropLeave>>", self._on_drag_leave)
        self.bind_all("<Button-1>", self._global_click, add="+")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_home()
        self.after(100, self._poll_queue)
        if self.cfg.get("update_check", True):
            self.after(2500, lambda: UpdateChecker(self.msg_queue).start())
        self.after(300, self._set_icon)         # CTk kendi simgesini 200 ms sonra koyar, ondan sonra değiştiriyoruz
        if self.icon_key != DEFAULT_ICON:       # güncelleme kurulumu kısayolları sıfırlamış olabilir
            threading.Thread(target=sync_shortcut_icons, args=(self.icon_key,), daemon=True).start()

    def show_error(self, message):
        if self.error_dialog is not None:
            try:
                self.error_dialog.close()
            except Exception:
                pass
        self.error_dialog = ErrorDialog(self, message)

    def _cleanup_tmp(self):
        if self.tmp_dir:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
            self.tmp_dir = None

    def _on_close(self):
        for w in (self.worker, self.link_worker, self.qworker):
            if w is not None:
                w.cancel.set()
        self._cleanup_tmp()
        self.destroy()

    def _set_icon(self):
        ico = ICON_DIR / f"{self.icon_key}.ico"
        try:
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    # ------------------------------------------------------------ tema yardımcıları
    def pal(self, mode):
        return COLORS[self.color][2 if mode == "light" else 3]

    def T(self, key):
        """CTk için (açık, koyu) renk çifti."""
        return (self.pal("light")[key], self.pal("dark")[key])

    def TT(self, base, over, t):
        """base rengine over rengini t oranında karıştırır (açık, koyu çifti)."""
        return tuple(mix(self.pal(m)[base], self.pal(m)[over], t) for m in ("light", "dark"))

    def tone(self):
        """Düğme ve menü yazıları için: siyah yerine temanın vurgu renginin koyu (koyu temada açık) tonu."""
        return self.TT("accent", "ink", 0.55)

    def hexc(self, key):
        return self.pal(ctk.get_appearance_mode().lower())[key]

    def font(self, size, bold=False):
        return ctk.CTkFont(family=FONT, size=int(round(size)), weight="bold" if bold else "normal")

    def lg(self, px):
        """Gerçek piksel -> CTk mantıksal birimi."""
        try:
            return px / ctk.ScalingTracker.get_window_scaling(self)
        except Exception:
            return px

    # ------------------------------------------------------------ üst bar
    def _build_header(self):
        if getattr(self, "header", None):
            self.header.destroy()
        kw = {"before": self.container} if hasattr(self, "container") else {}
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=40, pady=(22, 12), **kw)

        pal_l, pal_d = self.pal("light"), self.pal("dark")
        mark = load_app_icon(self.icon_key, 128)
        logo = ctk.CTkImage(light_image=mark, dark_image=mark, size=(42, 42))
        brand = ctk.CTkFrame(self.header, fg_color="transparent")
        brand.pack(side="left")
        ctk.CTkLabel(brand, image=logo, text="").pack(side="left")
        names = ctk.CTkFrame(brand, fg_color="transparent")
        names.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(names, text=app_title(), text_color=self.T("ink"), font=self.font(21, True),
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(names, text=app_tagline(), text_color=self.T("muted"), font=self.font(11.5),
                     anchor="w").pack(fill="x")

        dot = ctk.CTkImage(light_image=render_dot(pal_l["accent"]), dark_image=render_dot(pal_d["accent"]),
                           size=(14, 14))
        self.theme_btn = ctk.CTkButton(
            self.header, text=tr("Tema"), image=dot, compound="left", width=96, height=36, corner_radius=18,
            fg_color=self.T("zone"), hover_color=self.T("line"), text_color=self.tone(),
            font=self.font(13, True), command=self._toggle_theme_menu)
        flag = ctk.CTkImage(light_image=render_flag(LANG), dark_image=render_flag(LANG), size=(24, 16))
        self.lang_btn = ctk.CTkButton(
            self.header, text=dict(LANGS)[LANG] + "  ▾", image=flag, compound="left",
            width=122, height=36, corner_radius=18, fg_color=self.T("zone"), hover_color=self.T("line"),
            text_color=self.tone(), font=self.font(13, True), command=self._toggle_lang_menu)
        self._show_header_buttons(True)

    def _show_header_buttons(self, visible):
        """Tema ve dil butonları yalnızca ana ekranda görünür (tema sağda, dil onun solunda)."""
        for b in (self.theme_btn, self.lang_btn):
            b.pack_forget()
        if visible:
            self.theme_btn.pack(side="right")
            self.lang_btn.pack(side="right", padx=(0, 10))

    def _toggle_lang_menu(self):
        if self.overlay and self.overlay[3] == "lang":
            self.close_overlay()
        else:
            self._open_lang_menu()

    def _open_lang_menu(self):
        pop = ctk.CTkFrame(self, fg_color=self.T("card"), border_width=1, border_color=self.T("line"),
                           corner_radius=16)
        options = LANGS
        for i, (code, name) in enumerate(options):
            on = code == LANG
            base = self.TT("card", "accent", 0.18) if on else "transparent"
            row = ctk.CTkFrame(pop, corner_radius=11, fg_color=base, cursor="hand2")
            row.pack(fill="x", padx=8, pady=(8 if i == 0 else 0, 8 if i == len(options) - 1 else 2))
            flag = ctk.CTkImage(light_image=render_flag(code), dark_image=render_flag(code), size=(24, 16))
            ctk.CTkLabel(row, image=flag, text="   " + name, compound="left", text_color=self.T("ink"),
                         font=self.font(14, on), anchor="w").pack(side="left", padx=(14, 30), pady=10)
            hover = self.T("zone")
            bind_tree(row, "<Enter>", lambda e, r=row, h=hover: r.configure(fg_color=h))
            row.bind("<Leave>", lambda e, r=row, b=base: Dropdown._leave(r, b, e), add="+")
            bind_tree(row, "<Button-1>", lambda e, c=code: self.after(10, lambda: self._set_lang(c)))
        pop.update_idletasks()
        w = self.lg(pop.winfo_reqwidth())
        btn_right = self.lg(self.lang_btn.winfo_rootx() - self.winfo_rootx()) + self.lg(self.lang_btn.winfo_width())
        pop.place(x=btn_right - w, y=68)
        pop.lift()
        self.set_overlay(pop, [self.lang_btn], "lang")

    def _set_lang(self, code):
        global LANG
        LANG = code
        self.cfg["ui_lang"] = code
        save_config(self.cfg)
        self.close_overlay()
        self.title(app_title())
        self._build_header()
        self.show_home()

    def _toggle_theme_menu(self):
        if self.overlay and self.overlay[3] == "theme":
            self.close_overlay()
        else:
            self._open_theme_menu()

    def _open_theme_menu(self):
        pop = ctk.CTkFrame(self, fg_color=self.T("card"), border_width=1, border_color=self.T("line"),
                           corner_radius=16)
        inner = ctk.CTkFrame(pop, fg_color="transparent")
        inner.pack(padx=14, pady=14)

        def heading(text):
            ctk.CTkLabel(inner, text=text, text_color=self.T("muted"), font=self.font(11, True),
                         anchor="w").pack(fill="x", pady=(0, 6))

        heading(tr("TEMA"))
        seg = ctk.CTkFrame(inner, fg_color=self.T("zone"), corner_radius=12)
        seg.pack(fill="x", pady=(0, 14))
        for i, (mode, label) in enumerate(THEME_MODES):
            on = mode == self.theme_mode
            b = ctk.CTkButton(seg, text=tr(label), width=80, height=30, corner_radius=9, font=self.font(12.5),
                              fg_color=self.T("card") if on else "transparent", hover_color=self.T("line"),
                              text_color=self.T("ink") if on else self.T("muted"),
                              command=lambda m=mode: self.after(10, lambda: self._set_mode(m)))
            b.grid(row=0, column=i, padx=3, pady=3, sticky="ew")
            seg.grid_columnconfigure(i, weight=1, uniform="seg")

        heading(tr("RENK"))
        grid = ctk.CTkFrame(inner, fg_color="transparent")
        grid.pack(fill="x")
        for i, (key, (label, dot_color, _, _)) in enumerate(COLORS.items()):
            on = key == self.color
            img = ctk.CTkImage(light_image=render_dot(dot_color), dark_image=render_dot(dot_color), size=(18, 18))
            b = ctk.CTkButton(grid, text=tr(label), image=img, compound="top", width=82, height=62, corner_radius=12,
                              fg_color=self.T("zone"), hover_color=self.T("line"), text_color=self.T("ink"),
                              font=self.font(12), border_width=2,
                              border_color=self.T("accent") if on else self.T("zone"),
                              command=lambda k=key: self.after(10, lambda: self._set_color(k)))
            b.grid(row=i // 4, column=i % 4, padx=3, pady=3)

        ctk.CTkLabel(inner, text=tr("SİMGE"), text_color=self.T("muted"), font=self.font(11, True),
                     anchor="w").pack(fill="x", pady=(14, 6))
        icons = ctk.CTkFrame(inner, fg_color="transparent")
        icons.pack(fill="x")
        for i, (key, label) in enumerate(APP_ICONS):
            on = key == self.icon_key
            img = ctk.CTkImage(light_image=load_app_icon(key, 96), dark_image=load_app_icon(key, 96), size=(32, 32))
            b = ctk.CTkButton(icons, text=tr(label), image=img, compound="top", width=82, height=66, corner_radius=12,
                              fg_color=self.T("zone"), hover_color=self.T("line"), text_color=self.T("ink"),
                              font=self.font(12), border_width=2,
                              border_color=self.T("accent") if on else self.T("zone"),
                              command=lambda k=key: self.after(10, lambda: self._set_app_icon(k)))
            b.grid(row=i // 4, column=i % 4, padx=3, pady=3)
        pop.update_idletasks()
        x = self.lg(self.winfo_width()) - 40 - self.lg(pop.winfo_reqwidth())
        pop.place(x=x, y=68)
        pop.lift()
        self.set_overlay(pop, [self.theme_btn], "theme")

    def _set_mode(self, mode):
        self.theme_mode = mode
        self.cfg["theme"] = mode
        save_config(self.cfg)
        ctk.set_appearance_mode(mode)
        self.close_overlay()
        self.after(30, self._open_theme_menu)

    def _set_color(self, key):
        self.color = key
        self.cfg["color"] = key
        save_config(self.cfg)
        self.close_overlay()
        self.configure(fg_color=self.T("bg"))
        self._zone_cache.clear()
        self._build_header()
        self.show_home()
        self.after(60, self._open_theme_menu)

    def _set_app_icon(self, key):
        self.icon_key = key
        self.cfg["icon"] = key
        save_config(self.cfg)
        self.close_overlay()
        self._set_icon()
        self._build_header()
        threading.Thread(target=sync_shortcut_icons, args=(key,), daemon=True).start()
        self.after(60, self._open_theme_menu)

    # ------------------------------------------------------------ açılır pencereler / bildirimler
    def set_overlay(self, frame, owners, tag, on_close=None):
        self.close_overlay()
        self.overlay = (frame, owners, on_close, tag)

    def close_overlay(self):
        if not self.overlay:
            return
        frame, _, on_close, _ = self.overlay
        self.overlay = None
        try:
            frame.destroy()
        except Exception:
            pass
        if on_close:
            on_close()

    def _global_click(self, event):
        if not self.overlay:
            return
        w = str(event.widget)
        for owner in [self.overlay[0], *self.overlay[1]]:
            o = str(owner)
            if w == o or w.startswith(o + "."):
                return
        self.close_overlay()

    def notify(self, title, text="", warn=True, ms=4500):
        if self.notice is not None:
            try:
                self.notice.destroy()
            except Exception:
                pass
        if warn:
            f = ctk.CTkFrame(self, fg_color=self.T("card"), border_width=2, border_color=self.T("accent"),
                             corner_radius=16)
            ctk.CTkLabel(f, text="!", width=26, height=26, corner_radius=13, fg_color=self.T("accent"),
                         text_color=self.T("on_accent"), font=self.font(14, True)).pack(
                side="left", padx=(16, 12), pady=14, anchor="n")
            body = ctk.CTkFrame(f, fg_color="transparent")
            body.pack(side="left", padx=(0, 18), pady=12)
            ctk.CTkLabel(body, text=title, text_color=self.T("ink"), font=self.font(14, True), anchor="w").pack(fill="x")
            if text:
                ctk.CTkLabel(body, text=text, text_color=self.T("muted"), font=self.font(12.5), anchor="w",
                             justify="left", wraplength=360).pack(fill="x")
        else:
            f = ctk.CTkFrame(self, fg_color=self.T("zone"), border_width=2, border_color=self.T("accent"),
                             corner_radius=18)
            ctk.CTkLabel(f, text=title, text_color=self.T("ink"), fg_color="transparent",
                         font=self.font(14, True)).pack(padx=28, pady=14)
        if warn:
            f.place(relx=0.5, y=84, anchor="n")
        else:                                     # başarı bildirimi: üst çubuğun sağında, içerikten uzakta
            f.place(relx=1.0, x=-40, y=24, anchor="ne")
        f.lift()
        self.notice = f

        def _gone(frame=f):
            try:
                frame.destroy()
            except Exception:
                pass
            if self.notice is frame:
                self.notice = None

        self.after(ms, _gone)

    # ------------------------------------------------------------ ortak bileşenler
    def _goto(self, page):
        self.close_overlay()
        self.page = page
        for child in self.container.winfo_children():
            if child is self.qpage:                    # kuyruk ekranı yeniden kurulmasın diye saklanır
                child.pack_forget()
            else:
                child.destroy()
        self.zone_frame = None
        self.stack = None
        self.update_bar = None
        self._show_header_buttons(page == "home")

    def _label(self, parent, text, size=14, bold=False, color="ink", **kw):
        return ctk.CTkLabel(parent, text=text, text_color=self.T(color), font=self.font(size, bold), **kw)

    def bw(self, text, base, size=13):
        """Düğme genişliği: en az base, uzun metinlerde yazıya göre büyür."""
        return max(base, int(len(text) * size * 0.64) + 38)

    def dd_w(self, base):
        return base + 40 if LANG in ("de", "it") else base

    def _primary_button(self, parent, text, command, width=220):
        return ctk.CTkButton(parent, text=text, command=command, width=self.bw(text, width, 15), height=48,
                             corner_radius=24,
                             fg_color=self.T("accent"), hover_color=self.TT("accent", "ink", 0.12),
                             text_color=self.T("on_accent"), text_color_disabled=self.T("on_accent"),
                             font=self.font(15, True))

    def _soft_button(self, parent, text, command, width=120, height=38):
        return ctk.CTkButton(parent, text=text, command=command, width=self.bw(text, width), height=height,
                             corner_radius=height // 2, fg_color=self.T("zone"), hover_color=self.T("line"),
                             text_color=self.tone(), font=self.font(13, True))

    # ------------------------------------------------------------ 1) giriş ekranı
    def show_home(self):
        self._goto("home")
        self.zone_size = None
        stack = ctk.CTkFrame(self.container, fg_color="transparent", width=620, height=500)
        stack.pack_propagate(False)
        stack.place(relx=0.5, rely=0.5, anchor="center")
        self.stack = stack

        # bağlantı alanı
        link_row = ctk.CTkFrame(stack, fg_color="transparent")
        link_row.pack(fill="x")
        self.link_entry = ctk.CTkEntry(
            link_row, height=48, corner_radius=24, border_width=2, fg_color=self.T("card"),
            border_color=self.T("line"), text_color=self.T("ink"), font=self.font(14),
            placeholder_text=tr("Ses veya video dosyasının bağlantısını yapıştırın"),
            placeholder_text_color=self.T("muted"))
        self.link_entry.pack(side="left", fill="x", expand=True)
        self.link_entry.bind("<Return>", lambda e: self._start_link())
        self.link_entry.bind("<FocusIn>", lambda e: self.link_entry.configure(border_color=self.T("accent")))
        self.link_entry.bind("<FocusOut>", lambda e: self.link_entry.configure(border_color=self.T("line")))
        ctk.CTkButton(link_row, text=tr("Yükle"), width=96, height=48, corner_radius=24, fg_color=self.T("accent"),
                      hover_color=self.TT("accent", "ink", 0.12), text_color=self.T("on_accent"),
                      font=self.font(14, True), command=self._start_link).pack(side="left", padx=(10, 0))

        # "veya" ayracı
        sep = ctk.CTkFrame(stack, fg_color="transparent")
        sep.pack(fill="x", pady=(14, 14))
        sep.grid_columnconfigure((0, 2), weight=1)
        rule = self.TT("line", "dash", 0.8)
        ctk.CTkFrame(sep, height=3, corner_radius=0, fg_color=rule).grid(row=0, column=0, sticky="ew")
        self._label(sep, tr("veya"), 13, color="muted", height=20).grid(row=0, column=1, padx=14)
        ctk.CTkFrame(sep, height=3, corner_radius=0, fg_color=rule).grid(row=0, column=2, sticky="ew")

        zf = ctk.CTkFrame(stack, fg_color="transparent", width=600, height=380)
        zf.pack()
        self.zone_frame = zf
        self.zone_label = ctk.CTkLabel(zf, text="", fg_color="transparent", cursor="hand2")
        self.zone_label.place(x=0, y=0, relwidth=1, relheight=1)

        zc = self.T("zone")
        title = ctk.CTkLabel(zf, text=tr("Dosyaları buraya sürükleyebilirsiniz"), text_color=self.T("ink"),
                             fg_color=zc, bg_color=zc, font=self.font(23, True), cursor="hand2")
        sub = ctk.CTkLabel(zf, text=tr("ya da buraya tıklayıp bir veya birden fazla dosya seçebilirsiniz"), text_color=self.T("muted"),
                           fg_color=zc, bg_color=zc, font=self.font(14.5), cursor="hand2")
        fmts = ctk.CTkLabel(zf, text=tr("MP3 · WAV · M4A · MP4 · MKV · MOV ve daha fazlası"), text_color=self.T("muted"),
                            fg_color=zc, bg_color=zc, font=self.font(12), cursor="hand2")
        title.place(relx=0.5, rely=0.62, anchor="center")
        sub.place(relx=0.5, rely=0.72, anchor="center")
        fmts.place(relx=0.5, rely=0.85, anchor="center")
        for w in (zf, self.zone_label, title, sub, fmts):
            w.bind("<Button-1>", lambda e: self._browse())
        self._build_update_bar()
        self.after(30, self._layout_zone)

    def _update_visible(self):
        return bool(self.update_tag) and self.cfg.get("skip_version") != self.update_tag

    def _build_update_bar(self):
        """Ana ekranın altında "Yeni sürüm var" şeridi (yalnızca daha yeni bir sürüm varsa)."""
        self.update_bar = None
        if self.page != "home" or not self._update_visible():
            return
        bar = ctk.CTkFrame(self.container, fg_color=self.TT("card", "accent", 0.12), border_width=2,
                           border_color=self.TT("line", "accent", 0.5), corner_radius=22)
        ctk.CTkLabel(bar, text=tr("Yeni sürüm var: {v}", v=self.update_tag), text_color=self.T("ink"),
                     font=self.font(13.5, True)).pack(side="left", padx=(22, 14), pady=10)
        ctk.CTkButton(bar, text=tr("İndir"), width=88, height=34, corner_radius=17, fg_color=self.T("accent"),
                      hover_color=self.TT("accent", "ink", 0.12), text_color=self.T("on_accent"),
                      font=self.font(13, True), command=lambda: webbrowser.open(UPDATE_URL)).pack(
            side="left", pady=10)
        ctk.CTkButton(bar, text="✕", width=32, height=32, corner_radius=16, fg_color="transparent",
                      hover_color=self.T("zone"), text_color=self.T("muted"), font=self.font(14),
                      command=self._skip_update).pack(side="left", padx=(6, 12), pady=10)
        bar.place(relx=0.5, rely=1.0, anchor="s")
        self.update_bar = bar

    def _offer_update(self, tag):
        self.update_tag = tag
        if self.page == "home" and self.update_bar is None and self._update_visible():
            self._build_update_bar()
            self.zone_size = None
            self._layout_zone()

    def _skip_update(self):
        self.cfg["skip_version"] = self.update_tag
        save_config(self.cfg)
        if self.update_bar is not None:
            self.update_bar.destroy()
            self.update_bar = None
        self.zone_size = None
        self._layout_zone()

    def _layout_zone(self):
        if self.page != "home" or self.zone_frame is None or not self.zone_frame.winfo_exists():
            return
        cw = self.lg(self.container.winfo_width())
        reserve = 64 if self.update_bar is not None else 0          # şerit varsa alanı küçült
        ch = self.lg(self.container.winfo_height()) - reserve
        if cw < 100 or ch < 100:
            return
        above = 48 + 14 + 20 + 14 + 4              # bağlantı alanı + "veya" satırı + boşluklar (+ pay)
        w = int(max(340, min(620, cw - 8)))
        h = int(w / 1.55)
        if h > ch - above - 8:
            h = int(max(200, ch - above - 8))
            w = int(h * 1.55)
        if self.zone_size == (w, h):
            return
        self.zone_size = (w, h)
        self.stack.configure(width=w, height=above + h)
        self.stack.place(relx=0.5, rely=0.5, y=-reserve // 2, anchor="center")
        self.zone_frame.configure(width=w, height=h)
        if self._zone_job:
            self.after_cancel(self._zone_job)
        self._zone_job = self.after(60, self._render_zone)

    def _render_zone(self):
        self._zone_job = None
        if self.page != "home" or self.zone_frame is None or not self.zone_frame.winfo_exists() or not self.zone_size:
            return
        w, h = self.zone_size
        key = (w, h, self.color, self.zone_hl)
        if len(self._zone_cache) > 10:
            self._zone_cache.clear()
        if key not in self._zone_cache:
            self._zone_cache[key] = ctk.CTkImage(
                light_image=render_zone(w, h, self.pal("light"), self.zone_hl),
                dark_image=render_zone(w, h, self.pal("dark"), self.zone_hl), size=(w, h))
        self.zone_label.configure(image=self._zone_cache[key])

    def _set_zone_highlight(self, on):
        if self.page == "home" and self.zone_hl != on:
            self.zone_hl = on
            self._render_zone()

    def _browse(self):
        if self.busy:
            return
        paths = filedialog.askopenfilenames(title=tr("Ses veya video dosyası seç"), filetypes=media_types())
        if paths:
            self.add_files(list(paths))

    def _on_drag_enter(self, event):
        self._set_zone_highlight(True)
        return event.action

    def _on_drag_leave(self, event):
        self._set_zone_highlight(False)
        return event.action

    def _on_drop(self, event):
        self._set_zone_highlight(False)
        self._handle_drop(self.tk.splitlist(event.data))
        return event.action

    def _handle_drop(self, paths):
        if self.busy or self.page not in ("home", "queue"):
            return
        if paths:
            self.add_files([str(p) for p in paths])

    def _load_file(self, path):
        if not os.path.isfile(path):
            self.show_error(tr("Bu dosya açılamadı.\n\nDosyanın yerinde olduğundan ve başka bir program tarafından "
                               "kullanılmadığından emin olun."))
            return
        self.file_path = path
        self.display_name = None
        self.file_duration = media_duration(path)
        self.show_options()

    def _start_link(self):
        if self.busy:
            return
        url = self.link_entry.get().strip()
        if not url:
            self.notify(tr("Bağlantı girilmedi"), tr("Lütfen bir ses veya video dosyasının bağlantısını yapıştırın."))
            return
        if not re.match(r"^https?://\S+$", url, re.IGNORECASE):
            self.notify(tr("Geçersiz bağlantı"), tr("Bağlantı http:// veya https:// ile başlamalıdır."))
            return
        self.close_overlay()
        self._cleanup_tmp()
        self.tmp_dir = tempfile.mkdtemp(prefix="sesten_")
        self.busy = True
        self.t_start = None
        host = urllib.parse.urlparse(url).netloc or url
        self._build_progress_page(host, tr("Bağlantı kontrol ediliyor…"), self._cancel_link)
        self.link_worker = LinkWorker(url, self.tmp_dir, self.msg_queue)
        self.link_worker.start()

    def _cancel_link(self):
        if self.link_worker:
            self.link_worker.cancel.set()
            self.status_label.configure(text=tr("İptal ediliyor…"))

    # ------------------------------------------------------------ 2) seçenekler
    def est_seconds(self, key, duration=-1):
        if duration == -1:                         # verilmediyse seçenekler ekranındaki dosya
            duration = self.file_duration
        if not duration:
            return None
        ratio = self.cfg.get("ratios", {}).get(key, MODELS[key][3])
        return duration * ratio + 8

    def resolved_model(self, speed=None, duration=-1):
        speed = speed or self.speed
        if duration == -1:
            duration = self.file_duration
        if speed != "auto":
            return speed
        if not duration:
            return "balanced"
        for key in ("best", "balanced"):          # tahmini süresi 15 dk'yı geçmeyen en doğru model
            if self.est_seconds(key, duration) <= 900:
                return key
        return "fast"

    def speed_items(self, duration=-1):
        if duration == -1:
            duration = self.file_duration
        items = []
        for key, name, desc in SPEEDS:
            right = ""
            if key != "auto" and duration:
                right = fmt_estimate(self.est_seconds(key, duration))
            items.append(dict(key=key, name=tr(name), desc=tr(desc), right=right))
        return items

    def show_options(self):
        self._goto("options")
        page = self.container

        card = ctk.CTkFrame(page, fg_color=self.T("card"), border_width=1, border_color=self.T("line"),
                            corner_radius=18)
        card.pack(fill="x", pady=(8, 20))
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=22, pady=16)
        name = self.display_name or Path(self.file_path).name
        self._label(left, name if len(name) < 60 else name[:57] + "…", 16, True, anchor="w").pack(fill="x")
        dur = fmt_duration(self.file_duration) if self.file_duration else tr("süre okunamadı")
        self._label(left, tr("Süre: {dur}", dur=dur), 13, color="muted", anchor="w").pack(fill="x", pady=(2, 0))
        self._soft_button(card, tr("Değiştir"), self.show_home, width=100).pack(side="right", padx=18)

        row = ctk.CTkFrame(page, fg_color="transparent")
        row.pack(pady=(0, 14))
        self._label(row, tr("Çevirme Hızı"), 14, True).pack(side="left", padx=(0, 18))
        self.speed_dd = Dropdown(
            self, row, self.dd_w(300), self.speed_items, lambda: self.speed, self._on_speed)
        self.speed_dd.btn.pack(side="left")

        self.est_card = ctk.CTkFrame(page, fg_color=self.T("card"), border_width=1, border_color=self.T("line"),
                                     corner_radius=18, width=440, height=142)
        self.est_card.pack_propagate(False)
        self.est_card.pack(pady=(0, 6))
        self._label(self.est_card, tr("Tahmini süre"), 12.5, color="muted").pack(pady=(14, 0))
        self.est_big = self._label(self.est_card, "", 30, True)
        self.est_big.pack(pady=(2, 0))
        self.est_note = self._label(self.est_card, "", 12.5, color="muted")
        self.est_note.pack()
        self.est_note2 = self._label(self.est_card, "", 12, color="muted")
        self.est_note2.pack()
        self._refresh_est()

        lang = ctk.CTkFrame(page, fg_color="transparent")
        lang.pack(fill="x", pady=(18, 0))
        self._label(lang, tr("Konuşma dili"), 14, True).pack(side="left")
        menu = ctk.CTkOptionMenu(
            lang, values=[spoken_label(s[0]) for s in SPOKEN], width=200, height=38, corner_radius=19, font=self.font(13, True),
            dropdown_font=self.font(13), fg_color=self.T("zone"), button_color=self.T("zone"),
            button_hover_color=self.T("line"), text_color=self.tone(), dropdown_fg_color=self.T("card"),
            dropdown_text_color=self.tone(), dropdown_hover_color=self.T("zone"), command=self._on_language)
        menu.set(spoken_label(self.spoken))
        menu.pack(side="right")

        self._primary_button(page, tr("Transkripti başlat"), self.start_transcription, width=270).pack(
            side="bottom", pady=(0, 4))

    def _on_speed(self, key):
        self.speed = key
        self.cfg["speed"] = key
        save_config(self.cfg)
        self._refresh_est()

    def _refresh_est(self):
        key = self.resolved_model()
        est = self.est_seconds(key)
        self.est_big.configure(text=fmt_estimate(est) if est else "—")
        title, model_name, _, _, size = MODELS[key]
        self.est_note.configure(text=tr("Otomatik: {title} seçildi", title=tr(title)) if self.speed == "auto"
                                else tr(title))
        self.est_note2.configure(
            text="" if model_cached(model_name) else tr(
                "İlk kullanımda ek dosyalar indirilir (yaklaşık {size}, internet gerekir)", size=tr(size)))

    def _on_language(self, value):
        self.spoken = next((s[0] for s in SPOKEN if spoken_label(s[0]) == value), "auto")
        self.cfg["spoken"] = self.spoken
        save_config(self.cfg)

    # ------------------------------------------------------------ 3) ilerleme
    def start_transcription(self):
        self.busy = True
        self.model_key = self.resolved_model()
        self.progress_value = 0.0
        self.total_seconds = None
        self.t_start = None
        self.estimate_total = self.est_seconds(self.model_key)
        self._build_progress_page(self.display_name or Path(self.file_path).name, tr("Hazırlanıyor…"),
                                  self.cancel_transcription)
        self.worker = Worker(self.file_path, self.model_key, spoken_code(self.spoken), self.msg_queue)
        self.worker.start()

    def _build_progress_page(self, name, status, on_cancel):
        self._goto("progress")
        box = ctk.CTkFrame(self.container, fg_color="transparent")
        box.place(relx=0.5, rely=0.46, anchor="center")
        self._label(box, name if len(name) < 50 else name[:47] + "…", 14, color="muted").pack()
        self.percent_label = self._label(box, "—", 66, True)
        self.percent_label.pack(pady=(10, 14))
        self.progress_bar = ctk.CTkProgressBar(box, width=480, height=12, corner_radius=6,
                                               fg_color=self.T("zone"), progress_color=self.T("accent"),
                                               mode="indeterminate")
        self.progress_bar.pack()
        self.progress_bar.start()
        self.status_label = self._label(box, status, 15, color="muted", wraplength=520, justify="center")
        self.status_label.pack(pady=(16, 26))
        self._soft_button(box, tr("İptal"), on_cancel, width=110).pack()

    def cancel_transcription(self):
        if self.worker:
            self.worker.cancel.set()
            self.status_label.configure(text=tr("İptal ediliyor…"))

    def _poll_queue(self):
        try:
            while True:
                self._handle(self.msg_queue.get_nowait())
        except queue.Empty:
            pass
        if self.busy and self.t_start:
            self._update_eta()
        if self.queue_running:
            self._tick_queue()
        mode = ctk.get_appearance_mode()
        if mode != self._mode_seen:
            self._mode_seen = mode
            self._style_text_tags()
        self.after(150, self._poll_queue)

    def _handle(self, msg):
        kind = msg[0]
        if kind.startswith("q_"):
            self._handle_queue(msg)
        elif kind == "upd_found":
            self._offer_update(msg[1])
        elif kind == "loading":
            self.status_label.configure(
                text=tr("İlk kullanım için gerekli dosyalar indiriliyor…\nBu işlem yalnızca bir kez yapılır ve internet "
                        "bağlantısı gerekir.") if msg[1] else tr("Dönüştürme işlemi hazırlanıyor…"))
        elif kind == "started":
            self.total_seconds = msg[1]
            self.t_start = time.time()
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            self.percent_label.configure(text="0%")
        elif kind == "progress":
            self.progress_value = msg[1]
            self.progress_bar.set(self.progress_value)
            self.percent_label.configure(text=f"{int(self.progress_value * 100)}%")
        elif kind == "done":
            _, segments, elapsed, total = msg
            self.busy = False
            self._remember_speed(self.model_key, elapsed, total)
            job = Job(self.file_path, self.file_duration, "audio", self.speed, self.spoken)
            job.name = self.display_name or Path(self.file_path).name
            job.status, job.segments, job.elapsed = "done", segments, elapsed
            self.view, self.queue_mode = job, False
            self.show_result()
        elif kind == "dl_progress":
            self.status_label.configure(text=tr("Dosya indiriliyor…"))
            if msg[1] is not None:
                if self.progress_bar.cget("mode") != "determinate":
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(msg[1])
                self.percent_label.configure(text=f"{int(msg[1] * 100)}%")
        elif kind == "dl_done":
            self.busy = False
            self.file_path, self.display_name = msg[1], msg[2]
            self.file_duration = media_duration(msg[1])
            self.show_options()
        elif kind == "dl_cancelled":
            self.busy = False
            self._cleanup_tmp()
            self.show_home()
        elif kind == "dl_error":
            self.busy = False
            self._cleanup_tmp()
            self.show_home()
            self.show_error(msg[1])
        elif kind == "cancelled":
            self.busy = False
            self.show_options()
        elif kind == "error":
            self.busy = False
            self.show_options()
            self.show_error(tr("Transkript çıkarılamadı.\n\n{err}", err=msg[1]))

    def _update_eta(self):
        elapsed = time.time() - self.t_start
        p = self.progress_value
        if p >= 0.03 and elapsed >= 4:
            remaining = elapsed * (1 - p) / p
        elif self.estimate_total:
            remaining = max(self.estimate_total - elapsed - 8, 0)
        else:
            self.status_label.configure(text=tr("Hesaplanıyor…"))
            return
        self.status_label.configure(text=tr("Tahmini kalan süre: {t}", t=fmt_duration(remaining)))

    def _remember_speed(self, key, elapsed, total):
        if total >= 20:
            ratios = self.cfg.setdefault("ratios", {})
            old = ratios.get(key)
            new = elapsed / total
            ratios[key] = new if old is None else round(0.5 * old + 0.5 * new, 4)
            save_config(self.cfg)

    # ------------------------------------------------------------ 3b) kuyruk
    def _new_job(self, path):
        dur, kind, err = probe_media(path)
        job = Job(path, dur, kind, self.speed, self.spoken, tr(err) if err else None)
        self.next_id += 1
        job.id = self.next_id
        return job

    def file_icon(self, kind, size=46):
        key = (kind, size, self.color)
        if key not in self._icon_cache:
            self._icon_cache[key] = ctk.CTkImage(
                light_image=render_file_icon(kind, self.pal("light"), size),
                dark_image=render_file_icon(kind, self.pal("dark"), size), size=(size, size))
        return self._icon_cache[key]

    def ring_frames(self, done=False):
        key = (self.color, done)
        if key not in self._spin_cache:
            light, dark = self.pal("light")["accent"], self.pal("dark")["accent"]
            self._spin_cache[key] = [
                ctk.CTkImage(light_image=render_ring(light, k), dark_image=render_ring(dark, k), size=(24, 24))
                for k in ([None] if done else range(12))]
        return self._spin_cache[key]

    def model_for(self, job):
        return self.resolved_model(job.speed, job.duration)

    def add_files(self, paths):
        """Seçilen ya da sürüklenen dosyaları ekler. Kuyruk boşken tek dosya seçenekler ekranına, gerisi kuyruğa gider."""
        files = [p for p in paths if os.path.isfile(p)]
        if not files:
            if any(os.path.isdir(p) for p in paths):
                self.notify(tr("Klasör seçildi"), tr("Lütfen klasör yerine ses veya video dosyaları seçin."))
            else:
                self.show_error(tr("Bu dosya açılamadı.\n\nDosyanın yerinde olduğundan ve başka bir program "
                                   "tarafından kullanılmadığından emin olun."))
            return
        known = {os.path.normcase(os.path.abspath(j.path)) for j in self.jobs}
        fresh = []
        for p in files:
            key = os.path.normcase(os.path.abspath(p))
            if key not in known:
                known.add(key)
                fresh.append(p)
        if not fresh:
            self.notify(tr("Zaten kuyrukta"), tr("Seçtiğiniz dosyalar listede var."))
            return
        if not self.jobs and len(fresh) == 1:
            self._load_file(fresh[0])
            return
        room = MAX_JOBS - len(self.jobs)
        if room <= 0:
            self.notify(tr("Kuyruk dolu"), tr("Kuyruğa en fazla {n} dosya eklenebilir.", n=MAX_JOBS))
            return
        self.jobs.extend(self._new_job(p) for p in fresh[:room])
        if self.page == "queue":
            self._sync_rows()
            self._refresh_queue_ui()
        else:
            self.show_queue()
        if len(fresh) > room:
            self.notify(tr("Kuyruk dolu"), tr("Kuyruğa en fazla {n} dosya eklenebilir.", n=MAX_JOBS))

    def show_queue(self):
        self._goto("queue")
        if self.qpage is None or not self.qpage.winfo_exists():
            self._build_queue_page()
        self.qpage.pack(fill="both", expand=True)
        self._sync_rows()
        for row in self.qrows.values():
            row.update()
        self._refresh_queue_ui()

    def _build_queue_page(self):
        T = self.T
        q = ctk.CTkFrame(self.container, fg_color="transparent")
        self.qpage = q
        self.q_fmt_shown = False

        # alt çubuklar önce paketlenir; liste kalan alanı doldurur
        bar = ctk.CTkFrame(q, fg_color="transparent")
        bar.pack(side="bottom", fill="x")
        bar.grid_columnconfigure(1, weight=1)
        self.q_clear = self._soft_button(bar, tr("Listeyi temizle"), self._clear_list, width=140, height=42)
        self.q_clear.grid(row=0, column=0)
        tot = ctk.CTkFrame(bar, fg_color="transparent")
        tot.grid(row=0, column=2, padx=(0, 18))
        self.q_tot_lbl = self._label(tot, "", 12, color="muted", anchor="e")
        self.q_tot_lbl.pack(fill="x")
        self.q_tot_val = self._label(tot, "—", 17, True, anchor="e")
        self.q_tot_val.pack(fill="x")
        self.q_stop = self._soft_button(bar, tr("Kuyruğu durdur"), self._stop_queue, width=150, height=46)
        self.q_stop.grid(row=0, column=3, padx=(0, 10))
        self.q_stop.grid_remove()
        self.q_go = self._primary_button(bar, "", self._start_queue, width=270)
        self.q_go.grid(row=0, column=4)

        st = ctk.CTkFrame(q, fg_color="transparent")
        st.pack(side="bottom", fill="x", pady=(6, 14))
        self._label(st, tr("Hepsine uygula"), 13, True, color="muted").pack(side="left", padx=(2, 12))
        self.g_speed = Chip(self, st, tr("Hız"), big=True)
        self.g_speed.frame.pack(side="left", padx=(0, 8))
        self.g_lang = Chip(self, st, tr("Dil"), big=True)
        self.g_lang.frame.pack(side="left")
        self.g_speed.on_click = lambda c: self.pick_global_speed(c.frame)
        self.g_lang.on_click = lambda c: self.pick_global_spoken(c.frame)
        self.q_fmt = ctk.CTkFrame(st, fg_color="transparent")          # ilk transkript hazır olunca görünür
        self._label(self.q_fmt, tr("İndirme biçimi"), 13, True, color="muted").pack(side="left", padx=(0, 12))
        self.q_fmt_dd = Dropdown(self, self.q_fmt, self.dd_w(240), self.format_items, lambda: self.fmt, self._on_format, up=True)
        self.q_fmt_dd.btn.pack(side="left")

        head = ctk.CTkFrame(q, fg_color="transparent")
        head.pack(fill="x", pady=(2, 10))
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        self._label(titles, tr("Dönüştürme kuyruğu"), 22, True, anchor="w").pack(fill="x")
        self.q_sub = self._label(titles, "", 13, color="muted", anchor="w")
        self.q_sub.pack(fill="x")
        self._soft_button(head, tr("+ Dosya ekle"), self._browse, width=120, height=38).pack(side="right")
        self.q_all_var = ctk.BooleanVar(value=True)
        self.q_all = ctk.CTkCheckBox(
            head, text=tr("Tümünü seç"), variable=self.q_all_var, command=self._toggle_all, width=20,
            checkbox_width=22, checkbox_height=22, corner_radius=7, border_width=2, fg_color=T("accent"),
            hover_color=self.TT("accent", "ink", 0.12), checkmark_color=T("on_accent"), border_color=T("dash"),
            text_color=T("ink"), text_color_disabled=T("muted"), font=self.font(13.5, True))
        self.q_all.pack(side="right", padx=(0, 18))

        self.q_list = ctk.CTkScrollableFrame(
            q, fg_color="transparent", corner_radius=0, scrollbar_button_color=T("line"),
            scrollbar_button_hover_color=T("dash"))
        self.q_list.pack(fill="both", expand=True)

        self.q_overall = ctk.CTkFrame(q, fg_color=self.TT("card", "accent", 0.10), border_width=2,
                                      border_color=self.TT("line", "accent", 0.5), corner_radius=16)
        self.q_ov_shown = False
        ov_text = ctk.CTkFrame(self.q_overall, fg_color="transparent")
        ov_text.pack(side="left", padx=(20, 10), pady=12)
        self.q_ov_title = self._label(ov_text, "", 14, True, anchor="w", height=22)
        self.q_ov_title.pack(fill="x")
        self.q_ov_sub = self._label(ov_text, "", 12.5, color="muted", anchor="w", height=18)
        self.q_ov_sub.pack(fill="x")
        self.q_ov_bar = ctk.CTkProgressBar(self.q_overall, width=260, height=10, corner_radius=5,
                                           fg_color=T("zone"), progress_color=T("accent"))
        self.q_ov_bar.pack(side="right", padx=22)
        self.q_ov_bar.set(0)

    def _sync_rows(self):
        ids = {j.id for j in self.jobs}
        for jid in [i for i in self.qrows if i not in ids]:
            self.qrows.pop(jid).destroy()
        for j in self.jobs:
            if j.id not in self.qrows:
                self.qrows[j.id] = QRow(self, self.q_list, j)

    def _update_all_rows(self):
        if self.page == "queue":
            for row in self.qrows.values():
                row.update()

    def _remaining_seconds(self, jobs):
        total = 0.0
        for j in jobs:
            if j.status in ("done", "error"):
                continue
            est = self.est_seconds(j.model_key or self.model_for(j), j.duration)
            if est:
                total += est * (1 - (j.pct if j.status == "running" else 0))
        return total

    def _refresh_queue_ui(self):
        if self.page != "queue" or self.qpage is None:
            return
        jobs = self.jobs
        ready = [j for j in jobs if j.status == "ready"]
        picked = [j for j in ready if j.checked]
        run = [j for j in jobs if j.sel]
        running = self.queue_running
        status = tr("{m} dönüştürülüyor", m=len(run)) if running else tr("{m} seçili", m=len(picked))
        self.q_sub.configure(text=f"{fcount(len(jobs))} · {status}")
        self.q_all_var.set(bool(ready) and all(j.checked for j in ready))
        self.q_all.configure(state="normal" if ready and not running else "disabled")
        can = bool(picked) and not running
        go_text = tr("Dönüştürülüyor…") if running else tr("Seçilenleri dönüştür ({n})", n=len(picked))
        self.q_go.configure(
            text=go_text, width=self.bw(go_text, 270, 15),
            state="normal" if can else "disabled", fg_color=self.T("accent") if can else self.T("line"),
            text_color=self.T("on_accent"), text_color_disabled=self.T("muted"))
        if running:
            self.q_stop.grid()
        else:
            self.q_stop.grid_remove()
        self.q_clear.configure(state="disabled" if running else "normal")
        self.g_speed.set(tr(SPEED_NAMES[self.speed]))
        self.g_lang.set(spoken_short(self.spoken))
        show_fmt = any(j.status == "done" for j in jobs)
        if show_fmt != self.q_fmt_shown:
            self.q_fmt_shown = show_fmt
            if show_fmt:
                self.q_fmt.pack(side="right")
            else:
                self.q_fmt.pack_forget()
        self._refresh_totals()

    def _refresh_totals(self):
        if self.page != "queue" or self.qpage is None:
            return
        jobs = self.jobs
        picked = [j for j in jobs if j.status == "ready" and j.checked]
        run = [j for j in jobs if j.sel]
        left = self._remaining_seconds(run)
        if run:
            fin = [j for j in run if j.status in ("done", "error")]
            done = [j for j in run if j.status == "done"]
            if len(fin) == len(run):
                errs = len(run) - len(done)
                self.q_ov_title.configure(text=tr("Hepsi tamamlandı"))
                self.q_ov_sub.configure(text=tr("{n} transkript hazır · {e} hata", n=len(done), e=errs) if errs
                                        else tr("{n} transkript hazır", n=len(done)))
            else:
                self.q_ov_title.configure(text=tr("{done}/{tot} dosya tamamlandı", done=len(fin), tot=len(run)))
                self.q_ov_sub.configure(text=tr("Tahmini kalan süre {t}", t=fmt_estimate(left)) if left
                                        else tr("Hesaplanıyor…"))
            self.q_ov_bar.set(sum(1.0 if j.status in ("done", "error") else j.pct for j in run) / len(run))
            if not self.q_ov_shown:
                self.q_ov_shown = True
                self.q_overall.pack(fill="x", pady=(0, 10), before=self.q_list._parent_frame)   # listenin dış çerçevesi
        elif self.q_ov_shown:
            self.q_ov_shown = False
            self.q_overall.pack_forget()

        if self.queue_running:
            n = len([j for j in run if j.status not in ("done", "error")])
            lbl, val = tr("Tahmini kalan süre ({files})", files=fcount(n)), fmt_estimate(left) if left else "…"
        elif picked:
            total = sum(self.est_seconds(self.model_for(j), j.duration) or 0 for j in picked)
            lbl = tr("Tahmini toplam süre ({files})", files=fcount(len(picked)))
            val = fmt_estimate(total) if total else "—"
        elif run:
            lbl, val = "", tr("Tamamlandı")
        else:
            lbl, val = tr("Tahmini toplam süre"), "—"
        self.q_tot_lbl.configure(text=lbl)
        self.q_tot_val.configure(text=val)

    def _toggle_all(self):
        on = self.q_all_var.get()
        for j in self.jobs:
            if j.status == "ready":
                j.checked = on
        self._update_all_rows()
        self._refresh_queue_ui()

    def _remove_job(self, job):
        if job.status not in ("ready", "error") or job not in self.jobs:
            return
        self.jobs.remove(job)
        self._after_list_change()

    def _clear_list(self):
        if self.queue_running:
            return
        self.jobs[:] = [j for j in self.jobs if j.status not in ("ready", "error")]
        self._after_list_change()

    def _after_list_change(self):
        if not self.jobs:
            self._reset_queue()
            self.show_home()
        else:
            self._sync_rows()
            self._refresh_queue_ui()

    def _reset_queue(self):
        """Kuyruğu ve sonuçlarını tamamen siler (çalışan varsa durdurur)."""
        if self.qworker is not None:
            self.qworker.cancel.set()
            self.qworker = None
        self.run_id += 1                              # eski işçiden gelen mesajlar yok sayılır
        self.queue_running = False
        self.jobs, self.done_order, self.qrows = [], [], {}
        self.view, self.auto_jumped = None, False
        if self.qpage is not None:
            try:
                self.qpage.destroy()
            except Exception:
                pass
            self.qpage = None

    # ---- hız / dil seçicileri
    def open_menu(self, anchor, items, current, on_pick, min_width=230):
        """Bir düğmenin altında (sığmazsa üstünde) açılan seçim listesi. Uzun listeler kaydırılır."""
        tag = ("menu", str(anchor))
        if self.overlay and self.overlay[3] == tag:
            self.close_overlay()
            return
        pop = ctk.CTkFrame(self, fg_color=self.T("card"), border_width=1, border_color=self.T("line"), corner_radius=16)
        compact = not any(it.get("desc") for it in items)
        scroll = len(items) > 7
        host = pop
        if scroll:
            host = ctk.CTkScrollableFrame(pop, fg_color="transparent", corner_radius=0,
                                          scrollbar_button_color=self.T("line"),
                                          scrollbar_button_hover_color=self.T("dash"))
            host.pack(fill="both", expand=True, padx=(8, 2), pady=8)
        for i, it in enumerate(items):
            on = it["key"] == current
            base = self.TT("card", "accent", 0.18) if on else "transparent"
            row = ctk.CTkFrame(host, corner_radius=11, fg_color=base, cursor="hand2")
            if scroll:
                row.pack(fill="x", padx=(0, 6), pady=(0, 2))
            else:
                row.pack(fill="x", padx=8, pady=(8 if i == 0 else 0, 8 if i == len(items) - 1 else 2))
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=(12, 6), pady=6 if compact else 7)
            ctk.CTkLabel(left, text=it["name"], text_color=self.T("ink"), font=self.font(14 if not compact else 13.5, True),
                         anchor="w").pack(fill="x")
            if it.get("desc"):
                ctk.CTkLabel(left, text=it["desc"], text_color=self.T("muted"), font=self.font(11.5),
                             anchor="w").pack(fill="x")
            if it.get("right"):
                ctk.CTkLabel(row, text=it["right"], text_color=self.T("ink"), font=self.font(12.5, True)).pack(
                    side="right", padx=12)
            hover = self.T("zone")
            bind_tree(row, "<Enter>", lambda e, r=row, h=hover: r.configure(fg_color=h))
            row.bind("<Leave>", lambda e, r=row, b=base: Dropdown._leave(r, b, e), add="+")
            bind_tree(row, "<Button-1>", lambda e, k=it["key"]: self.after(10, lambda: self._menu_pick(on_pick, k)))
        pop.update_idletasks()
        w = max(min_width, self.lg(pop.winfo_reqwidth()))
        if scroll:
            ph = (8 if compact else 6) * (38 if compact else 56) + 16
        else:
            ph = self.lg(pop.winfo_reqheight())
        pop.pack_propagate(False)
        pop.configure(width=w, height=ph)
        bx = self.lg(anchor.winfo_rootx() - self.winfo_rootx())
        by = self.lg(anchor.winfo_rooty() - self.winfo_rooty())
        y = by + self.lg(anchor.winfo_height()) + 6
        if y + ph > self.lg(self.winfo_height()) - 8:
            y = max(8, by - ph - 6)
        pop.place(x=max(8, min(bx, self.lg(self.winfo_width()) - w - 12)), y=y)
        pop.lift()
        self.set_overlay(pop, [anchor], tag)

    def _menu_pick(self, on_pick, key):
        self.close_overlay()
        on_pick(key)

    def spoken_items(self):
        return [dict(key=s[0], name=spoken_label(s[0]), desc="") for s in SPOKEN]

    def pick_speed(self, job, anchor):
        if job.status == "ready":
            self.open_menu(anchor, self.speed_items(job.duration), job.speed, lambda k: self._set_job(job, speed=k))

    def pick_spoken(self, job, anchor):
        if job.status == "ready":
            self.open_menu(anchor, self.spoken_items(), job.spoken, lambda k: self._set_job(job, spoken=k))

    def _set_job(self, job, **kw):
        for name, value in kw.items():
            setattr(job, name, value)
        row = self.qrows.get(job.id)
        if row is not None:
            row.update()
        self._refresh_queue_ui()

    def pick_global_speed(self, anchor):
        self.open_menu(anchor, self.speed_items(None), self.speed, self._apply_global_speed)

    def pick_global_spoken(self, anchor):
        self.open_menu(anchor, self.spoken_items(), self.spoken, self._apply_global_spoken)

    def _apply_global_speed(self, key):
        self.speed = key
        self.cfg["speed"] = key
        save_config(self.cfg)
        for j in self.jobs:
            if j.status == "ready":
                j.speed = key
        self._update_all_rows()
        self._refresh_queue_ui()

    def _apply_global_spoken(self, key):
        self.spoken = key
        self.cfg["spoken"] = key
        save_config(self.cfg)
        for j in self.jobs:
            if j.status == "ready":
                j.spoken = key
        self._update_all_rows()
        self._refresh_queue_ui()

    # ---- çalıştırma
    def _start_queue(self):
        picked = [j for j in self.jobs if j.status == "ready" and j.checked]
        if not picked or self.queue_running:
            return
        self.close_overlay()
        self.run_id += 1
        for j in self.jobs:
            j.sel = False
        specs = []
        for j in picked:
            j.sel, j.status, j.pct, j.note, j.eta_text, j.t_start = True, "queued", 0.0, "", "", None
            j.model_key = self.model_for(j)
            specs.append(dict(id=j.id, path=j.path, model_key=j.model_key, language=spoken_code(j.spoken)))
        self.queue_running, self.auto_jumped = True, False
        self.qworker = QueueWorker(self.run_id, specs, self.msg_queue)
        self.qworker.start()
        self._update_all_rows()
        self._refresh_queue_ui()

    def _stop_queue(self):
        if not self.queue_running or self.qworker is None:
            return
        self.qworker.stop_after.set()
        for j in self.jobs:
            if j.status == "queued":
                j.status, j.sel = "ready", False
        self.notify(tr("Kuyruk durduruldu. Çalışan dosya tamamlanınca durur."), warn=False, ms=3600)
        self._update_all_rows()
        self._refresh_queue_ui()

    def _after_state_change(self):
        if self.page == "queue":
            self._update_all_rows()
            self._refresh_queue_ui()
        elif self.page == "result" and self.queue_mode:
            self._update_banner()
            self._update_nav()

    def _handle_queue(self, msg):
        kind = msg[0]
        if msg[1] != self.run_id:
            return
        if kind == "q_finished":
            self.queue_running, self.qworker = False, None
            self._after_state_change()
            return
        if kind == "q_failed":
            self.queue_running, self.qworker = False, None
            for j in self.jobs:
                if j.status == "running":
                    j.status, j.err_kind, j.checked = "error", "run", False
                    j.note = tr("Dönüştürülemedi") + ": " + short_name(msg[2], 70)
                elif j.status == "queued":
                    j.status, j.sel = "ready", False
            self._after_state_change()
            self.show_error(tr("Transkript çıkarılamadı.\n\n{err}", err=msg[2]))
            return
        job = next((j for j in self.jobs if j.id == msg[2]), None)
        if job is None:
            return
        if kind == "q_start":
            job.status, job.pct, job.t_start, job.eta_text = "running", 0.0, None, ""
            job.note = tr("Hazırlanıyor…")
            self._after_state_change()
        elif kind == "q_loading":
            job.note = (tr("Gerekli dosyalar indiriliyor…") if msg[3] else tr("Hazırlanıyor…"))
        elif kind == "q_began":
            job.t_start = time.time()
            job.duration = job.duration or msg[3]
        elif kind == "q_progress":
            job.pct = msg[3]
        elif kind == "q_done":
            _, _, _, segments, elapsed, total = msg
            job.status, job.pct, job.segments, job.elapsed = "done", 1.0, segments, elapsed
            self._remember_speed(job.model_key, elapsed, total)
            self.done_order.append(job)
            first, self.auto_jumped = not self.auto_jumped, True
            name = short_name(job.name, 30)
            if first and self.page == "queue":                  # ilk biten transkript kendiliğinden açılır
                more = any(j.status == "queued" for j in self.jobs)
                self.view_job(job)
                self.notify(tr("{name} tamamlandı · sıradaki dosya başladı", name=name) if more
                            else tr("{name} tamamlandı", name=name), warn=False, ms=3600)
            else:
                self.notify(tr("{name} tamamlandı", name=name), warn=False, ms=3000)
                self._after_state_change()
        elif kind == "q_error":
            job.status, job.err_kind, job.checked = "error", "run", False
            job.note = tr("Dönüştürülemedi") + ": " + short_name(msg[3], 70)
            self.notify(tr("{name} dönüştürülemedi", name=short_name(job.name, 30)), short_name(msg[3], 160), ms=5500)
            self._after_state_change()

    def _tick_queue(self):
        """Çalışan dosyanın kalan süresini ve ekrandaki ilerlemeyi tazeler (150 ms'de bir)."""
        job = next((j for j in self.jobs if j.status == "running"), None)
        if job is not None and job.t_start:
            elapsed = time.time() - job.t_start
            if job.pct >= 0.03 and elapsed >= 4:
                remaining = elapsed * (1 - job.pct) / job.pct
            else:
                est = self.est_seconds(job.model_key, job.duration)
                remaining = max(est - elapsed - 8, 0) if est else None
            if remaining is None:
                job.eta_text = ""
            elif remaining < 45:
                job.eta_text = tr("birkaç saniye kaldı")
            else:
                job.eta_text = tr("kalan {t}", t=fmt_estimate(remaining))
        if self.page == "queue":
            row = self.qrows.get(job.id) if job is not None else None
            if row is not None:
                row.update_progress()
            self._refresh_totals()
        elif self.page == "result" and self.queue_mode:
            self._update_banner()

    # ------------------------------------------------------------ 4) sonuç
    def view_job(self, job):
        self.view, self.queue_mode = job, True
        self.show_result()

    def _new_file(self):
        if self.queue_mode and self.jobs:
            body = tr("Kuyruk temizlenir; indirmediğiniz transkriptler kaybolur.")
            if self.queue_running:
                body += "\n" + tr("Çalışan dönüştürme de durdurulur.")
            if not self.confirm(tr("Yeni dosya seçilsin mi?") + "\n\n" + body, tr("Evet, temizle"), tr("Vazgeç")):
                return
            self._reset_queue()
        self.show_home()

    def show_result(self):
        job = self.view
        self._goto("result")
        page = self.container
        page.grid_columnconfigure((0, 1), weight=1, uniform="panel")
        for row, weight in ((0, 0), (1, 0), (2, 1), (3, 0)):
            page.grid_rowconfigure(row, weight=weight)

        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 12))
        if self.queue_mode:
            self._soft_button(head, tr("← Geri"), self.show_queue, width=92, height=38).pack(side="left", padx=(0, 14))
        self._label(head, tr("Transkript hazır"), 22, True).pack(side="left")
        self.nav_prev = None
        if self.queue_mode:
            self._build_nav(head)
        else:
            self._label(head, tr("{t} sürdü", t=fmt_duration(job.elapsed)), 13, color="muted").pack(
                side="left", padx=14, pady=(6, 0))
        self.sel_hint = self._label(head, "", 13, color="muted", wraplength=250, justify="right")
        self.sel_hint.pack(side="right", pady=(6, 0))

        self.banner = None
        if self.queue_mode:
            self._build_banner(page)

        self.var_plain = ctk.BooleanVar(value=True)
        self.var_timed = ctk.BooleanVar(value=False)
        self.panel_plain, self.cb_plain, self.tb_plain = self._make_panel(0, tr("Düz metin"), self.var_plain, False)
        self.panel_timed, self.cb_timed, self.tb_timed = self._make_panel(1, tr("Zaman damgalı"), self.var_timed, True)
        self._fill_result()

        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        self._soft_button(bar, tr("Yeni dosya"), self._new_file, width=120, height=42).pack(side="left")
        self.dl_btn = self._primary_button(bar, tr("İndir"), self._download, width=200)
        self.dl_btn.pack(side="right")
        self.fmt_dd = Dropdown(self, bar, self.dd_w(270), self.format_items, lambda: self.fmt, self._on_format, up=True)
        self.fmt_dd.btn.pack(side="right", padx=(12, 14))
        self._label(bar, tr("Dosya biçimi"), 14, True).pack(side="right")
        self._on_format(self.fmt)
        self._update_nav()
        self._update_banner()

    def _fill_result(self):
        """Görüntülenen dosyanın metnini iki panele yazar."""
        segments = self.view.segments
        total = len(segments)
        shown = segments[:PREVIEW_LINES]                # ekranda sadece ilk satırlar; indirilen dosya tamamını içerir
        note = (tr("İlk {n} satır gösteriliyor (toplam {total} satır). İndirilen dosya tamamını içerir.",
                   n=PREVIEW_LINES, total=total) if total > PREVIEW_LINES else "")
        for panel, tb, timed in ((self.panel_plain, self.tb_plain, False), (self.panel_timed, self.tb_timed, True)):
            tb.configure(state="normal")
            tb.delete("1.0", "end")
            if timed:
                for start, _, text in shown:
                    tb.insert("end", f"{fmt_clock(start)}  ", "ts")
                    tb.insert("end", f"{text}\n")
            else:
                tb.insert("1.0", "\n".join(t for _, _, t in shown))
            if not segments:
                tb.insert("1.0", tr("(Konuşma bulunamadı)"))
            tb.configure(state="disabled")
            tb.yview_moveto(0)
            if note:
                panel.note.configure(text=note)
                panel.note.pack(side="bottom", fill="x", padx=22, pady=(0, 16), before=tb)
                tb.pack_configure(pady=(10, 6))
            else:
                panel.note.pack_forget()
                tb.pack_configure(pady=(10, 20))
        self._style_text_tags()

    def _build_nav(self, head):
        """Başlıktaki dosya seçici: ‹ simge ad 2/3 ›  (biten transkriptler arasında gezinir)."""
        nav = ctk.CTkFrame(head, corner_radius=19, fg_color=self.T("zone"))
        nav.pack(side="left", padx=(18, 0), pady=(2, 0))

        def arrow(text, delta):
            return ctk.CTkButton(nav, text=text, width=30, height=30, corner_radius=15, fg_color="transparent",
                                 hover_color=self.T("line"), text_color=self.tone(), text_color_disabled=self.T("dash"),
                                 font=self.font(17, True), command=lambda: self._nav(delta))

        self.nav_prev = arrow("‹", -1)
        self.nav_prev.pack(side="left", padx=(5, 0), pady=4)
        self.nav_icon = ctk.CTkLabel(nav, text="", image=self.file_icon(self.view.kind, 24))
        self.nav_icon.pack(side="left", padx=(4, 6))
        self.nav_name = ctk.CTkLabel(nav, text="", text_color=self.T("ink"), font=self.font(13, True))
        self.nav_name.pack(side="left")
        self.nav_idx = ctk.CTkLabel(nav, text="", text_color=self.T("muted"), font=self.font(12.5))
        self.nav_idx.pack(side="left", padx=(8, 0))
        self.nav_next = arrow("›", 1)
        self.nav_next.pack(side="left", padx=(2, 5), pady=4)

    def _update_nav(self):
        if self.page != "result" or not self.queue_mode or self.nav_prev is None or not self.nav_prev.winfo_exists():
            return
        job, order = self.view, self.done_order
        p = order.index(job) if job in order else -1
        self.nav_icon.configure(image=self.file_icon(job.kind, 24))
        self.nav_name.configure(text=short_name(job.name, 22))
        self.nav_idx.configure(text=f"{p + 1}/{len(order)}" if len(order) > 1 and p >= 0 else "")
        self.nav_prev.configure(state="normal" if p > 0 else "disabled")
        self.nav_next.configure(state="normal" if 0 <= p < len(order) - 1 else "disabled")

    def _nav(self, delta):
        order = self.done_order
        if self.view not in order:
            return
        p = order.index(self.view) + delta
        if 0 <= p < len(order):
            self.view = order[p]
            self._fill_result()
            self._update_nav()

    def _build_banner(self, page):
        """Sonuç ekranının üstünde, kuyruğun durumunu gösteren şerit (tıklanınca kuyruğa gider)."""
        b = ctk.CTkFrame(page, fg_color=self.TT("card", "accent", 0.12), border_width=2,
                         border_color=self.TT("line", "accent", 0.5), corner_radius=16, cursor="hand2")
        b.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        b.grid_remove()
        self.banner, self._banner_on, self._banner_busy = b, False, False
        go = self._soft_button(b, tr("Kuyruğa git"), self.show_queue, width=110, height=34)
        go.pack(side="right", padx=(10, 16), pady=10)
        self.bn_pct = ctk.CTkLabel(b, text="", text_color=self.T("ink"), font=self.font(14, True), width=44, anchor="e")
        self.bn_pct.pack(side="right")
        self.bn_bar = ctk.CTkProgressBar(b, width=170, height=8, corner_radius=4, fg_color=self.T("line"),
                                         progress_color=self.T("accent"))
        self.bn_bar.pack(side="right", padx=(10, 8))
        self.bn_icon = ctk.CTkLabel(b, text="", image=self.ring_frames()[0])
        self.bn_icon.pack(side="left", padx=(16, 10), pady=10)
        text = ctk.CTkFrame(b, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, pady=8)       # kenarlığa değmesin
        self.bn_title = ctk.CTkLabel(text, text="", text_color=self.T("ink"), font=self.font(13.5, True), anchor="w",
                                     height=22)
        self.bn_title.pack(fill="x")
        self.bn_name = ctk.CTkLabel(text, text="", text_color=self.T("muted"), font=self.font(12), anchor="w",
                                    height=18)
        self.bn_name.pack(fill="x")
        for w in (b, self.bn_icon, text, self.bn_title, self.bn_name):
            w.bind("<Button-1>", lambda e: self.show_queue())

    def _update_banner(self):
        b = self.banner
        if self.page != "result" or not self.queue_mode or b is None or not b.winfo_exists():
            return
        run = [j for j in self.jobs if j.sel]
        cur = next((j for j in run if j.status == "running"), None) or next((j for j in run if j.status == "queued"), None)
        if cur is not None and self.queue_running:
            self._banner_busy = True
            idx = run.index(cur) + 1
            self.bn_title.configure(text=tr("Sıradaki dosya dönüştürülüyor · {i}/{n}", i=idx, n=len(run)))
            self.bn_name.configure(text=short_name(cur.name, 60))
            self.bn_bar.set(cur.pct if cur.status == "running" else 0)
            self.bn_pct.configure(text=fmt_pct(cur.pct) if cur.status == "running" else "—")
            if not self._spin_job:
                self._spin()
        elif run and all(j.status == "done" for j in run):
            self._banner_busy = False
            self.bn_icon.configure(image=self.ring_frames(True)[0])
            self.bn_title.configure(text=tr("Tüm dosyalar tamamlandı · {n}/{n}", n=len(run)))
            self.bn_name.configure(text=tr("Transkriptlere kuyruk ekranından ulaşabilirsiniz"))
            self.bn_bar.set(1)
            self.bn_pct.configure(text="✓")
        else:
            self._banner_busy = False
            if self._banner_on:
                b.grid_remove()
                self._banner_on = False
            return
        if not self._banner_on:
            b.grid()
            self._banner_on = True

    def _spin(self):
        self._spin_job = None
        b = self.banner
        if self.page != "result" or b is None or not b.winfo_exists() or not self._banner_busy:
            return
        self._spin_k = (self._spin_k + 1) % 12
        self.bn_icon.configure(image=self.ring_frames()[self._spin_k])
        self._spin_job = self.after(90, self._spin)

    def _make_panel(self, col, title, var, timed):
        panel = ctk.CTkFrame(self.container, fg_color=self.T("card"), border_width=2,
                             border_color=self.T("line"), corner_radius=18)
        panel.grid(row=2, column=col, sticky="nsew", padx=(0, 7) if col == 0 else (7, 0))
        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.pack(fill="x", padx=22, pady=(16, 10))          # içerik yuvarlak köşe yayının dışında kalsın
        cb = ctk.CTkCheckBox(
            head, text=title, variable=var, command=self._sync_dl, width=20, checkbox_width=22, checkbox_height=22,
            corner_radius=7, border_width=2, fg_color=self.T("accent"), hover_color=self.TT("accent", "ink", 0.12),
            checkmark_color=self.T("on_accent"), border_color=self.T("dash"), text_color=self.T("ink"),
            text_color_disabled=self.T("muted"), font=self.font(14, True))
        cb.pack(side="left")
        copy = self._soft_button(head, tr("Kopyala"), None, width=84, height=28)
        copy.configure(font=self.font(12, True))
        copy.pack(side="right")
        # ayırıcı çizgi panelin çerçevesine değmesin (aksi halde çerçeve kesiliyor)
        ctk.CTkFrame(panel, height=3, corner_radius=0, fg_color=self.TT("line", "dash", 0.3)).pack(fill="x", padx=18)
        tb = ctk.CTkTextbox(panel, fg_color="transparent", text_color=self.T("ink"), wrap="word",
                            font=self.font(14), border_width=0, activate_scrollbars=True,
                            scrollbar_button_color=self.T("line"), scrollbar_button_hover_color=self.T("dash"))
        tb.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        panel.note = ctk.CTkLabel(panel, text="", text_color=self.T("muted"), font=self.font(11.5), anchor="w")
        copy.configure(command=lambda b=copy, k=timed: self._copy(k, b))
        return panel, cb, tb

    def _style_text_tags(self):
        if self.page != "result":
            return
        try:
            self.tb_timed.tag_config("ts", foreground=self.hexc("muted"))
        except Exception:
            pass

    def _copy(self, timed, button):
        self.clipboard_clear()
        self.clipboard_append(build_text(self.view.segments, timed))        # ekrandaki önizleme değil, metnin tamamı
        button.configure(text=tr("Kopyalandı ✓"))
        self.after(1500, lambda: button.winfo_exists() and button.configure(text=tr("Kopyala")))

    def format_items(self):
        return [dict(key=k, name=tr(v[0]), desc=tr(v[2]), right=v[1]) for k, v in FORMATS.items()]

    def _on_format(self, key):
        self.fmt = key
        self.cfg["format"] = key
        save_config(self.cfg)
        if self.page != "result":
            return
        if key == "srt":                          # altyazı = zaman damgalı metin
            self.var_plain.set(False)
            self.cb_plain.configure(state="disabled")
            self.var_timed.set(True)
        else:
            self.cb_plain.configure(state="normal")
        self._sync_dl()
        self.fmt_dd.refresh()

    def _sync_dl(self):
        plain, timed = self.var_plain.get(), self.var_timed.get()
        self.panel_plain.configure(border_color=self.T("accent") if plain else self.T("line"))
        self.panel_timed.configure(border_color=self.T("accent") if timed else self.T("line"))
        n = int(plain) + int(timed)
        self.dl_btn.configure(text=tr("Bir metin seçin") if n == 0 else tr("İndir") if n == 1 else tr("2 dosyayı indir"),
                              state="disabled" if n == 0 else "normal")
        if self.fmt == "srt":
            hint = tr("Sadece zaman damgalı seçildi (altyazı biçimi)")
        elif plain and timed:
            hint = tr("İkisi de seçildi")
        elif plain:
            hint = tr("Sadece düz metin seçildi")
        elif timed:
            hint = tr("Sadece zaman damgalı seçildi")
        else:
            hint = tr("İndirmek istediklerinizi işaretleyin")
        self.sel_hint.configure(text=hint)

    def _download(self):
        stem = Path(self.view.name).stem
        wanted = []
        if self.var_plain.get():
            wanted.append((False, stem))
        if self.var_timed.get():
            wanted.append((True, tr("{stem} (zaman damgalı)", stem=stem)))
        if wanted:
            self._export(self.view, wanted)

    def _download_job(self, job):
        """Kuyruktaki satırın "İndir" düğmesi: düz metni seçili biçimde kaydeder."""
        self._export(job, [(self.fmt == "srt", Path(job.name).stem)])

    def _export(self, job, wanted):
        ext = FORMATS[self.fmt][1]
        if len(wanted) == 1:
            path = filedialog.asksaveasfilename(
                title=tr("Kaydet"), initialfile=wanted[0][1], defaultextension=ext,
                filetypes=[(tr(FORMATS[self.fmt][0]), f"*{ext}")])
            if not path:
                return
            targets = [(wanted[0][0], Path(path))]
        else:
            folder = filedialog.askdirectory(title=tr("Dosyaların kaydedileceği klasörü seçin"))
            if not folder:
                return
            targets = [(timed, Path(folder) / f"{name}{ext}") for timed, name in wanted]
            existing = [p.name for _, p in targets if p.exists()]
            if existing and not self.confirm(
                    tr("Şu dosyalar zaten var, üzerine yazılsın mı?\n\n{files}", files="\n".join(existing)),
                    tr("Üzerine yaz"), tr("Vazgeç")):
                return
        try:
            for timed, path in targets:
                write_export(path, self.fmt, Path(job.name).stem, job.segments, timed or self.fmt == "srt")
        except Exception as exc:  # noqa: BLE001
            self.show_error(tr("Dosya kaydedilemedi.\n\nSeçtiğiniz konuma yazılamadı. Başka bir klasör deneyin.\n({err})",
                               err=exc))
            return
        self.notify(tr("Dosya indirme işlemi tamamlandı."), warn=False, ms=3600)

    def confirm(self, message, yes, no):
        """Temaya uyan evet/hayır penceresi; "evet" seçilirse True döner."""
        dlg = ErrorDialog(self, message, kind="info", buttons=[(no, False, False), (yes, True, True)])
        self.wait_window(dlg)
        return bool(dlg.result)


def selftest(audio_path, out_path):
    """Pencere açmadan transkripsiyon hattını dener: sesten.exe --selftest ses.wav sonuc.txt"""
    q = queue.Queue()
    worker = Worker(audio_path, "fast", None, q)
    worker.start()
    worker.join()
    lines = []
    while not q.empty():
        msg = q.get()
        lines.append(" ".join(map(str, msg)) if msg[0] != "done" else "done\n" + build_text(msg[1], False))
        if msg[0] == "done":                      # Word ve PDF yazıcılarını da dene
            for fmt in ("docx", "pdf"):
                try:
                    write_export(Path(out_path).with_suffix("." + fmt), fmt, "selftest", msg[1], True)
                    lines.append(f"{fmt} tamam")
                except Exception as exc:  # noqa: BLE001
                    lines.append(f"{fmt} HATA {type(exc).__name__}: {exc}")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--selftest":
        selftest(sys.argv[2], sys.argv[3])
    else:
        App().mainloop()
