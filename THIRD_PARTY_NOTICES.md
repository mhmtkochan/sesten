# Third-party components and their licenses

**English** · [Türkçe](THIRD_PARTY_NOTICES.tr.md)

The code of this project is released under the [MIT license](LICENSE). The program uses the open-source components
listed below. This list is for information only and is not legal advice. See each component's own page for details.

## Components that turn speech into text

| Component | License | Address |
|---|---|---|
| faster-whisper | MIT | https://github.com/SYSTRAN/faster-whisper |
| CTranslate2 | MIT | https://github.com/OpenNMT/CTranslate2 |
| ONNX Runtime | MIT | https://github.com/microsoft/onnxruntime |
| Silero VAD (inside faster-whisper) | MIT | https://github.com/snakers4/silero-vad |
| OpenAI Whisper models | MIT | https://github.com/openai/whisper |

The Whisper model files (the versions converted to the CTranslate2 format by Systran) are **not distributed** with
the program. They are downloaded to the user's computer from Hugging Face on first use.

## Audio and video decoding

| Component | License | Address |
|---|---|---|
| PyAV | BSD-3-Clause | https://github.com/PyAV-Org/PyAV |
| FFmpeg libraries (inside the PyAV package) | LGPL-2.1+ and GPL-2+ (depending on the component) | https://ffmpeg.org |

**Important note about the GPL:** the FFmpeg build in PyAV's Windows package also contains the GPL-licensed
`libx264` and `libx265` libraries. Because the compiled installer of this project (`MedyaTextKurulum.exe`,
`MedyaText.exe`) contains these libraries, the license terms of these components apply to the distribution of the
binary. The program uses FFmpeg only for **decoding** audio/video, not for encoding. Source code of these components:

- FFmpeg: https://ffmpeg.org/download.html
- x264: https://www.videolan.org/developers/x264.html
- x265: https://www.x265.org
- Source versions and build scripts of the FFmpeg package used by PyAV: https://github.com/PyAV-Org/pyav-ffmpeg

Other libraries inside FFmpeg: libmp3lame (LGPL), libopus (BSD), libvpx (BSD), dav1d (BSD-2-Clause),
SVT-AV1 (BSD-3-Clause-Clear), opencore-amr (Apache-2.0), libwebp (BSD-3-Clause).

## Interface and file output

| Component | License | Address |
|---|---|---|
| CustomTkinter (includes the Roboto font, Apache-2.0) | MIT | https://github.com/TomSchimansky/CustomTkinter |
| tkinterdnd2 (with tkdnd) | MIT | https://github.com/Eliav2/tkinterdnd2 |
| Pillow | MIT-CMU (HPND) | https://github.com/python-pillow/Pillow |
| python-docx (with lxml) | MIT (lxml: BSD-3-Clause) | https://github.com/python-openxml/python-docx |
| fpdf2 | **LGPL-3.0** | https://github.com/py-pdf/fpdf2 |
| fontTools, defusedxml | MIT, PSF | https://github.com/fonttools/fonttools |

`fpdf2` is licensed under the LGPL-3.0. The library is used unmodified; its source code is available at the address
above. Anyone building from source can replace the library with their own version (`requirements.txt`).

## Other libraries

NumPy (BSD-3-Clause), huggingface_hub (Apache-2.0), tokenizers (Apache-2.0), tqdm (MPL-2.0 / MIT), PyYAML (MIT),
Python (PSF).

## Build tools

- **PyInstaller** (GPL-2.0 with the "bootloader exception"): does not affect the license of the built program.
- **Inno Setup**: used to create the installer.
