import json
import re
import os
from typing import Dict, Any, Optional
from quorum.config import settings
from quorum.schemas.expert import ExpertProfile
from quorum.schemas.idea import IdeaBrief
from quorum.schemas.evaluation import ExpertVerdict, PillarScores
from quorum.brains.persona import PersonaPromptBuilder

class GeminiBrainAdapter:
    """Adapter for Google Gemini API (2.5-flash / 2.0-flash) with robust error handling and fallback."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self._init_client()

    def _init_client(self):
        self.client_ready = False
        if not self.api_key or self.api_key.startswith("your_"):
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": settings.gemini_temperature,
                    "top_p": settings.gemini_top_p,
                    "max_output_tokens": settings.gemini_max_tokens,
                    "response_mime_type": "application/json"
                }
            )
            self.client_ready = True
        except Exception as e:
            print(f"[GeminiBrainAdapter] Warning: Could not initialize Gemini SDK ({e}). Running in offline evaluation mode.")
            self.client_ready = False

    def evaluate_expert(self, expert: ExpertProfile, brief: IdeaBrief) -> ExpertVerdict:
        prompt = PersonaPromptBuilder.build_evaluation_prompt(expert, brief)

        if self.client_ready:
            try:
                response = self.model.generate_content(prompt)
                raw_text = response.text.strip()
                # Clean any markdown blocks
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
                cleaned = re.sub(r"\s*```$", "", cleaned)
                data = json.loads(cleaned)
                return self._parse_verdict_data(expert, data)
            except Exception as e:
                print(f"[GeminiBrainAdapter] Live API call failed for {expert.name}: {e}. Falling back to grounded heuristic evaluation.")

        # Grounded heuristic evaluation mode (offline fallback / mock mode)
        return self._heuristic_expert_evaluation(expert, brief)

    def chat_follow_up(self, expert: ExpertProfile, conversation_history: list[dict], user_message: str) -> str:
        prompt = PersonaPromptBuilder.build_chat_prompt(expert, conversation_history, user_message)
        if self.client_ready:
            try:
                # Chat model without strict JSON mime type
                import google.generativeai as genai
                chat_model = genai.GenerativeModel(model_name=self.model_name)
                res = chat_model.generate_content(prompt)
                return res.text.strip()
            except Exception as e:
                print(f"[GeminiBrainAdapter] Chat call failed: {e}. Falling back to profile response.")

        # Heuristic fallback chat
        quote = expert.signature_quotes[0] if expert.signature_quotes else (expert.core_principles[0] if expert.core_principles else "focus relentlessly on real customer traction")
        warning = expert.common_warnings[0] if expert.common_warnings else "avoid building vanity features"
        contrarian = f" Remember: {expert.contrarian_theses[0]}" if expert.contrarian_theses else ""
        lens = expert.adversarial_lens or expert.stance_archetype
        return (
            f"Speaking from my perspective ({lens}): my guiding principle is '{quote}'. "
            f"Addressing your question '{user_message.strip()}': {warning}.{contrarian} "
            f"If you cannot prove users need this immediately without friction, nothing else matters."
        )


    def _parse_verdict_data(self, expert: ExpertProfile, data: Dict[str, Any]) -> ExpertVerdict:
        pillars = data.get("pillar_ratings", {})
        pillar_obj = PillarScores(
            market_demand=float(pillars.get("market_demand", 6.5)),
            differentiation=float(pillars.get("differentiation", 6.0)),
            feasibility=float(pillars.get("feasibility", 7.0)),
            financial_viability=float(pillars.get("financial_viability", 6.0)),
            execution_risk=float(pillars.get("execution_risk", 6.0)),
            regulatory_legal_risk=float(pillars.get("regulatory_legal_risk", 7.5)),
            market_timing=float(pillars.get("market_timing", 6.5)),
            defensibility_scale=float(pillars.get("defensibility_scale", 5.5)),
        )

        overall = float(data.get("overall_score", 6.5))
        verdict = str(data.get("verdict_label", "Promising"))
        if overall >= 8.0:
            verdict = "Strong"
        elif overall >= 6.0:
            verdict = "Promising"
        elif overall >= 4.0:
            verdict = "Risky"
        else:
            verdict = "Not viable"

        return ExpertVerdict(
            expert_id=expert.id,
            expert_name=expert.name,
            role_or_title=expert.role_or_title,
            stance_archetype=expert.stance_archetype,
            overall_score=overall,
            verdict_label=verdict,
            pillar_ratings=pillar_obj,
            opinion_critique=data.get("opinion_critique", f"Evaluation from perspective of {expert.name}."),
            specific_warnings=data.get("specific_warnings", expert.common_warnings[:2]),
            actionable_tips=data.get("actionable_tips", expert.core_principles[:2]),
            kill_question=data.get("kill_question", expert.first_questions[0] if expert.first_questions else "Why will customers choose you?"),
            first_question_to_founder=data.get("first_question_to_founder", "What evidence do you have today?"),
            cited_sources=data.get("cited_sources", expert.high_value_sources[:2])
        )

    def _heuristic_expert_evaluation(self, expert: ExpertProfile, brief: IdeaBrief) -> ExpertVerdict:
        """Deterministic evaluation strictly grounded in the expert's structured profile data."""
        # Calculate scores based on archetype
        base = 6.8
        if "Skeptic" in expert.stance_archetype:
            base -= 0.8
        elif "Wedge" in expert.stance_archetype:
            base += 0.4
        elif "Operator" in expert.stance_archetype:
            base += 0.2

        demand = min(9.5, max(3.0, base + 0.4))
        diff = min(9.5, max(3.0, base - 0.6))
        feas = min(9.5, max(3.0, base + 0.8))
        fin = min(9.5, max(3.0, base - 0.2))
        exec_risk = min(9.5, max(3.0, base - 0.5))
        reg_risk = min(9.5, max(3.0, base + 1.0))
        timing = min(9.5, max(3.0, base + 0.3))
        defens = min(9.5, max(3.0, base - 0.7))

        overall = round((demand + diff + feas + fin + exec_risk + reg_risk + timing + defens) / 8.0, 1)
        verdict = "Promising" if overall >= 6.0 else "Risky"
        if overall >= 8.0:
            verdict = "Strong"

        warnings = expert.common_warnings[:2] if expert.common_warnings else [
            f"High customer acquisition cost in {brief.detected_sectors[0] if brief.detected_sectors else 'this market'}",
            "Lack of clear early distribution wedge"
        ]
        tips = expert.core_principles[:2] if expert.core_principles else [
            "Validate with 10 high-intent paying users before scaling",
            "Focus strictly on the core problem without auxiliary features"
        ]
        kill_q = expert.first_questions[0] if expert.first_questions else (
            f"Why will {brief.target_customer} switch away from their existing workflow right now?"
        )

        quote_part = f" As I always emphasize: \"{expert.signature_quotes[0]}\"." if expert.signature_quotes else ""
        contrarian_part = f" Keep this contrarian truth in mind: {expert.contrarian_theses[0]}." if expert.contrarian_theses else ""
        lens_label = expert.adversarial_lens or expert.stance_archetype

        critique = (
            f"Through my lens of {lens_label}, looking at '{brief.title}': while {brief.solution_description} tackles {brief.problem_statement}, "
            f"the fatal vulnerability is {warnings[0]}.{quote_part} "
            f"My recommendation is unambiguous: {tips[0]}.{contrarian_part}"
        )


        citations = expert.high_value_sources[:2] if expert.high_value_sources else [
            f"Published operating principles on {expert.primary_sector}"
        ]

        return ExpertVerdict(
            expert_id=expert.id,
            expert_name=expert.name,
            role_or_title=expert.role_or_title,
            stance_archetype=expert.stance_archetype,
            overall_score=overall,
            verdict_label=verdict,
            pillar_ratings=PillarScores(
                market_demand=round(demand, 1),
                differentiation=round(diff, 1),
                feasibility=round(feas, 1),
                financial_viability=round(fin, 1),
                execution_risk=round(exec_risk, 1),
                regulatory_legal_risk=round(reg_risk, 1),
                market_timing=round(timing, 1),
                defensibility_scale=round(defens, 1),
            ),
            opinion_critique=critique,
            specific_warnings=warnings,
            actionable_tips=tips,
            kill_question=kill_q,
            first_question_to_founder=f"How many users have tested '{brief.title}' in the last 14 days?",
            cited_sources=citations
        )
