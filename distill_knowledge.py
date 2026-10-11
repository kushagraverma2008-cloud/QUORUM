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
CATALOG_FILE = BASE_DIR / "src" / "quorum" / "data" / "expert_catalog.json"
DISTILLED_DIR = BASE_DIR / "data" / "distilled_profiles"
DISTILLED_DIR.mkdir(parents=True, exist_ok=True)

class DistilledPersonaVector(BaseModel):
    expert_id: str
    expert_name: str
    core_principles: List[str] = Field(..., description="Top 3-5 operational/mental models they repeat")
    common_warnings: List[str] = Field(..., description="Top 3 fatal failure modes/red flags they flag")
    contrarian_theses: List[str] = Field(default_factory=list, description="Unique counter-intuitive beliefs")
    signature_quotes: List[str] = Field(default_factory=list, description="Memorable authentic statements")
    adversarial_lens: str = Field(..., description="Concise description of their analytical judgment lens")

PROMPT_TEMPLATE = """You are the Knowledge Distillation Engine for QUORUM, an elite startup advisory council.
Below is the raw spoken transcript from a podcast, keynote, or interview featuring: {expert_name}.

Extract this expert's genuine business philosophy, evaluation heuristics, and recurring warnings. 
Filter out ALL pleasantries, host chatter, jokes, and introductory remarks. Keep ONLY high-density startup reality.

Return ONLY valid JSON matching this schema:
{{
  "expert_id": "{expert_id}",
  "expert_name": "{expert_name}",
  "core_principles": [
    "First principles heuristic 1...",
    "First principles heuristic 2..."
  ],
  "common_warnings": [
    "Fatal failure mode 1...",
    "Fatal failure mode 2..."
  ],
  "contrarian_theses": [
    "Contrarian thesis 1..."
  ],
  "signature_quotes": [
    "Verbatim authentic insight quote 1..."
  ],
  "adversarial_lens": "e.g. Radical Simplicity & Organic Product Obsession"
}}

RAW TRANSCRIPT EXCERPT:
{transcript_text}
"""

def distill_transcript_with_gemini(expert_id: str, expert_name: str, transcript_text: str):
    """
    Distills raw transcript text into structured persona vectors using Gemini 2.5/2.0 Flash.
    """
    # Truncate to first 40,000 characters if exceptionally long (approx 10,000 tokens)
    clean_text = transcript_text[:40000]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from quorum.config import settings
        api_key = settings.gemini_api_key

    if not api_key:
        print(f"[WARN] No GEMINI_API_KEY set. Falling back to heuristic distillation for {expert_name}.")
        return heuristic_distill(expert_id, expert_name, clean_text)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = PROMPT_TEMPLATE.format(expert_id=expert_id, expert_name=expert_name, transcript_text=clean_text)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw_resp = response.text.strip()
        # Clean markdown codeblocks
        if raw_resp.startswith("```json"):
            raw_resp = raw_resp[7:]
        if raw_resp.endswith("```"):
            raw_resp = raw_resp[:-3]
        data = json.loads(raw_resp.strip())
        return DistilledPersonaVector(**data)
    except Exception as e:
        print(f"[WARN] Gemini distillation error for {expert_name} ({e}), using heuristic parser.")
        return heuristic_distill(expert_id, expert_name, clean_text)

def heuristic_distill(expert_id: str, expert_name: str, text: str) -> DistilledPersonaVector:
    """Local extraction fallback if offline or API key missing."""
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
    principles = []
    warnings = []
    for line in lines:
        l_lower = line.lower()
        if any(w in l_lower for w in ["important", "rule", "must", "always", "focus", "need to"]):
            if len(principles) < 4:
                principles.append(line.strip())
        if any(w in l_lower for w in ["fail", "mistake", "wrong", "trap", "danger", "don't", "kill"]):
            if len(warnings) < 4:
                warnings.append(line.strip())

    return DistilledPersonaVector(
        expert_id=expert_id,
        expert_name=expert_name,
        core_principles=principles or ["Relentless prioritization on product quality and customer retention."],
        common_warnings=warnings or ["Premature scaling and lack of focus before proving product-market fit."],
        contrarian_theses=["Market dynamics always overwhelm individual operational speed."],
        signature_quotes=[],
        adversarial_lens=f"{expert_name}'s First-Principles Lens"
    )

if __name__ == "__main__":
    test_file = TRANSCRIPTS_DIR / "brian_chesky_g5GaBnavBrY.txt"
    if test_file.exists():
        print(f"Testing Knowledge Distillation on: {test_file.name}")
        content = test_file.read_text(encoding="utf-8", errors="ignore")
        distilled = distill_transcript_with_gemini("brian_chesky", "Brian Chesky", content)
        print("\n[SUCCESS] Distilled Vector Output:")
        print(json.dumps(distilled.model_dump(), indent=2))
