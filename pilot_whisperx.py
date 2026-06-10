import os
import whisperx

AUDIO =r"C:\Users\mogur\Documents\Audacity\Test-DND-1.mp3"
OUT = r"J:\DnD Sessions audio\transcripts\Test-DND-1_whisperx.txt"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"
BATCH_SIZE = 8

hf_token = os.environ["HF_TOKEN"]

audio = whisperx.load_audio(AUDIO)
model = whisperx.load_model("large-v3", DEVICE, compute_type=COMPUTE_TYPE, language="es")
result = model.transcribe(audio, batch_size=BATCH_SIZE, language="es")

align_model, metadata = whisperx.load_align_model(language_code="es", device=DEVICE)
result = whisperx.align(result["segments"], align_model, metadata, audio, DEVICE)

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