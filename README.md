# DnD Audio Transcriber

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![WhisperX](https://img.shields.io/badge/WhisperX-large--v3-412991)](https://github.com/m-bain/whisperX)
[![PyTorch](https://img.shields.io/badge/PyTorch-CUDA%2012.4-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A personal Python project for transcribing Spanish Dungeons and Dragons session recordings and producing structured session recaps. Audio is processed locally with GPU-accelerated speech recognition; summaries are generated manually through Google Gemini Advanced using a curated name glossary and prompt template.

## Overview

This repository implements a local-first transcription pipeline for tabletop session audio (typically MP3 exports from Audacity). The goal is to convert multi-hour recordings into timestamped, speaker-labelled text suitable for downstream AI-assisted recap writing, without relying on a paid transcription API.

```text
Session MP3
    |
    v
WhisperX (local, CUDA)
    |
    +-- Transcription (OpenAI Whisper large-v3)
    +-- Word alignment (Spanish)
    +-- Speaker diarization (pyannote)
    |
    v
Timestamped transcript (.txt)
    |
    v
Gemini Advanced (manual upload)
    +-- names.txt (campaign glossary)
    +-- prompts/gemini_recap.txt
    |
    v
Session recap (.md)
```

## Features

- Local transcription with **WhisperX** and **large-v3**, forced to Spanish (`es`)
- **GPU acceleration** via PyTorch CUDA (`float16` on NVIDIA hardware)
- **Speaker diarization** output (`SPEAKER_00`, `SPEAKER_01`, etc.) with segment timestamps
- **Campaign glossary** (`names.txt`) to correct fantasy names and places in Gemini
- **Reusable recap prompt** (`prompts/gemini_recap.txt`) for consistent session summaries
- **Automation pipeline** — PowerShell menu script that orchestrates chunking, transcribing, and merging
- Pilot script (`pilot_whisperx.py`) now accepts CLI arguments (no hardcoded paths)
- **Automatic merge** of chunked transcripts into a single continuous-timestamp file

## Requirements

### Hardware

- NVIDIA GPU with CUDA support (developed and tested on an **RTX 3060 Ti**, 8 GB VRAM)
- Sufficient disk space for Whisper model weights (~3 GB for large-v3)

### Software

| Component | Purpose |
|-----------|---------|
| Python 3.12 | Recommended interpreter for the project virtual environment |
| CUDA-enabled PyTorch | GPU inference (CPU-only builds will not work with `--device cuda`) |
| [FFmpeg](https://ffmpeg.org/) | Audio loading and decoding |
| [WhisperX](https://github.com/m-bain/whisperX) | Transcription, alignment, and diarization pipeline |
| Hugging Face account | Required for pyannote diarization models |

### Hugging Face model access

Accept the user conditions for the diarization models used by WhisperX (for example [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)). Create a read token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and expose it as `HF_TOKEN` in your environment.

## Installation

Clone the repository and create a virtual environment from the project root:

```powershell
cd DnD-audio-transcriber
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
```

Install CUDA-enabled PyTorch before WhisperX. Use the index URL that matches your driver and CUDA toolkit (example below uses CUDA 12.4 wheels):

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

Verify GPU availability:

```powershell
python -c "import torch; print(torch.__version__); print('cuda:', torch.cuda.is_available())"
```

Expected output includes a `+cu124` (or similar) build suffix and `cuda: True`.

## Configuration

### Environment variables

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | Hugging Face read token for speaker diarization |

Example (current PowerShell session):

```powershell
$env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxx"
```

### Local files (not tracked in Git)

The following paths are listed in `.gitignore` and must be maintained locally:

| File | Purpose |
|------|---------|
| `names.txt` | Authoritative list of PC names, NPCs, places, and common transcription variants |
| `prompts/gemini_recap.txt` | Gemini instructions for generating a session recap |

Copy or create these files before running the Gemini step. Update `names.txt` after each session as new characters and locations appear.

## Usage

### Pipeline overview

```text
Raw MP3
   |
   v
[1. Prepare Audio]   ─── ffmpeg chunking (1-hour segments)
   |
   v
[2. Transcribe]      ─── transcriber.py
   ├── Loops over chunks
   ├── Calls pilot_whisperx.py per chunk (argparse input/output)
   └── Merges all transcripts into one continuous-timestamp file
   |
   v
[3. Recap (manual)]  ─── Gemini Advanced + names.txt
```

### 1. Run the menu (recommended)

```powershell
.\venv\Scripts\Activate.ps1
$env:HF_TOKEN = "hf_xxxxxxxxxxxxxxxx"
.\transcriber.ps1
```

Menu options:

| Option | Description |
|--------|-------------|
| **1 — Prepare Audio** | Enter the audio file path. Extracts session name via regex, creates `chunks\session_N` folder, splits into 1-hour segments with ffmpeg. |
| **2 — Transcribe Audio** | Enter the chunks directory path. Runs `transcriber.py` which transcribes all chunks via whisperx, then merges into `sessionN_merged_whisperx.txt`. |
| **3 — Exit** | |

### 2. Transcribe directly (advanced)

Process a single chunk with `pilot_whisperx.py`:

```powershell
python pilot_whisperx.py "input.mp3" "output.txt"
```

Process all chunks and merge with `transcriber.py`:

```powershell
python transcriber.py "J:\DnD Sessions audio\chunks\session_N"
```

Flags:

| Flag | Description |
|------|-------------|
| `--dry-run` | Print what would be done without running whisperx |
| `--merge-only` | Skip transcribing, just merge existing transcript files |

### Settings (pilot_whisperx.py)

| Setting | Value |
|---------|-------|
| Model | `large-v3` |
| Language | `es` |
| Device | `cuda` |
| Compute type | `int8_float16` |
| Batch size | `8` (reduce to `4` if VRAM runs out) |

Output format (one line per segment):

```text
[0128.51] SPEAKER_02: Narration or dialogue text...
```

Monitor GPU usage during long runs:

```powershell
nvidia-smi -l 2
```

Close GPU-intensive desktop applications before transcribing multi-hour sessions to avoid VRAM pressure on 8 GB cards.

### 3. Generate a recap (Gemini Advanced)

This step is manual and uses a personal Gemini Advanced subscription (no API integration in this repository).

1. Upload the WhisperX transcript (`.txt`).
2. Upload `names.txt`.
3. Paste the contents of `prompts/gemini_recap.txt` into the chat.
4. Review and lightly edit the generated recap (name corrections, lore details).
5. Save the result as a Markdown file (for example `Session_1_recap.md`).

The prompt requests sections for summary, key events, NPCs, combat, social scenes, open plot threads, and detected transcription errors.

## Project structure

```text
DnD-audio-transcriber/
  transcriber.ps1        # PowerShell menu: Prepare Audio → Transcribe → Exit
  transcriber.py         # Orchestrator: loops chunks, transcribes, merges
  pilot_whisperx.py      # WhisperX single-file transcribe + diarize (argparse CLI)
  requirements.txt       # Python dependencies (WhisperX)
  names.txt              # Local campaign glossary (gitignored)
  prompts/
    gemini_recap.txt     # Local Gemini prompt template (gitignored)
  venv/                  # Virtual environment (gitignored)
```

Session audio and transcripts are stored outside the repository (for example on a dedicated drive).

## Development notes

### Lessons from initial testing

- The legacy `openai-whisper` CLI on CPU produced poor throughput (on the order of hours for short samples). CUDA PyTorch inside the project `venv` is required for practical runtimes.
- On 8 GB VRAM, `large-v3` can consume most available GPU memory. Reducing `BATCH_SIZE` or closing other GPU applications improves stability.
- Must delete models between steps (`del model`, `gc.collect()`, `torch.cuda.empty_cache()`) to free VRAM for diarization on 8 GB cards.
- Use `compute_type="int8_float16"` to reduce memory usage without significant quality loss.
- WhisperX diarization uses `token=`, not the deprecated `use_auth_token=` parameter.
- Speaker labels (`SPEAKER_XX`) are not character names; map speakers to PCs and the DM using context and `names.txt`.
- Gemini recaps reached roughly 80% accuracy on a 10-minute pilot after glossary tuning; `names.txt` is the primary lever for improving name and place spelling.
- PowerShell requires function definitions before their first call (unlike Python).
- Zero-padded chunk names (`%02d`) ensure reliable alphabetical sort order for merging.
- Offset-based merge (3600s per chunk) produces human-readable continuous timestamps without reading file tails.

### Roadmap

- [x] Run a full-length session transcription (3--4 hours)
- [x] Promote `pilot_whisperx.py` into a configurable CLI (`transcriber.py`)
- [x] Audio chunking for very long sessions on 8 GB GPUs
- [ ] Finalize `names.txt` for the current campaign
- [ ] Process remaining sessions (3 through N)
- [ ] Auto-upload transcripts to Notion campaign database

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
