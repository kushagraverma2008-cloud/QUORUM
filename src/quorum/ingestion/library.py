import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from quorum.schemas.expert import ExpertProfile
from quorum.config import settings

class LibraryIngestor:
    """Parses Word document advice libraries and enriches expert profiles."""

    @classmethod
    def parse_advice_docx(cls, docx_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        path = docx_path or settings.docx_library_path
        if not path.exists():
            return {}

        import docx
        doc = docx.Document(str(path))
        
        advice_by_expert: Dict[str, Dict[str, Any]] = {}
        current_expert = None
        current_section = None
        
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            # Check if this paragraph is a Heading 1 (expert name)
            if p.style.name.startswith("Heading 1"):
                current_expert = text
                current_section = None
                if current_expert not in advice_by_expert:
                    advice_by_expert[current_expert] = {
                        "name": current_expert,
                        "topics": [],
                        "sources": [],
                        "advice": [],
                        "warnings": [],
                        "questions": []
                    }
                continue

            if not current_expert:
                continue

            data = advice_by_expert[current_expert]

            if text.startswith("Video:"):
                data["sources"].append(text.replace("Video:", "").strip())
                continue
            elif "Advice and takeaways" in text:
                current_section = "advice"
                continue
            elif "Warnings and conditions" in text:
                current_section = "warnings"
                continue
            elif "Questions to apply to an idea" in text:
                current_section = "questions"
                continue
            elif not current_section and not data["topics"]:
                data["topics"].append(text)
                continue

            if current_section == "advice":
                data["advice"].append(text)
            elif current_section == "warnings":
                data["warnings"].append(text)
            elif current_section == "questions":
                data["questions"].append(text)

        return advice_by_expert

    @classmethod
    def enrich_profiles(
        cls, 
        profiles: List[ExpertProfile], 
        advice_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[ExpertProfile]:
        advice_map = advice_data if advice_data is not None else cls.parse_advice_docx()

        # Predefined rich foundational profiles for major tech/seed icons if docx is small
        foundational_wisdom = {
            "paul_graham": {
                "role": "Co-founder, Y Combinator",
                "principles": [
                    "Make something people want.",
                    "Do things that don't scale at the beginning.",
                    "Look for ideas that are at the intersection of what is possible now and what looks like a toy.",
                    "Live in the future, then build what's missing."
                ],
                "warnings": [
                    "Beware of 'schlep blindness' — founders instinctively avoid tedious, messy problems where the biggest opportunities hide.",
                    "Beware of solving problems you don't personally have or understand intimately.",
                    "Do not scale marketing before reaching undeniable product-market fit."
                ],
                "heuristics": [
                    "Is the problem hair-on-fire urgent for a small initial group?",
                    "Are the founders formidable, relentless, and obsessively curious?"
                ],
                "questions": [
                    "Who wants this so urgently that they would use a broken prototype?",
                    "What makes this problem hard enough that incumbents have avoided it?"
                ]
            },
            "michael_seibel": {
                "role": "Managing Director YC / Co-founder Twitch & Socialcam",
                "principles": [
                    "Launch quickly and talk to users every single day.",
                    "Solve a specific problem for specific users; do not build horizontal platforms early.",
                    "Simple product, clear value metric, relentless iteration."
                ],
                "warnings": [
                    "Avoid endless feature development without customer feedback loops.",
                    "A small team loses momentum when nobody owns fast decision-making."
                ],
                "heuristics": [
                    "Can the founder find their first 10 customers without spending a dollar on ads?",
                    "Is the core value delivery measurable in the first session?"
                ],
                "questions": [
                    "Why are you qualified to work on this problem?",
                    "Who will use the first version, and how will you reach them next week?"
                ]
            },
            "dalton_caldwell": {
                "role": "Managing Director, Y Combinator",
                "principles": [
                    "Clarity over buzzwords. If you can't explain it simply, you don't understand it.",
                    "Evidence trumps aspiration. Show what users actually did, not what they might do.",
                    "Relentless focus on the primary constraint."
                ],
                "warnings": [
                    "Do not confuse vanity metrics or waitlist signups with real commitment.",
                    "Do not build solutions looking for problems."
                ],
                "heuristics": [
                    "Does the pitch separate facts from optimistic hypotheses?"
                ],
                "questions": [
                    "Does the story show hard evidence or only founder aspiration?",
                    "What is the single biggest risk that could kill this venture in 90 days?"
                ]
            },
            "geoff_ralston": {
                "role": "Former President, Y Combinator",
                "principles": [
                    "Startups survive through sheer relentless persistence and rapid adaptation.",
                    "Focus entirely on speaking with customers and writing code."
                ],
                "warnings": [
                    "Beware of premature optimization, excessive hiring, or burning cash on brand marketing."
                ],
                "heuristics": [
                    "Is the founder in touch with the cold reality of customer demand?"
                ],
                "questions": [
                    "What evidence says that people want this right now?",
                    "What will you do next week that gets the product closer to paying users?"
                ]
            },
            "tobi_lutke": {
                "role": "Founder & CEO, Shopify",
                "principles": [
                    "Build tooling that empowers the underdog.",
                    "Focus on high-craft execution and scalable systems architecture.",
                    "Make the simple easy and the complex possible."
                ],
                "warnings": [
                    "Beware of building for enterprise gatekeepers before mastering the core end-user workflow."
                ],
                "heuristics": [
                    "Can this product create an ecosystem where third parties make money building on it?"
                ],
                "questions": [
                    "Does this product remove friction or merely add another abstraction?"
                ]
            },
            "sam_altman": {
                "role": "CEO OpenAI / Former President YC",
                "principles": [
                    "A small group of users who love your product is infinitely better than a million who merely like it.",
                    "Exponential curves feel flat at first. Bet on compounding advantages.",
                    "Focus, speed, and execution velocity define winner-take-all markets."
                ],
                "warnings": [
                    "Beware of being a fast follower in a declining paradigm.",
                    "Avoid hiring for vanity; small, intense teams win."
                ],
                "heuristics": [
                    "Does this venture benefit from compounding data, compute, or network loops?"
                ],
                "questions": [
                    "Why will this be 10x better than existing solutions, not just 10% cheaper?"
                ]
            }
        }

        for p in profiles:
            # Check parsed docx advice
            matched_docx = None
            for exp_name, data in advice_map.items():
                if exp_name.lower() in p.name.lower() or p.name.lower() in exp_name.lower():
                    matched_docx = data
                    break

            if matched_docx:
                p.core_principles.extend(matched_docx.get("advice", []))
                p.common_warnings.extend(matched_docx.get("warnings", []))
                p.first_questions.extend(matched_docx.get("questions", []))
                p.high_value_sources.extend(matched_docx.get("sources", []))

            # Check foundational wisdom catalog
            if p.id in foundational_wisdom:
                w = foundational_wisdom[p.id]
                p.role_or_title = w.get("role", p.role_or_title)
                for pr in w.get("principles", []):
                    if pr not in p.core_principles:
                        p.core_principles.append(pr)
                for wr in w.get("warnings", []):
                    if wr not in p.common_warnings:
                        p.common_warnings.append(wr)
                for he in w.get("heuristics", []):
                    if he not in p.decision_heuristics:
                        p.decision_heuristics.append(he)
                for qu in w.get("questions", []):
                    if qu not in p.first_questions:
                        p.first_questions.append(qu)

        return profiles

    @classmethod
    def save_advice_library_json(cls, output_path: Optional[Path] = None) -> Path:
        out = output_path or (settings.data_dir / "advice_library.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        advice = cls.parse_advice_docx()
        with open(out, "w", encoding="utf-8") as f:
            json.dump(advice, f, indent=2, ensure_ascii=False)
        return out
