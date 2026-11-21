import sys
import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def extract_video_id(url_or_id: str) -> str:
    if not url_or_id:
        return ""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url_or_id)
    return match.group(1) if match else url_or_id.strip()

_api_instance = YouTubeTranscriptApi()

def fetch_youtube_transcript(video_url: str, output_path: Path = None) -> str:
    vid_id = extract_video_id(video_url)
    if not vid_id:
        return ""

    # 1. Fast direct API fetch
    try:
        fetched = _api_instance.fetch(vid_id, languages=['en', 'en-US', 'en-GB'])
        text_snippets = [item['text'] if isinstance(item, dict) else item.text for item in fetched]
        full_text = " ".join(text_snippets)
        if full_text and len(full_text) > 100:
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(full_text, encoding='utf-8')
            return full_text
    except Exception:
        pass

    # 2. yt-dlp auto-sub fallback for videos with auto-generated captions
    import subprocess
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "--output", f"data/raw_transcripts/temp_{vid_id}",
        f"https://www.youtube.com/watch?v={vid_id}"
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=20)
        vtt_file = Path(f"data/raw_transcripts/temp_{vid_id}.en.vtt")
        if vtt_file.exists():
            content = vtt_file.read_text(encoding="utf-8", errors="ignore")
            cleaned = re.sub(r'<[^>]+>', '', content)
            cleaned = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', cleaned)
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(cleaned, encoding="utf-8")
            vtt_file.unlink(missing_ok=True)
            return cleaned
    except Exception:
        pass

    return ""
