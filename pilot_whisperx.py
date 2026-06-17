import os
import gc
import whisperx
import torch
import warnings
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", type=str, help="Path to input audio file")
parser.add_argument("output", type=str, help="Path to output transcript file")
args = parser.parse_args()

#AUDIO = r"J:\DnD Sessions audio\chunks\session_03\chunk_00.mp3"
#OUT = r"J:\DnD Sessions audio\transcripts\session3_chunk_00_whisperx.txt"
AUDIO = args.input
OUT = args.output
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"
BATCH_SIZE = 8

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

warnings.filterwarnings("ignore")

hf_token = os.environ["HF_TOKEN"]

audio = whisperx.load_audio(AUDIO)

# Transcribe
model = whisperx.load_model("large-v3", DEVICE, compute_type=COMPUTE_TYPE, language="es")
result = model.transcribe(audio, batch_size=BATCH_SIZE, language="es")
del model
gc.collect()
torch.cuda.empty_cache()

# Align
align_model, metadata = whisperx.load_align_model(language_code="es", device=DEVICE)
result = whisperx.align(result["segments"], align_model, metadata, audio, DEVICE)
del align_model
gc.collect()
torch.cuda.empty_cache()

# Save intermediate result without speaker labels (in case diarization fails)
lines = []
for seg in result["segments"]:
    start = seg.get("start", 0)
    text = seg.get("text", "").strip()
    if text:
        lines.append(f"[{start:07.2f}] {text}")

with open(OUT.replace(".txt", "_notdiarized.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Transcription done ({len(lines)} lines). Starting diarization...")

# Diarize on GPU (should have ~5GB free now)
diarize = whisperx.diarize.DiarizationPipeline(token=hf_token, device=DEVICE)
diarize_segments = diarize(audio)
result = whisperx.assign_word_speakers(diarize_segments, result)

lines = []
for seg in result["segments"]:
    speaker = seg.get("speaker", "UNKNOWN")
    start = seg.get("start", 0)
    text = seg.get("text", "").strip()
    if text:
        lines.append(f"[{start:07.2f}] {speaker}: {text}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote {OUT}")
print(f"Lines: {len(lines)}")