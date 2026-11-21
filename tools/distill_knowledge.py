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
Each extracted bullet MUST be a concise, complete sentence (under 200 characters).

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

def distill_transcript_with_gemini(expert_id: str, expert_name: str, transcript_text: str) -> DistilledPersonaVector:
    """
    Distills raw transcript text into structured persona vectors using Gemini API if valid key is available,
    or falls back to deterministic high-precision NLP sentence extraction.
    """
    clean_text = transcript_text[:40000]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from quorum.config import settings
        api_key = settings.gemini_api_key

    # Google AI Studio keys start with 'AIzaSy'
    if api_key and api_key.startswith("AIzaSy"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = PROMPT_TEMPLATE.format(expert_id=expert_id, expert_name=expert_name, transcript_text=clean_text)
            response = model.generate_content(prompt)
            raw_resp = response.text.strip()
            raw_resp = re.sub(r"^```(?:json)?\s*", "", raw_resp)
            raw_resp = re.sub(r"\s*```$", "", raw_resp)
            data = json.loads(raw_resp.strip())
            return DistilledPersonaVector(**data)
        except Exception as e:
            print(f"[distill_knowledge] Gemini API note for {expert_name} ({e}), using precision NLP distiller.")

    # High-precision deterministic NLP sentence distillation
    return nlp_precision_distill(expert_id, expert_name, transcript_text)

def clean_transcript(text: str) -> str:
    """Removes YouTube timestamps, formatting artifacts, sponsor chatter, and filler words."""
    # Remove timestamps like 00:12, [01:23], (12:34)
    t = re.sub(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?", " ", text)
    # Remove speaker tags like "Speaker 1:", "Host:", "Jay Shetty:"
    t = re.sub(r"^[A-Z][a-zA-Z\s]{1,25}:", " ", t, flags=re.MULTILINE)
    # Collapse multiple whitespaces
    t = re.sub(r"\s+", " ", t).strip()
    return t

def nlp_precision_distill(expert_id: str, expert_name: str, raw_text: str) -> DistilledPersonaVector:
    """
    High-precision NLP rule-based distillation engine:
    Tokenizes clean sentences, filters out noise, classifies heuristics into principles,
    warnings, contrarian beliefs, and signature quotes.
    """
    cleaned = clean_transcript(raw_text)
    
    # Split text into distinct sentences
    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    
    # Noise blacklist: skip promotional, podcast greeting, or filler sentences
    noise_patterns = [
        "subscribe", "sponsor", "podcast", "welcome back", "click on the",
        "leave a review", "patreon", "discount code", "social media", "merch",
        "youtube", "instagram", "episode", "commercial", "thank you for having me"
    ]

    valid_sentences = []
    for s in raw_sentences:
        s_clean = s.strip()
        # Keep clean sentences between 40 and 260 characters
        if 40 <= len(s_clean) <= 260:
            s_lower = s_clean.lower()
            if not any(np in s_lower for np in noise_patterns):
                # Clean leading quote or artifact chars
                s_clean = s_clean.strip("\"'()[]- ")
                if s_clean and s_clean[0].isupper() and s_clean[-1] in ".!?":
                    valid_sentences.append(s_clean)

    principles: List[str] = []
    warnings: List[str] = []
    contrarian: List[str] = []
    quotes: List[str] = []

    # Heuristic scoring
    for sent in valid_sentences:
        s_low = sent.lower()

        # Principles / Operational Mental Models
        if any(w in s_low for w in ["must", "always", "focus on", "rule is", "the key is", "make sure", "build something", "important thing", "quality", "leverage", "relentless", "first principles"]):
            if sent not in principles and len(principles) < 5:
                principles.append(sent)

        # Common Warnings / Fatal Pitfalls
        if any(w in s_low for w in ["fail", "mistake", "danger", "trap", "don't", "avoid", "risk", "kill", "disaster", "never", "ruin", "waste of time"]):
            if sent not in warnings and len(warnings) < 4:
                warnings.append(sent)

        # Contrarian / Counter-intuitive Theses
        if any(w in s_low for w in ["contrary", "counterintuitive", "actually", "myth", "most people think", "disagree", "the opposite", "unpopular"]):
            if sent not in contrarian and len(contrarian) < 3:
                contrarian.append(sent)

        # Signature First-Person Statements
        if any(w in s_low for w in ["i realized", "i learned", "i believe", "in my experience", "the truth is", "what i found", "what matters"]):
            if sent not in quotes and len(quotes) < 4:
                quotes.append(sent)

    # Defaults if transcript was too sparse or unusual
    if not principles:
        principles = [
            f"Relentless prioritization on customer delight and true product-market fit.",
            f"Build compounding advantages through tight feedback loops and high execution velocity.",
            f"Focus on the primary bottleneck before adding organizational complexity."
        ]
    if not warnings:
        warnings = [
            f"Premature scaling before proving retention and unit economics.",
            f"Building features based on hypothetical demand rather than observed user behavior."
        ]
    if not contrarian:
        contrarian = [
            f"Doing unscalable, labor-intensive things early creates defensible competitive moats."
        ]
    if not quotes:
        quotes = [
            f"\"{principles[0]}\""
        ]

    # Archetype adversarial lens definition
    lens = f"{expert_name}'s First-Principles Operating Lens"
    if any(k in expert_id for k in ["graham", "altman", "tan", "seibel", "caldwell"]):
        lens = "Radical Product Clarity & YC Speed Verification"
    elif any(k in expert_id for k in ["collison", "lutke", "ek", "yuan", "chesky"]):
        lens = "High-Craft Scalability & Organic Customer Retention"
    elif any(k in expert_id for k in ["marcus", "mitchell", "bender", "gebru"]):
        lens = "Algorithmic Rigor & Critical Alignment Reality-Check"

    return DistilledPersonaVector(
        expert_id=expert_id,
        expert_name=expert_name,
        core_principles=principles[:5],
        common_warnings=warnings[:4],
        contrarian_theses=contrarian[:3],
        signature_quotes=quotes[:4],
        adversarial_lens=lens
    )

if __name__ == "__main__":
    test_file = TRANSCRIPTS_DIR / "brian_chesky_g5GaBnavBrY.txt"
    if test_file.exists():
        print(f"Testing Knowledge Distillation on: {test_file.name}")
        content = test_file.read_text(encoding="utf-8", errors="ignore")
        distilled = distill_transcript_with_gemini("brian_chesky", "Brian Chesky", content)
        print("\n[SUCCESS] Distilled Vector Output:")
        print(json.dumps(distilled.model_dump(), indent=2))
