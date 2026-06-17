import glob
from pathlib import Path
import argparse
import subprocess
import re
import sys

script_dir = Path(__file__).parent
output = Path(r"J:\DnD Sessions audio\transcripts")


parser = argparse.ArgumentParser()
parser.add_argument('directory', help="the directory where the chunk files are.")
parser.add_argument('--dry-run', action='store_true', help="print what would be done without running")
parser.add_argument('--merge-only', action='store_true', help="merges the transcripts only.")
args = parser.parse_args()

chunks = sorted(Path(args.directory).glob("*.mp3"))
output_session_name = Path(args.directory).name
cleaned_name = output_session_name.replace("_", "")

def merge_transcripts(files, output_path):
    lines = []
    for i, file_path in enumerate(files):
        offset = 3600 * i
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\[(\d+\.\d+)\]\s*(.*)', line)
                if m:
                    ts = float(m.group(1)) + offset
                    lines.append(f"[{ts:07.2f}] {m.group(2)}")
                else:
                    lines.append(line.rstrip())
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Merged {len(lines)} lines -> {output_path}")

if args.dry_run:
    print("[PRINT MODE] This will execute the dry run.")
    for chunk in chunks:
        transcribed_file = output / f"{cleaned_name}_{chunk.stem}_whisperx.txt"
        print(f"[DRY RUN] python {script_dir / 'pilot_whisperx.py'} {chunk} {transcribed_file}")
    print(f"[DRY RUN] Would merge: {output / f'{cleaned_name}_merged_whisperx.txt'}")
    print(f"The transcripted file is located at {transcribed_file}")

elif args.merge_only:
    print("[MERGE ONLY] This will only merge existing transcripts only")
    transcript_files = sorted(output.glob(f"{cleaned_name}_*_whisperx.txt"))
    merge_transcripts(transcript_files, output / f"{cleaned_name}_merged_whisperx.txt")

else:
    print("[FULL MODE] This will run transcript and merge")
    for chunk in chunks:
        transcribed_file = output / f"{cleaned_name}_{chunk.stem}_whisperx.txt"
        subprocess.run([sys.executable, str(script_dir / "pilot_whisperx.py"), str(chunk), str(transcribed_file)])
    transcript_files = sorted(output.glob(f"{cleaned_name}_*_whisperx.txt"))
    merge_transcripts(transcript_files, output / f"{cleaned_name}_merged_whisperx.txt")
    print(f"The transcripted file is located at {transcribed_file}")


