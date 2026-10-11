import os
import sys
import re
import time
import json
from pathlib import Path
import openpyxl

# Ensure UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
EXCEL_LINKS = BASE_DIR / "EXPERT_YOUTUBE_LINKS.xlsx"
TRANSCRIPTS_DIR = BASE_DIR / "data" / "raw_transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_FILE = BASE_DIR / "data" / "transcript_extraction_progress.json"

from extract_transcripts import fetch_youtube_transcript, extract_video_id

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_.]', '_', name.strip().lower())

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"completed_videos": {}, "completed_experts": {}}

def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")

def extract_all_transcripts():
    print("============================================================", flush=True)
    print("[*] QUORUM - PHASE 2 BATCH TRANSCRIPT EXTRACTION", flush=True)
    print("============================================================", flush=True)

    if not EXCEL_LINKS.exists():
        print(f"[ERROR] Links file {EXCEL_LINKS} not found! Run Phase 1 first.", flush=True)
        return

    wb = openpyxl.load_workbook(EXCEL_LINKS, data_only=True)
    progress = load_progress()
    total_experts = 0
    total_videos_processed = 0

    sheet_names = wb.sheetnames
    print(f"Loaded {len(sheet_names)} sector sheets from {EXCEL_LINKS.name}\n", flush=True)

    for s_idx, sname in enumerate(sheet_names, start=1):
        ws = wb[sname]
        rows = list(ws.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            continue

        print(f"[{s_idx}/{len(sheet_names)}] Processing Sector: '{sname}' ({len(rows)-1} experts)", flush=True)

        for r_idx, row in enumerate(rows[1:], start=1):
            if not row or len(row) < 2 or not row[1]:
                continue

            expert_name = str(row[1]).strip()
            expert_slug = sanitize_filename(expert_name)
            total_experts += 1

            # URLs are in cols 5, 7, 9 (1-indexed: 6, 8, 10)
            video_urls = []
            if len(row) > 5 and row[5] and str(row[5]).startswith("http"):
                video_urls.append(str(row[5]).strip())
            if len(row) > 7 and row[7] and str(row[7]).startswith("http"):
                video_urls.append(str(row[7]).strip())
            if len(row) > 9 and row[9] and str(row[9]).startswith("http"):
                video_urls.append(str(row[9]).strip())

            if not video_urls:
                continue

            expert_vids_done = 0
            for v_idx, url in enumerate(video_urls, start=1):
                vid_id = extract_video_id(url)
                if not vid_id:
                    continue

                if vid_id in progress["completed_videos"]:
                    expert_vids_done += 1
                    continue

                out_file = TRANSCRIPTS_DIR / f"{expert_slug}_{vid_id}.txt"
                if out_file.exists() and out_file.stat().st_size > 100:
                    progress["completed_videos"][vid_id] = str(out_file)
                    expert_vids_done += 1
                    continue

                print(f"   -> [{expert_name}] Extracting Video {v_idx}/{len(video_urls)}: {vid_id}...", flush=True)
                transcript = fetch_youtube_transcript(url, out_file)
                if transcript and len(transcript) > 100:
                    progress["completed_videos"][vid_id] = str(out_file)
                    expert_vids_done += 1
                    total_videos_processed += 1
                    print(f"      [OK] Saved {len(transcript)} chars -> {out_file.name}", flush=True)
                else:
                    print(f"      [SKIP] No English captions found for {vid_id}", flush=True)

                save_progress(progress)
                time.sleep(0.3)

            progress["completed_experts"][expert_slug] = expert_vids_done
            save_progress(progress)

    print("\n============================================================", flush=True)
    print(f"[SUCCESS] Phase 2 Extraction Complete!", flush=True)
    print(f"Total videos successfully saved: {len(progress['completed_videos'])}", flush=True)
    print(f"Transcripts stored in: {TRANSCRIPTS_DIR}", flush=True)
    print("============================================================", flush=True)

if __name__ == "__main__":
    extract_all_transcripts()
