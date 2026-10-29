# Üçüncü taraf bileşenler ve lisansları

[English](THIRD_PARTY_NOTICES.md) · **Türkçe**

Bu projenin kendi kodu [MIT lisansı](LICENSE) ile yayınlanmıştır. Program aşağıdaki açık kaynak bileşenleri kullanır.
Bu liste bilgilendirme amaçlıdır ve hukuki danışmanlık yerine geçmez. Ayrıntılar için her bileşenin kendi sayfasına bakın.

## Konuşmayı yazıya çeviren bileşenler

| Bileşen | Lisans | Adres |
|---|---|---|
| faster-whisper | MIT | https://github.com/SYSTRAN/faster-whisper |
| CTranslate2 | MIT | https://github.com/OpenNMT/CTranslate2 |
| ONNX Runtime | MIT | https://github.com/microsoft/onnxruntime |
| Silero VAD (faster-whisper içinde) | MIT | https://github.com/snakers4/silero-vad |
| OpenAI Whisper modelleri | MIT | https://github.com/openai/whisper |

Whisper model dosyaları (Systran tarafından CTranslate2 biçimine çevrilmiş sürümleri) programla birlikte **dağıtılmaz**.
İlk kullanımda kullanıcının bilgisayarına Hugging Face üzerinden indirilir.

## Ses ve video çözme

| Bileşen | Lisans | Adres |
|---|---|---|
| PyAV | BSD-3-Clause | https://github.com/PyAV-Org/PyAV |
| FFmpeg kütüphaneleri (PyAV paketinin içinde) | LGPL-2.1+ ve GPL-2+ (bileşene göre) | https://ffmpeg.org |

**GPL hakkında önemli not:** PyAV'ın Windows paketindeki FFmpeg derlemesi, GPL lisanslı `libx264` ve `libx265`
kütüphanelerini de içerir. Bu projenin derlenmiş kurulum dosyası (`MedyaTextKurulum.exe`, `MedyaText.exe`) bu
kütüphaneleri barındırdığı için, ikili dosyanın dağıtımında bu bileşenlerin lisans koşulları geçerlidir.
Program yalnızca ses/video **çözme** için FFmpeg'i kullanır, kodlama yapmaz. Bu bileşenlerin kaynak kodları:

- FFmpeg: https://ffmpeg.org/download.html
- x264: https://www.videolan.org/developers/x264.html
- x265: https://www.x265.org
- PyAV'ın kullandığı FFmpeg paketinin kaynak sürümleri ve derleme betikleri: https://github.com/PyAV-Org/pyav-ffmpeg

FFmpeg içindeki diğer kütüphaneler: libmp3lame (LGPL), libopus (BSD), libvpx (BSD), dav1d (BSD-2-Clause),
SVT-AV1 (BSD-3-Clause-Clear), opencore-amr (Apache-2.0), libwebp (BSD-3-Clause).

## Arayüz ve dosya çıktıları

| Bileşen | Lisans | Adres |
|---|---|---|
| CustomTkinter (içinde Roboto yazı tipi, Apache-2.0) | MIT | https://github.com/TomSchimansky/CustomTkinter |
| tkinterdnd2 (tkdnd ile) | MIT | https://github.com/Eliav2/tkinterdnd2 |
| Pillow | MIT-CMU (HPND) | https://github.com/python-pillow/Pillow |
| python-docx (lxml ile) | MIT (lxml: BSD-3-Clause) | https://github.com/python-openxml/python-docx |
| fpdf2 | **LGPL-3.0** | https://github.com/py-pdf/fpdf2 |
| fontTools, defusedxml | MIT, PSF | https://github.com/fonttools/fonttools |

`fpdf2` LGPL-3.0 lisanslıdır. Kütüphane değiştirilmeden kullanılmıştır; kaynak kodu yukarıdaki adresten alınabilir.
Kaynaktan derleme yapan herkes kütüphaneyi kendi sürümüyle değiştirebilir (`requirements.txt`).

## Diğer kütüphaneler

NumPy (BSD-3-Clause), huggingface_hub (Apache-2.0), tokenizers (Apache-2.0), tqdm (MPL-2.0 / MIT), PyYAML (MIT),
Python (PSF).

## Derleme araçları

- **PyInstaller** (GPL-2.0 ve "önyükleyici istisnası"): Derlenen programın lisansını etkilemez.
- **Inno Setup**: Kurulum dosyasını oluşturmak için kullanılır.
