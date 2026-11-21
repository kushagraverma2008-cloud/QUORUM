import os
import sys
import time
import urllib.parse
import urllib.request
import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE_DIR = Path(__file__).resolve().parent
EXCEL_INPUT = BASE_DIR / "EXPERT LIST.xlsx"
EXCEL_OUTPUT = BASE_DIR / "EXPERT_YOUTUBE_LINKS.xlsx"

def search_youtube_videos(query: str, max_results: int = 3):
    """
    Search authentic YouTube interviews/podcasts for an expert using ytsearch.
    Uses yt-dlp to extract authentic long-form video IDs and titles.
    """
    import subprocess
    cmd = [
        sys.executable, "-m", "yt_dlp",
        f"ytsearch{max_results}:{query}",
        "--flat-playlist",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        "--ignore-errors"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            entries = data.get("entries", [])
            results = []
            for item in entries:
                if not item:
                    continue
                vid_id = item.get("id")
                title = item.get("title")
                url = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None
                if url:
                    results.append({"title": title, "url": url, "id": vid_id})
            return results
    except Exception as e:
        print(f"    [WARN] Search error for '{query}': {e}")
    return []

def harvest_sector(sheet_name: str, max_experts_limit: int = None):
    print(f"\n==================================================")
    print(f"[*] Processing Sector: {sheet_name}")
    print(f"==================================================")

    wb_in = openpyxl.load_workbook(EXCEL_INPUT, data_only=True)
    if sheet_name not in wb_in.sheetnames:
        print(f"Sheet {sheet_name} not found in {EXCEL_INPUT}")
        return

    ws_in = wb_in[sheet_name]
    rows = list(ws_in.iter_rows(values_only=True))
    if not rows or len(rows) < 2:
        return

    # Create or load output workbook
    if EXCEL_OUTPUT.exists():
        wb_out = openpyxl.load_workbook(EXCEL_OUTPUT)
    else:
        wb_out = openpyxl.Workbook()
        # remove default sheet if new
        if "Sheet" in wb_out.sheetnames:
            wb_out.remove(wb_out["Sheet"])

    if sheet_name in wb_out.sheetnames:
        ws_out = wb_out[sheet_name]
    else:
        ws_out = wb_out.create_sheet(title=sheet_name[:31])
        # Format headers
        headers = [
            "Index", "Expert Name", "Domain / Subdomains", "Content Focus",
            "Video 1 Title", "Video 1 URL",
            "Video 2 Title", "Video 2 URL",
            "Video 3 Title", "Video 3 URL",
            "Harvest Status"
        ]
        ws_out.append(headers)
        # Style Header
        header_fill = PatternFill(start_color="0A111F", end_color="0A111F", fill_type="solid")
        header_font = Font(name="Arial", size=10, bold=True, color="00E5FF")
        for col_num in range(1, len(headers) + 1):
            cell = ws_out.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

    existing_experts = set()
    for row in ws_out.iter_rows(min_row=2, values_only=True):
        if row and row[1]:
            existing_experts.add(str(row[1]).strip().lower())

    processed_count = 0
    for r_idx, row in enumerate(rows[1:], start=1):
        if not row or len(row) < 2 or not row[1]:
            continue

        expert_name = str(row[1]).strip()
        if expert_name.lower() in existing_experts:
            continue

        domain_info = str(row[2]) if len(row) > 2 and row[2] else ""
        content_focus = str(row[3]) if len(row) > 3 and row[3] else ""

        query = f'"{expert_name}" (interview OR podcast OR speech OR talk)'
        print(f" -> [{r_idx}] Searching authentic video for: {expert_name}...")
        videos = search_youtube_videos(query, max_results=3)

        v1_t, v1_u = (videos[0]["title"], videos[0]["url"]) if len(videos) > 0 else ("", "")
        v2_t, v2_u = (videos[1]["title"], videos[1]["url"]) if len(videos) > 1 else ("", "")
        v3_t, v3_u = (videos[2]["title"], videos[2]["url"]) if len(videos) > 2 else ("", "")

        status = f"FOUND {len(videos)} VIDEOS" if len(videos) >= 2 else "PARTIAL"

        ws_out.append([
            r_idx, expert_name, domain_info, content_focus,
            v1_t, v1_u,
            v2_t, v2_u,
            v3_t, v3_u,
            status
        ])
        existing_experts.add(expert_name.lower())
        processed_count += 1
        wb_out.save(EXCEL_OUTPUT)
        time.sleep(0.5)

        if max_experts_limit and processed_count >= max_experts_limit:
            print(f"[+] Reached batch limit of {max_experts_limit} for sheet {sheet_name}")
            break

    wb_out.save(EXCEL_OUTPUT)
    print(f"[SUCCESS] Completed sector '{sheet_name}'. Harvested {processed_count} profiles. Output saved to {EXCEL_OUTPUT.name}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="QUORUM - Phase 1 YouTube Harvester")
    parser.add_argument("--sheet", type=str, default="technology and software", help="Sheet name to process")
    parser.add_argument("--limit", type=int, default=10, help="Max experts to harvest in this batch")
    args = parser.parse_args()

    harvest_sector(args.sheet, args.limit)
