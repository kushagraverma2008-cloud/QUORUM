import os
import sys
import time
import json
import subprocess
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
EXCEL_INPUT = BASE_DIR / "EXPERT LIST.xlsx"
EXCEL_OUTPUT = BASE_DIR / "EXPERT_YOUTUBE_LINKS.xlsx"

def search_youtube_videos(query: str, max_results: int = 3):
    """
    Search authentic YouTube interviews/podcasts for an expert using ytsearch.
    Uses yt-dlp to extract authentic long-form video IDs and titles.
    """
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
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
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
        print(f"    [WARN] Search error for '{query}': {e}", flush=True)
    return []

def get_or_create_output_wb():
    if EXCEL_OUTPUT.exists():
        return openpyxl.load_workbook(EXCEL_OUTPUT)
    wb = openpyxl.Workbook()
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])
    return wb

def harvest_all_sectors():
    print(f"============================================================", flush=True)
    print(f"[*] QUORUM - FULL CATALOG YOUTUBE HARVESTER (ALL EXPERTS)", flush=True)
    print(f"============================================================", flush=True)

    wb_in = openpyxl.load_workbook(EXCEL_INPUT, data_only=True)
    sheet_names = wb_in.sheetnames
    print(f"Found {len(sheet_names)} sector sheets in {EXCEL_INPUT.name}\n", flush=True)

    wb_out = get_or_create_output_wb()
    total_harvested_session = 0

    for s_idx, sheet_name in enumerate(sheet_names, start=1):
        clean_sheet_title = sheet_name.strip()[:31]
        print(f"\n[{s_idx}/{len(sheet_names)}] Processing Sector: '{clean_sheet_title}'", flush=True)

        ws_in = wb_in[sheet_name]
        rows = list(ws_in.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            print(f"    [SKIP] Empty sheet: {sheet_name}", flush=True)
            continue

        if clean_sheet_title in wb_out.sheetnames:
            ws_out = wb_out[clean_sheet_title]
        else:
            ws_out = wb_out.create_sheet(title=clean_sheet_title)
            headers = [
                "Index", "Expert Name", "Domain / Subdomains", "Content Focus",
                "Video 1 Title", "Video 1 URL",
                "Video 2 Title", "Video 2 URL",
                "Video 3 Title", "Video 3 URL",
                "Harvest Status"
            ]
            ws_out.append(headers)
            header_fill = PatternFill(start_color="0A111F", end_color="0A111F", fill_type="solid")
            header_font = Font(name="Arial", size=10, bold=True, color="00E5FF")
            for col_num in range(1, len(headers) + 1):
                cell = ws_out.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

        # Track experts already harvested
        existing_experts = set()
        for r in ws_out.iter_rows(min_row=2, values_only=True):
            if r and len(r) > 1 and r[1]:
                existing_experts.add(str(r[1]).strip().lower())

        sheet_harvested = 0
        for r_idx, row in enumerate(rows[1:], start=1):
            if not row or len(row) < 2 or not row[1]:
                continue

            expert_name = str(row[1]).strip()
            if expert_name.lower() in existing_experts:
                continue

            domain_info = str(row[2]) if len(row) > 2 and row[2] else ""
            content_focus = str(row[3]) if len(row) > 3 and row[3] else ""

            query = f'"{expert_name}" (interview OR podcast OR keynote OR talk)'
            print(f"  -> [{r_idx}/{len(rows)-1}] Harvesting: {expert_name}...", flush=True)
            videos = search_youtube_videos(query, max_results=3)

            v1_t, v1_u = (videos[0]["title"], videos[0]["url"]) if len(videos) > 0 else ("", "")
            v2_t, v2_u = (videos[1]["title"], videos[1]["url"]) if len(videos) > 1 else ("", "")
            v3_t, v3_u = (videos[2]["title"], videos[2]["url"]) if len(videos) > 2 else ("", "")

            status = f"FOUND {len(videos)} VIDEOS" if len(videos) >= 2 else ("PARTIAL (1)" if len(videos) == 1 else "NO_LINKS")

            ws_out.append([
                r_idx, expert_name, domain_info, content_focus,
                v1_t, v1_u,
                v2_t, v2_u,
                v3_t, v3_u,
                status
            ])
            existing_experts.add(expert_name.lower())
            sheet_harvested += 1
            total_harvested_session += 1

            # Save incrementally after every profile
            wb_out.save(EXCEL_OUTPUT)
            time.sleep(0.4)

        wb_out.save(EXCEL_OUTPUT)
        print(f"    [COMPLETED] '{clean_sheet_title}': {sheet_harvested} new profiles added.", flush=True)

    print(f"\n============================================================", flush=True)
    print(f"[SUCCESS] Full catalog run complete! Total added: {total_harvested_session}", flush=True)
    print(f"Output saved to: {EXCEL_OUTPUT}", flush=True)
    print(f"============================================================", flush=True)

if __name__ == "__main__":
    harvest_all_sectors()
