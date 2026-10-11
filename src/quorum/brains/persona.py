from typing import Dict, Any
from quorum.schemas.expert import ExpertProfile
from quorum.schemas.idea import IdeaBrief

class PersonaPromptBuilder:
    """Builds strict, grounded persona prompts for Gemini evaluations."""

    @staticmethod
    def build_evaluation_prompt(expert: ExpertProfile, brief: IdeaBrief) -> str:
        principles_txt = "\n".join(f"- {p}" for p in expert.core_principles[:5]) if expert.core_principles else "- Rely on fundamental first-principles of " + expert.primary_sector
        warnings_txt = "\n".join(f"- {w}" for w in expert.common_warnings[:4]) if expert.common_warnings else "- Avoid unvalidated assumptions and premature scaling"
        heuristics_txt = "\n".join(f"- {h}" for h in expert.decision_heuristics[:4]) if expert.decision_heuristics else "- Look for authentic founder-market fit and tangible proof"
        contrarian_txt = "\n".join(f"- {c}" for c in expert.contrarian_theses[:3]) if expert.contrarian_theses else "- Standard playbook rarely produces outlier returns"
        quotes_txt = "\n".join(f"- \"{q}\"" for q in expert.signature_quotes[:3]) if expert.signature_quotes else "- Look for clear evidence of genuine user love"
        sources_txt = "\n".join(f"- {s}" for s in expert.high_value_sources[:4]) if expert.high_value_sources else "- Documented public interviews and operating lessons"

        prompt = f"""You are acting as the AI Digital Persona of {expert.name} ({expert.role_or_title or expert.primary_sector}).
Your evaluation MUST strictly reflect your documented thinking, mental models, and principles.

=== YOUR AUTHENTIC KNOWLEDGE BASE ===
PRIMARY SECTOR: {expert.primary_sector}
EVALUATION ARCHETYPE: {expert.stance_archetype}
ADVERSARIAL LENS: {expert.adversarial_lens or expert.stance_archetype}

CORE PRINCIPLES YOU LIVE BY:
{principles_txt}

CRITICAL WARNINGS & PITFALLS YOU REPEATEDLY HIGHLIGHT:
{warnings_txt}

CONTRARIAN THESES YOU HOLD:
{contrarian_txt}

SIGNATURE AUTHENTIC QUOTES:
{quotes_txt}

DECISION HEURISTICS YOU USE TO JUDGE VENTURES:
{heuristics_txt}

HIGH-VALUE PUBLIC SOURCES TO REFERENCE/CITE:
{sources_txt}


=== THE VENTURE TO EVALUATE ===
Title: {brief.title}
One-Liner: {brief.one_liner}
Problem: {brief.problem_statement}
Target Customer: {brief.target_customer}
Solution: {brief.solution_description}
Revenue Model: {brief.revenue_model}
Key Assumptions: {", ".join(brief.key_assumptions)}
Stage / Context: Stage: {brief.context.stage}, Market: {brief.context.target_market}, Geography: {brief.context.geography}, Budget: {brief.context.budget}

=== STRICT EVALUATION GUIDELINES ===
1. BRUTAL TRUTH OVER POLITENESS: Identify weaknesses, flaws, and naive assumptions first.
2. CITATION REQUIREMENT: Ground your reasoning in your real-world philosophies or public talks.
3. 8 PILLAR RATINGS (Each score MUST be a float from 0.0 to 10.0, where 10 is the best / safest):
   - market_demand: Is there a real, reachable customer need?
   - differentiation: Is there an unfair advantage or defensible moat?
   - feasibility: Can it be realistically built and delivered with available resources?
   - financial_viability: Unit economics, margins, and path to sustainable cashflow.
   - execution_risk: Team/operational risk safety (10.0 = low risk/safest, 0.0 = lethal risk).
   - regulatory_legal_risk: Compliance/legal safety (10.0 = low risk/safest, 0.0 = massive liability).
   - market_timing: Why is now the right time, or is it too early/late?
   - defensibility_scale: Can it compound and resist copycats at scale?
4. OVERALL SCORE: Relevance-weighted 0.0 to 10.0.
5. VERDICT LABEL: Exactly one of: 'Strong', 'Promising', 'Risky', 'Not viable'.
6. KILL QUESTION: The single hardest question that could instantly sink this startup if unanswered.
7. FIRST QUESTION TO FOUNDER: What you would look them in the eye and ask first.

Return your response in pure JSON format matching this schema:
{{
  "overall_score": 6.5,
  "verdict_label": "Risky",
  "pillar_ratings": {{
    "market_demand": 7.0,
    "differentiation": 5.0,
    "feasibility": 8.0,
    "financial_viability": 6.0,
    "execution_risk": 5.5,
    "regulatory_legal_risk": 9.0,
    "market_timing": 7.5,
    "defensibility_scale": 4.5
  }},
  "opinion_critique": "Your detailed, unvarnished critique in the direct voice of {expert.name}...",
  "specific_warnings": ["Warning 1", "Warning 2"],
  "actionable_tips": ["Actionable tip 1", "Actionable tip 2"],
  "kill_question": "Your lethal question here...",
  "first_question_to_founder": "What you ask them first...",
  "cited_sources": ["Name of talk/book/principle cited"]
}}
"""
        return prompt

    @staticmethod
    def build_chat_prompt(expert: ExpertProfile, conversation_history: list[dict], user_message: str) -> str:
        history_txt = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in conversation_history[-6:])
        quote_hint = f"\nYOUR AUTHENTIC VOICE/QUOTE: \"{expert.signature_quotes[0]}\"" if expert.signature_quotes else ""
        contrarian_hint = f"\nYOUR CONTRARIAN THESIS: \"{expert.contrarian_theses[0]}\"" if expert.contrarian_theses else ""
        lens_hint = f"\nYOUR JUDGMENT LENS: {expert.adversarial_lens or expert.stance_archetype}"

        return f"""You are the AI persona of {expert.name} ({expert.role_or_title or expert.primary_sector}).
Engage with the founder in your authentic, documented style. Give direct, high-signal, actionable feedback.
Ground your answers in your published experiences and principles. Do NOT invent claims outside your domain.{lens_hint}{quote_hint}{contrarian_hint}

CONVERSATION CONTEXT:
{history_txt}

FOUNDER SAYS:
{user_message}

Respond directly as {expert.name}:"""

