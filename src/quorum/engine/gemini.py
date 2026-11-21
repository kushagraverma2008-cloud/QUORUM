import asyncio
import hashlib
import json
import logging
import random
import re
from typing import List, Optional

from pydantic import BaseModel, Field

from quorum.config import settings
from quorum.engine.persona import PersonaPromptBuilder
from quorum.schemas import (
    ExpertProfile,
    ExpertVerdict,
    IdeaBrief,
    PillarScores,
)

logger = logging.getLogger("quorum.engine.gemini")


class StructuredEvaluationOutput(BaseModel):
    pillar_ratings: PillarScores
    opinion_critique: str = Field(description="Max 80 words authentic critique")
    specific_warnings: List[str] = Field(default_factory=list, description="At most 3 warnings")
    actionable_tips: List[str] = Field(
        default_factory=list, description="At most 2 actionable tips"
    )
    kill_question: str = Field(description="The single make-or-break question")
    first_question_to_founder: str = Field(description="Opening question")
    cited_sources: List[str] = Field(default_factory=list)


class GeminiBrainAdapter:
    """Modernized Gemini Adapter using google-genai SDK, disk caching, concurrency, and honest fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        concurrency: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.concurrency = concurrency or settings.llm_concurrency
        self.timeout_seconds = timeout_seconds or settings.llm_timeout_seconds
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Ensure cache directory exists
        self.cache_dir = settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._client = None
        self._is_ready = False
        self._init_client_lazy()

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.concurrency)
        return self._semaphore

    def _init_client_lazy(self):
        """Lazy load google-genai only when a valid API key exists."""
        clean_key = (self.api_key or "").strip()
        if not clean_key or clean_key.startswith("your_") or len(clean_key) < 10:
            self._is_ready = False
            return

        try:
            from google import genai

            self._client = genai.Client(api_key=clean_key, http_options={"api_version": "v1beta"})
            self._is_ready = True
            logger.info("Initialized google-genai client with model: %s", self.model_name)
        except Exception as e:
            logger.warning("Could not initialize google-genai client: %s. Using offline mode.", e)
            self._is_ready = False

    def _compute_cache_key(self, brief: IdeaBrief, expert: ExpertProfile) -> str:
        raw_pitch = getattr(brief, "raw_pitch", "") or brief.one_liner or brief.title
        seed = f"{raw_pitch}_{expert.id}_{self.model_name}_{PersonaPromptBuilder.PROMPT_VERSION}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[ExpertVerdict]:
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return ExpertVerdict(**data)
            except Exception as e:
                logger.debug("Cache read error for %s: %s", cache_key, e)
        return None

    def _save_to_cache(self, cache_key: str, verdict: ExpertVerdict):
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(verdict.model_dump(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug("Cache write error for %s: %s", cache_key, e)

    @staticmethod
    def _compute_overall_and_verdict(pillar_obj: PillarScores) -> tuple[float, str]:
        """Compute overall score on server as the strict mean of 8 pillars."""
        scores = [
            pillar_obj.market_demand,
            pillar_obj.differentiation,
            pillar_obj.feasibility,
            pillar_obj.financial_viability,
            pillar_obj.execution_risk,
            pillar_obj.regulatory_legal_risk,
            pillar_obj.market_timing,
            pillar_obj.defensibility_scale,
        ]
        mean_score = round(sum(scores) / len(scores), 1)

        if mean_score >= 7.5:
            label = "Strong"
        elif mean_score >= 5.5:
            label = "Promising but risky"
        elif mean_score >= 4.0:
            label = "Weak"
        else:
            label = "Do not build as-is"

        return mean_score, label

    async def evaluate_expert_async(
        self, expert: ExpertProfile, brief: IdeaBrief, fresh: bool = False
    ) -> ExpertVerdict:
        """Async evaluation with disk caching, semaphore, timeout, and structured output."""
        cache_key = self._compute_cache_key(brief, expert)

        # 1. Check disk cache if not fresh
        if not fresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        # 2. If client is not ready (no API key), run offline fallback immediately
        if not self._is_ready or not self._client:
            verdict = self._heuristic_expert_evaluation(expert, brief)
            self._save_to_cache(cache_key, verdict)
            return verdict

        # 3. Call Live Gemini with concurrency semaphore and retries
        prompt = PersonaPromptBuilder.build_evaluation_prompt(expert, brief)

        async with self.semaphore:
            verdict = await self._call_gemini_with_retries(expert, brief, prompt)

        self._save_to_cache(cache_key, verdict)
        return verdict

    def evaluate_expert(
        self, expert: ExpertProfile, brief: IdeaBrief, fresh: bool = False
    ) -> ExpertVerdict:
        """Synchronous wrapper for evaluate_expert_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running inside existing loop, create task or run offline
                return self._heuristic_expert_evaluation(expert, brief)
            return loop.run_until_complete(self.evaluate_expert_async(expert, brief, fresh=fresh))
        except Exception:
            return asyncio.run(self.evaluate_expert_async(expert, brief, fresh=fresh))

    async def _call_gemini_with_retries(
        self, expert: ExpertProfile, brief: IdeaBrief, prompt: str, max_retries: int = 2
    ) -> ExpertVerdict:
        from google.genai import types

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=settings.gemini_temperature,
            max_output_tokens=4096,
        )

        active_model = self.model_name
        for attempt in range(max_retries + 1):
            try:
                # Wrap synchronous client call in thread with timeout
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._client.models.generate_content,
                        model=active_model,
                        contents=prompt,
                        config=config,
                    ),
                    timeout=self.timeout_seconds,
                )

                raw_text = response.text.strip() if response and response.text else ""
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
                cleaned = re.sub(r"\s*```$", "", cleaned)
                data = json.loads(cleaned)

                # Extract pillar ratings robustly (whether flat or nested)
                p_data = (
                    data.get("pillar_ratings")
                    if isinstance(data.get("pillar_ratings"), dict)
                    else data
                )

                def get_p_val(key, default=6.0):
                    val = p_data.get(key, data.get(key, default))
                    try:
                        return max(0.0, min(10.0, float(val)))
                    except (TypeError, ValueError):
                        return default

                pillar_obj = PillarScores(
                    market_demand=get_p_val("market_demand", 6.0),
                    differentiation=get_p_val("differentiation", 5.5),
                    feasibility=get_p_val("feasibility", 6.5),
                    financial_viability=get_p_val("financial_viability", 5.5),
                    execution_risk=get_p_val("execution_risk", 6.0),
                    regulatory_legal_risk=get_p_val("regulatory_legal_risk", 7.5),
                    market_timing=get_p_val("market_timing", 6.0),
                    defensibility_scale=get_p_val("defensibility_scale", 5.0),
                )

                # Server-calculated overall score and label
                overall_score, verdict_label = self._compute_overall_and_verdict(pillar_obj)

                critique = str(data.get("opinion_critique", f"Evaluation from {expert.name}."))
                warnings = data.get("specific_warnings", expert.common_warnings[:2])
                if not isinstance(warnings, list):
                    warnings = [str(warnings)]
                tips = data.get("actionable_tips", expert.core_principles[:2])
                if not isinstance(tips, list):
                    tips = [str(tips)]

                kill_q = str(
                    data.get("kill_question") or expert.first_questions[0]
                    if expert.first_questions
                    else "What prevents an incumbent from copying this?"
                )
                opening_q = str(
                    data.get("first_question_to_founder")
                    or "Show me evidence of real customer pull."
                )
                sources = data.get("cited_sources", expert.high_value_sources[:2])
                if not isinstance(sources, list):
                    sources = [str(sources)]

                return ExpertVerdict(
                    expert_id=expert.id,
                    expert_name=expert.name,
                    role_or_title=expert.role_or_title,
                    stance_archetype=expert.stance_archetype,
                    profile_depth=expert.profile_depth,
                    source="llm",
                    overall_score=overall_score,
                    verdict_label=verdict_label,
                    pillar_ratings=pillar_obj,
                    opinion_critique=critique[:500],
                    specific_warnings=[str(w)[:180] for w in warnings[:3]],
                    actionable_tips=[str(t)[:180] for t in tips[:2]],
                    kill_question=kill_q[:250],
                    first_question_to_founder=opening_q[:250],
                    cited_sources=[str(s)[:100] for s in sources[:2]],
                    is_dissenting=False,
                    weight=1.0,
                )

            except (asyncio.TimeoutError, Exception) as e:
                err_str = str(e).lower()
                # Check for 404 / Model Not Found and fall back to secondary model
                if (
                    "not found" in err_str or "404" in err_str
                ) and active_model != settings.gemini_fallback_model:
                    fallback_model = settings.gemini_fallback_model
                    logger.warning(
                        "Primary model '%s' not found (%s). Falling back to secondary model '%s'.",
                        active_model,
                        e,
                        fallback_model,
                    )
                    active_model = fallback_model
                    continue

                is_rate_or_server_err = (
                    "429" in str(e)
                    or "500" in str(e)
                    or "503" in str(e)
                    or isinstance(e, asyncio.TimeoutError)
                )
                if attempt < max_retries and is_rate_or_server_err:
                    backoff = (2**attempt) + random.uniform(0.1, 0.4)
                    logger.warning(
                        "Retryable error for %s on attempt %d: %s. Backing off %.2fs",
                        expert.name,
                        attempt,
                        e,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                else:
                    logger.warning(
                        "Gemini call failed for %s (%s). Falling back to offline heuristic.",
                        expert.name,
                        e,
                    )
                    break

        return self._heuristic_expert_evaluation(expert, brief)

    def _heuristic_expert_evaluation(
        self, expert: ExpertProfile, brief: IdeaBrief
    ) -> ExpertVerdict:
        """Deterministic persona-grounded offline evaluation (never fails)."""
        title_low = brief.title.lower()
        pitch_low = brief.solution_description.lower()
        context_stage = brief.context.stage.lower()

        # Seed pseudo-random variance based on expert ID and pitch
        seed_val = int(hashlib.md5(f"{expert.id}_{brief.title}".encode()).hexdigest()[:8], 16)
        rnd = random.Random(seed_val)

        # Baseline scores
        base_demand = 6.5 + (rnd.uniform(-0.8, 1.2))
        base_diff = 5.5 + (rnd.uniform(-1.0, 1.2))
        base_feas = 7.0 + (rnd.uniform(-0.5, 1.5))
        base_fin = 6.0 + (rnd.uniform(-1.0, 1.0))
        base_exec = 6.0 + (rnd.uniform(-0.8, 1.0))
        base_reg = 7.5 + (rnd.uniform(-0.5, 1.0))
        base_timing = 6.5 + (rnd.uniform(-0.8, 1.2))
        base_defens = 5.0 + (rnd.uniform(-1.0, 1.5))

        if "ai" in title_low or "ai" in pitch_low:
            base_diff -= 0.3

        # Adjust based on archetype
        arch = expert.stance_archetype.lower()
        if "skeptic" in arch or "cynic" in arch:
            base_demand -= 1.2
            base_diff -= 1.0
            base_defens -= 1.5
        elif "unit economics" in arch or "hawk" in arch or "capital" in arch:
            base_fin -= 1.8
            base_exec -= 1.0
        elif "product" in arch or "wedge" in arch or "visionary" in arch:
            base_feas += 0.8
            base_timing += 0.7
        elif "contrarian" in arch:
            base_diff += 1.0
            base_demand -= 1.0

        if context_stage in ("idea", "concept"):
            base_exec -= 0.8
            base_fin -= 0.6

        # Clamp between 1.0 and 9.5
        def clamp(val):
            return round(max(1.0, min(9.5, val)), 1)

        pillars = PillarScores(
            market_demand=clamp(base_demand),
            differentiation=clamp(base_diff),
            feasibility=clamp(base_feas),
            financial_viability=clamp(base_fin),
            execution_risk=clamp(base_exec),
            regulatory_legal_risk=clamp(base_reg),
            market_timing=clamp(base_timing),
            defensibility_scale=clamp(base_defens),
        )

        overall, label = self._compute_overall_and_verdict(pillars)

        # Authentic critique voice
        quote = (
            expert.signature_quotes[0]
            if expert.signature_quotes
            else "Demand unvarnished customer reality before building."
        )
        warning = (
            expert.common_warnings[0]
            if expert.common_warnings
            else "Premature scaling will burn cash before true PMF is discovered."
        )
        principle = (
            expert.core_principles[0]
            if expert.core_principles
            else "First principles reasoning is essential."
        )

        critique = (
            f"As {expert.name}, my core rule is '{quote}'. "
            f"For '{brief.title}', your wedge must overcome customer inertia. "
            f"My primary concern is that {warning.lower().rstrip('.')}. "
            f"Validate willingness to pay immediately before scaling."
        )

        kill_q = (
            expert.first_questions[0]
            if expert.first_questions
            else "If a dominant incumbent copies this feature next month, why do your customers stay?"
        )

        warnings_list = expert.common_warnings[:2] or [warning]
        tips_list = expert.core_principles[:2] or [principle]

        return ExpertVerdict(
            expert_id=expert.id,
            expert_name=expert.name,
            role_or_title=expert.role_or_title,
            stance_archetype=expert.stance_archetype,
            profile_depth=expert.profile_depth,
            source="offline",
            overall_score=overall,
            verdict_label=label,
            pillar_ratings=pillars,
            opinion_critique=critique[:400],
            specific_warnings=warnings_list,
            actionable_tips=tips_list,
            kill_question=kill_q,
            first_question_to_founder="Show me proof that real customers desperately want this today.",
            cited_sources=expert.high_value_sources[:2],
            is_dissenting=False,
            weight=1.0,
        )

    def chat_follow_up(
        self, expert: ExpertProfile, conversation_history: list[dict], user_message: str
    ) -> str:
        prompt = PersonaPromptBuilder.build_chat_prompt(expert, conversation_history, user_message)

        if self._is_ready and self._client:
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(
                    "Live chat call failed for %s: %s. Using heuristic reply.", expert.name, e
                )

        quote = (
            expert.signature_quotes[0]
            if expert.signature_quotes
            else (
                expert.core_principles[0]
                if expert.core_principles
                else "focus on retention and user pull"
            )
        )
        warning = expert.common_warnings[0] if expert.common_warnings else "avoid vanity metrics"
        lens = expert.adversarial_lens or expert.stance_archetype

        return (
            f"Speaking from my perspective as a {lens}: '{quote}'. "
            f"To your point: {warning}. "
            f"If you can't verify that customers will commit cash or daily usage, you don't have a business yet."
        )


_default_adapter: Optional[GeminiBrainAdapter] = None


def get_gemini_adapter() -> GeminiBrainAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = GeminiBrainAdapter()
    return _default_adapter
