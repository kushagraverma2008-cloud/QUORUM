import os
import sys
import json
import re
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

TRANSCRIPTS_DIR = BASE_DIR / "data" / "raw_transcripts"
DISTILLED_DIR = BASE_DIR / "data" / "distilled_profiles"
DISTILLED_DIR.mkdir(parents=True, exist_ok=True)
CATALOG_FILE = BASE_DIR / "src" / "quorum" / "data" / "expert_catalog.json"

from distill_knowledge import distill_transcript_with_gemini

def run_batch_distillation(force_overwrite: bool = True):
    print("============================================================", flush=True)
    print("[*] QUORUM - BATCH KNOWLEDGE DISTILLATION (PHASE 3)", flush=True)
    print("============================================================", flush=True)

    transcript_files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".txt") and not f.startswith("temp_")]
    print(f"Found {len(transcript_files)} raw transcripts to distill into structured knowledge.\n", flush=True)

    # Group by expert slug (e.g. paul_graham, brian_chesky)
    experts_map = {}
    for fname in sorted(transcript_files):
        match = re.match(r"^([a-z0-9_]+)_[0-9A-Za-z_-]{11}\.txt$", fname)
        if match:
            slug = match.group(1)
            experts_map.setdefault(slug, []).append(fname)
        else:
            slug = fname.replace(".txt", "")
            experts_map.setdefault(slug, []).append(fname)

    print(f"Distinct experts mapped: {len(experts_map)}\n", flush=True)

    distilled_count = 0
    for idx, (expert_slug, file_list) in enumerate(experts_map.items(), start=1):
        out_profile = DISTILLED_DIR / f"{expert_slug}.json"
        
        # Combine transcripts for this expert (up to 60,000 characters)
        combined_text = ""
        for fn in file_list:
            fp = TRANSCRIPTS_DIR / fn
            try:
                txt = fp.read_text(encoding="utf-8", errors="ignore")
                combined_text += f"\n--- TRANSCRIPT ({fn}) ---\n" + txt
            except Exception:
                pass

        if not combined_text.strip():
            continue

        expert_display_name = expert_slug.replace("_", " ").title()
        print(f"[{idx}/{len(experts_map)}] Distilling: {expert_display_name} ({len(file_list)} videos)...", flush=True)

        try:
            vector = distill_transcript_with_gemini(expert_slug, expert_display_name, combined_text)
            out_profile.write_text(json.dumps(vector.model_dump(), indent=2), encoding="utf-8")
            distilled_count += 1
            print(f"    [OK] Saved distilled profile -> {out_profile.name} (Principles: {len(vector.core_principles)}, Warnings: {len(vector.common_warnings)}, Quotes: {len(vector.signature_quotes)})", flush=True)
        except Exception as e:
            print(f"    [ERR] Distillation failed for {expert_slug}: {e}", flush=True)

    print("\n============================================================", flush=True)
    print(f"[SUCCESS] Phase 3 Distillation Complete! {distilled_count} profiles generated.", flush=True)
    print(f"Distilled Knowledge Directory: {DISTILLED_DIR}", flush=True)
    print("============================================================", flush=True)

if __name__ == "__main__":
    run_batch_distillation(force_overwrite=True)
