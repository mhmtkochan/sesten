"""Medya - Text Dönüştürücü: ses ve videoları yazıya çeviren, tamamen çevrimdışı çalışan masaüstü uygulaması."""
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
from pathlib import Path

# Pencereli (konsolsuz) exe'de stdout/stderr None olur; tqdm/huggingface çökmesin diye.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import customtkinter as ctk
from PIL import Image, ImageDraw
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

LANG = "tr"          # arayüz dili: "tr" (varsayılan) ya da "en"

# Türkçe metin anahtar, İngilizce karşılığı değer. İngilizce seçilince metin buradan bulunur.
EN = {
    # üst bar, tema
    "Ses ve videodan yazıya": "Audio and video to text",
    "Tema": "Theme", "TEMA": "THEME", "RENK": "COLOR",
    "Otomatik": "Automatic", "Açık": "Light", "Koyu": "Dark",
    "Yumuşak": "Soft", "Karamel": "Caramel", "Bal": "Honey", "Adaçayı": "Sage",
    "Okyanus": "Ocean", "Nergis": "Daffodil", "Lavanta": "Lavender",
    # giriş ekranı
    "Ses veya video dosyasının bağlantısını yapıştırın": "Paste a link to an audio or video file",
    "Yükle": "Load",
    "veya": "or",
    "Dosyayı buraya sürükleyebilirsiniz": "You can drag the file here",
    "ya da buraya tıklayıp seçebilirsiniz": "or click here to choose it",
    "MP3 · WAV · M4A · MP4 · MKV · MOV ve daha fazlası": "MP3 · WAV · M4A · MP4 · MKV · MOV and more",
    "Ses veya video dosyası seç": "Choose an audio or video file",
    "Ses ve video dosyaları": "Audio and video files",
    "Tüm dosyalar": "All files",
    "Birden fazla dosya seçildi": "More than one file selected",
    "Aynı anda yalnızca bir dosya yükleyebilirsiniz. Lütfen tek bir dosya seçin.":
        "You can only load one file at a time. Please choose a single file.",
    "Klasör seçildi": "Folder selected",
    "Lütfen klasör yerine tek bir ses veya video dosyası seçin.":
        "Please choose a single audio or video file instead of a folder.",
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
}


def tr(text, **kw):
    """Arayüz metnini seçili dile çevirir; {alan} içeren metinlerde değerleri yerleştirir."""
    out = EN.get(text, text) if LANG == "en" else text
    return out.format(**kw) if kw else out


def app_title():
    return "Media - Text Converter" if LANG == "en" else "Medya - Text Dönüştürücü"


def app_tagline():
    return tr("Ses ve videodan yazıya")
CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "MedyaTextDonusturucu" / "config.json"
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


def spoken_label(key):
    for k, _, name_tr, name_en in SPOKEN:
        if k == key:
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
    return ("sec", "min", "h") if LANG == "en" else ("sn", "dk", "sa")


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


def render_logo(accent, on_accent, px=84):
    S = 4
    N = px * S
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, N - 1, N - 1], radius=int(N * 13 / 42), fill=_hex(accent))
    u = N / 42
    off = (N - 24 * u) / 2
    wd = 2.4 * u
    col = _hex(on_accent)
    for x, y1, y2 in [(3.5, 10, 14), (8, 6.5, 17.5), (12.5, 3.5, 20.5), (17, 7.5, 16.5), (21, 10.5, 13.5)]:
        X, ya, yb = off + x * u, off + y1 * u, off + y2 * u
        d.line([(X, ya), (X, yb)], fill=col, width=int(wd))
        for Y in (ya, yb):
            d.ellipse([X - wd / 2, Y - wd / 2, X + wd / 2, Y + wd / 2], fill=col)
    return img.resize((px, px), Image.Resampling.LANCZOS)


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
    """Türkiye ("tr") ve İngiltere ("en") bayrağı; köşeleri yuvarlatılmış küçük simge (2x çıktı)."""
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MedyaText"})
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


# ---------------------------------------------------------------- açılır liste
def bind_tree(widget, sequence, func):
    widget.bind(sequence, func, add="+")
    for child in widget.winfo_children():
        bind_tree(child, sequence, func)


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
    """Uygulamanın temasına uyan, kırmızı simgeli hata penceresi (Windows'un standart kutusu yerine)."""

    def __init__(self, app, message):
        super().__init__(app)
        self.app = app
        self.withdraw()
        self.title(app_title())
        self.resizable(False, False)
        self.configure(fg_color=app.T("bg"))

        head, _, body = message.strip().partition("\n\n")
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
        ok = app._primary_button(self, tr("Tamam"), self.close, width=120)
        ok.configure(height=40, corner_radius=20, font=app.font(14, True))
        ok.pack(side="bottom", anchor="e", padx=28, pady=(8, 24))

        self.update_idletasks()
        w, h = app.lg(self.winfo_reqwidth()), app.lg(self.winfo_reqheight())
        x = app.lg(app.winfo_rootx()) + (app.lg(app.winfo_width()) - w) // 2
        y = app.lg(app.winfo_rooty()) + (app.lg(app.winfo_height()) - h) // 3
        self.geometry(f"{int(w)}x{int(h)}+{int(max(x, 0))}+{int(max(y, 0))}")
        self.transient(app)
        self.deiconify()
        self.bind("<Return>", lambda e: self.close())
        self.bind("<Escape>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(60, self._modal)
        self.after(300, self._icon)

    def _modal(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _icon(self):
        ico = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "app.ico"
        try:
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    def close(self):
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
        if LANG not in ("tr", "en"):
            LANG = "tr"
        self.theme_mode = self.cfg.get("theme", "system")
        if self.theme_mode not in [m for m, _ in THEME_MODES]:
            self.theme_mode = "system"
        self.color = self.cfg.get("color", "yumusak")
        if self.color not in COLORS:
            self.color = "yumusak"
        ctk.set_appearance_mode(self.theme_mode)

        self.title(app_title())
        self.geometry("920x700")
        self.minsize(780, 640)
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
        self.segments = []
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
        self.after(300, self._set_icon)         # CTk kendi simgesini 200 ms sonra koyar, ondan sonra değiştiriyoruz

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
        for w in (self.worker, self.link_worker):
            if w is not None:
                w.cancel.set()
        self._cleanup_tmp()
        self.destroy()

    def _set_icon(self):
        ico = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "app.ico"
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
        logo = ctk.CTkImage(light_image=render_logo(pal_l["accent"], pal_l["on_accent"]),
                            dark_image=render_logo(pal_d["accent"], pal_d["on_accent"]), size=(42, 42))
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
            self.header, text=("English" if LANG == "en" else "Türkçe") + "  ▾", image=flag, compound="left",
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
        options = (("tr", "Türkçe"), ("en", "English"))
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
            child.destroy()
        self.zone_frame = None
        self.stack = None
        self._show_header_buttons(page == "home")

    def _label(self, parent, text, size=14, bold=False, color="ink", **kw):
        return ctk.CTkLabel(parent, text=text, text_color=self.T(color), font=self.font(size, bold), **kw)

    def _primary_button(self, parent, text, command, width=220):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=48, corner_radius=24,
                             fg_color=self.T("accent"), hover_color=self.TT("accent", "ink", 0.12),
                             text_color=self.T("on_accent"), text_color_disabled=self.T("on_accent"),
                             font=self.font(15, True))

    def _soft_button(self, parent, text, command, width=120, height=38):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=height,
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
        title = ctk.CTkLabel(zf, text=tr("Dosyayı buraya sürükleyebilirsiniz"), text_color=self.T("ink"),
                             fg_color=zc, bg_color=zc, font=self.font(23, True), cursor="hand2")
        sub = ctk.CTkLabel(zf, text=tr("ya da buraya tıklayıp seçebilirsiniz"), text_color=self.T("muted"),
                           fg_color=zc, bg_color=zc, font=self.font(14.5), cursor="hand2")
        fmts = ctk.CTkLabel(zf, text=tr("MP3 · WAV · M4A · MP4 · MKV · MOV ve daha fazlası"), text_color=self.T("muted"),
                            fg_color=zc, bg_color=zc, font=self.font(12), cursor="hand2")
        title.place(relx=0.5, rely=0.62, anchor="center")
        sub.place(relx=0.5, rely=0.72, anchor="center")
        fmts.place(relx=0.5, rely=0.85, anchor="center")
        for w in (zf, self.zone_label, title, sub, fmts):
            w.bind("<Button-1>", lambda e: self._browse())
        self.after(30, self._layout_zone)

    def _layout_zone(self):
        if self.page != "home" or self.zone_frame is None or not self.zone_frame.winfo_exists():
            return
        cw = self.lg(self.container.winfo_width())
        ch = self.lg(self.container.winfo_height())
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
        path = filedialog.askopenfilename(title=tr("Ses veya video dosyası seç"), filetypes=media_types())
        if path:
            self._load_file(path)

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
        if self.busy or self.page != "home":
            return
        if len(paths) > 1:
            self.notify(tr("Birden fazla dosya seçildi"),
                        tr("Aynı anda yalnızca bir dosya yükleyebilirsiniz. Lütfen tek bir dosya seçin."))
        elif paths and os.path.isdir(paths[0]):
            self.notify(tr("Klasör seçildi"), tr("Lütfen klasör yerine tek bir ses veya video dosyası seçin."))
        elif paths:
            self._load_file(paths[0])

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
        self.tmp_dir = tempfile.mkdtemp(prefix="MedyaText_")
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
    def est_seconds(self, key):
        if not self.file_duration:
            return None
        ratio = self.cfg.get("ratios", {}).get(key, MODELS[key][3])
        return self.file_duration * ratio + 8

    def resolved_model(self):
        if self.speed != "auto":
            return self.speed
        if not self.file_duration:
            return "balanced"
        for key in ("best", "balanced"):          # tahmini süresi 15 dk'yı geçmeyen en doğru model
            if self.est_seconds(key) <= 900:
                return key
        return "fast"

    def speed_items(self):
        items = []
        for key, name, desc in SPEEDS:
            right = ""
            if key != "auto" and self.file_duration:
                right = fmt_estimate(self.est_seconds(key))
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
            self, row, 300, self.speed_items, lambda: self.speed, self._on_speed)
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
        mode = ctk.get_appearance_mode()
        if mode != self._mode_seen:
            self._mode_seen = mode
            self._style_text_tags()
        self.after(150, self._poll_queue)

    def _handle(self, msg):
        kind = msg[0]
        if kind == "loading":
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
            self._remember_speed(elapsed, total)
            self.segments = segments
            self.show_result(elapsed)
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

    def _remember_speed(self, elapsed, total):
        if total >= 20:
            ratios = self.cfg.setdefault("ratios", {})
            old = ratios.get(self.model_key)
            new = elapsed / total
            ratios[self.model_key] = new if old is None else round(0.5 * old + 0.5 * new, 4)
            save_config(self.cfg)

    # ------------------------------------------------------------ 4) sonuç
    def show_result(self, elapsed):
        self._goto("result")
        page = self.container
        page.grid_columnconfigure((0, 1), weight=1, uniform="panel")
        page.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(2, 12))
        self._label(head, tr("Transkript hazır"), 22, True).pack(side="left")
        self._label(head, tr("{t} sürdü", t=fmt_duration(elapsed)), 13, color="muted").pack(
            side="left", padx=14, pady=(6, 0))
        self.sel_hint = self._label(head, "", 13, color="muted")
        self.sel_hint.pack(side="right", pady=(6, 0))

        self.var_plain = ctk.BooleanVar(value=True)
        self.var_timed = ctk.BooleanVar(value=False)
        total = len(self.segments)
        shown = self.segments[:PREVIEW_LINES]           # ekranda sadece ilk satırlar; indirilen dosya tamamını içerir
        note = (tr("İlk {n} satır gösteriliyor (toplam {total} satır). İndirilen dosya tamamını içerir.",
                   n=PREVIEW_LINES, total=total) if total > PREVIEW_LINES else "")
        self.panel_plain, self.cb_plain, self.tb_plain = self._make_panel(
            0, tr("Düz metin"), self.var_plain, False, note)
        self.panel_timed, self.cb_timed, self.tb_timed = self._make_panel(
            1, tr("Zaman damgalı"), self.var_timed, True, note)

        for tb, timed in ((self.tb_plain, False), (self.tb_timed, True)):
            tb.configure(state="normal")
            if timed:
                for start, _, text in shown:
                    tb.insert("end", f"{fmt_clock(start)}  ", "ts")
                    tb.insert("end", f"{text}\n")
            else:
                tb.insert("1.0", "\n".join(t for _, _, t in shown))
            if not self.segments:
                tb.insert("1.0", tr("(Konuşma bulunamadı)"))
            tb.configure(state="disabled")
        self._style_text_tags()

        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        self._soft_button(bar, tr("Yeni dosya"), self.show_home, width=120, height=42).pack(side="left")
        self.dl_btn = self._primary_button(bar, tr("İndir"), self._download, width=200)
        self.dl_btn.pack(side="right")
        self.fmt_dd = Dropdown(self, bar, 270, self.format_items, lambda: self.fmt, self._on_format, up=True)
        self.fmt_dd.btn.pack(side="right", padx=(12, 14))
        self._label(bar, tr("Dosya biçimi"), 14, True).pack(side="right")
        self._on_format(self.fmt)

    def _make_panel(self, col, title, var, timed, note=""):
        panel = ctk.CTkFrame(self.container, fg_color=self.T("card"), border_width=2,
                             border_color=self.T("line"), corner_radius=18)
        panel.grid(row=1, column=col, sticky="nsew", padx=(0, 7) if col == 0 else (7, 0))
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
        if note:
            ctk.CTkLabel(panel, text=note, text_color=self.T("muted"), font=self.font(11.5), anchor="w").pack(
                side="bottom", fill="x", padx=22, pady=(0, 16))
        tb = ctk.CTkTextbox(panel, fg_color="transparent", text_color=self.T("ink"), wrap="word",
                            font=self.font(14), border_width=0, activate_scrollbars=True,
                            scrollbar_button_color=self.T("line"), scrollbar_button_hover_color=self.T("dash"))
        tb.pack(fill="both", expand=True, padx=20, pady=(10, 6 if note else 20))
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
        self.clipboard_append(build_text(self.segments, timed))        # ekrandaki önizleme değil, metnin tamamı
        button.configure(text=tr("Kopyalandı ✓"))
        self.after(1500, lambda: button.winfo_exists() and button.configure(text=tr("Kopyala")))

    def format_items(self):
        return [dict(key=k, name=tr(v[0]), desc=tr(v[2]), right=v[1]) for k, v in FORMATS.items()]

    def _on_format(self, key):
        self.fmt = key
        self.cfg["format"] = key
        save_config(self.cfg)
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
        ext = FORMATS[self.fmt][1]
        stem = Path(self.file_path).stem
        wanted = []
        if self.var_plain.get():
            wanted.append((False, stem))
        if self.var_timed.get():
            wanted.append((True, tr("{stem} (zaman damgalı)", stem=stem)))
        if not wanted:
            return
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
            if existing and not messagebox.askyesno(
                    app_title(), tr("Şu dosyalar zaten var, üzerine yazılsın mı?\n\n{files}", files="\n".join(existing))):
                return
        try:
            for timed, path in targets:
                write_export(path, self.fmt, stem, self.segments, timed or self.fmt == "srt")
        except Exception as exc:  # noqa: BLE001
            self.show_error(tr("Dosya kaydedilemedi.\n\nSeçtiğiniz konuma yazılamadı. Başka bir klasör deneyin.\n({err})",
                               err=exc))
            return
        self.notify(tr("Dosya indirme işlemi tamamlandı."), warn=False, ms=3600)


def selftest(audio_path, out_path):
    """Pencere açmadan transkripsiyon hattını dener: MedyaText.exe --selftest ses.wav sonuc.txt"""
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
