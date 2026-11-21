import hashlib
import logging
import random
import uuid
from typing import List, Optional

from quorum.engine.store import ExpertStore
from quorum.schemas import ContextPills, ExpertProfile, IdeaBrief, IdeaInput

logger = logging.getLogger("quorum.engine.router")


class CouncilRouter:
    """Selects a balanced, deterministic, adversarial expert panel grounded in real domain expertise."""

    SECTOR_KEYWORDS = {
        "technology and software": [
            "saas",
            "software",
            "app",
            "api",
            "cloud",
            "developer",
            "platform",
            "b2b",
            "workflow",
            "crm",
            "database",
            "web",
            "infra",
        ],
        "A.I. M.L. DATA SCIENCE": [
            "ai",
            "machine learning",
            "llm",
            "neural",
            "vision",
            "nlp",
            "agent",
            "generative",
            "model",
            "data",
            "deep learning",
        ],
        "Telecom & Connectivity": [
            "telecom",
            "5g",
            "network",
            "satellite",
            "broadband",
            "iot",
            "wireless",
        ],
        "Deep Tech, Space & Defence": [
            "aerospace",
            "quantum",
            "defense",
            "drone",
            "space",
            "robotics",
            "hardware",
            "satellite",
        ],
        "Manufacturing & Hardware": [
            "hardware",
            "manufacturing",
            "electronics",
            "factory",
            "3d printing",
            "devices",
            "supply chain",
        ],
        "Finance & Fintech": [
            "fintech",
            "payment",
            "banking",
            "lending",
            "credit",
            "crypto",
            "defi",
            "investment",
            "insurance",
            "payments",
        ],
        "Professional Services": [
            "consulting",
            "legal",
            "recruiting",
            "hr",
            "accounting",
            "agency",
        ],
        "E-commerce & Retail": [
            "ecommerce",
            "store",
            "d2c",
            "retail",
            "marketplace",
            "checkout",
            "shipping",
            "cart",
            "inventory",
        ],
        "Consumer Goods & FMCG": ["fmcg", "packaged goods", "household", "consumer", "appliance"],
        "Fashion, Beauty & Personal Care": [
            "fashion",
            "beauty",
            "cosmetics",
            "skincare",
            "apparel",
            "luxury",
            "clothing",
        ],
        "Food & Beverage": [
            "food",
            "beverage",
            "restaurant",
            "cloud kitchen",
            "drink",
            "snack",
            "dining",
        ],
        "Agriculture & Agritech": [
            "agritech",
            "farming",
            "crop",
            "dairy",
            "agriculture",
            "fertilizer",
            "soil",
        ],
        "Travel & Hospitality": [
            "travel",
            "hotel",
            "hospitality",
            "tourism",
            "airline",
            "booking",
            "flight",
        ],
        "Media, Entertainment & Gaming": [
            "gaming",
            "media",
            "entertainment",
            "music",
            "video",
            "creator",
            "streaming",
            "ott",
        ],
        "Sports & Fitness": ["fitness", "gym", "sport", "workout", "athlete", "wellness"],
        "Home, Lifestyle & Pets": ["pet", "home", "interior", "furniture", "lifestyle", "decor"],
        "Healthcare & Life Sciences": [
            "health",
            "biotech",
            "pharma",
            "medical",
            "clinic",
            "hospital",
            "patient",
            "wellness",
            "clinical",
        ],
        "Education & EdTech": [
            "edtech",
            "education",
            "student",
            "learning",
            "course",
            "tutor",
            "school",
            "college",
        ],
        "Social Impact & Public Sector": [
            "social impact",
            "ngo",
            "non-profit",
            "government",
            "policy",
            "sustainability",
            "civic",
            "climate",
        ],
    }

    REQUIRED_ARCHETYPES = [
        ("skeptic", ["skeptic", "cynic", "risk", "critic"]),
        (
            "unit-economics",
            ["unit economics", "capital", "financial", "margin", "hawk", "operator"],
        ),
        ("product", ["product", "wedge", "visionary", "builder", "creator"]),
        ("contrarian", ["contrarian", "philosopher", "outlier", "radical", "paradox"]),
    ]

    @classmethod
    def create_brief_from_input(
        cls, submission: IdeaInput, parsed_text: Optional[str] = None
    ) -> IdeaBrief:
        full_pitch = ((parsed_text or "") + "\n" + submission.pitch).strip()
        detected_sectors = cls.detect_sectors(full_pitch)
        if not detected_sectors:
            detected_sectors = ["technology and software"]

        title = (
            submission.title.strip()
            if submission.title and submission.title != "Untitled Venture"
            else full_pitch.split("\n")[0][:60].strip()
        )
        if not title:
            title = "Autonomous Venture Concept"

        first_line = (
            full_pitch.split("\n")[0][:120].strip()
            if full_pitch
            else "Venture concept addressing core market need."
        )

        brief = IdeaBrief(
            id=f"idea_{uuid.uuid4().hex[:8]}",
            title=title,
            one_liner=first_line,
            problem_statement="Target customers experience significant friction, high operational cost, or lack of alternatives.",
            target_customer=submission.context.target_market
            if submission.context and submission.context.target_market
            else "Enterprise / B2B Operators",
            solution_description=full_pitch[:500] if len(full_pitch) > 500 else full_pitch,
            revenue_model="SaaS Subscription / Usage Fee / Transaction Margin",
            key_assumptions=[
                "Target users have urgent, quantifiable pain and budget to solve it",
                "Distribution wedge enables repeatable customer acquisition below payback threshold",
                "Unit economics remain resilient against competitive compression",
            ],
            detected_sectors=detected_sectors,
            detected_functions=["Product Wedge", "Distribution", "Unit Economics", "Execution"],
            raw_pitch=full_pitch,
            context=submission.context or ContextPills(),
        )
        return brief

    @classmethod
    def detect_sectors(cls, text: str) -> List[str]:
        t_low = text.lower()
        scored: List[tuple[int, str]] = []
        for sector, keywords in cls.SECTOR_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in t_low)
            if matches > 0:
                scored.append((matches, sector))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:3]]

    @classmethod
    def recommend_panel(
        cls, brief: IdeaBrief, panel_size: int = 6, seed: Optional[int] = None
    ) -> List[ExpertProfile]:
        """Convenes a deterministic 5-7 expert council ensuring required archetypes & deep profiles."""
        target_size = max(5, min(7, panel_size))

        # Deterministic seed from brief contents if not explicitly given
        if seed is None:
            raw = f"{brief.title}_{brief.one_liner}_{brief.solution_description[:100]}_{','.join(brief.detected_sectors)}"
            seed = int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)

        rnd = random.Random(seed)
        store = ExpertStore.get_instance()

        chosen: List[ExpertProfile] = []
        chosen_ids = set()

        def add_candidate(c: ExpertProfile) -> bool:
            if c and c.id not in chosen_ids:
                chosen.append(c)
                chosen_ids.add(c.id)
                return True
            return False

        # Helper to sort candidates: prefer deep profiles, then deterministic shuffle
        def pick_best(candidates: List[ExpertProfile]) -> Optional[ExpertProfile]:
            available = [c for c in candidates if c.id not in chosen_ids]
            if not available:
                return None
            deep = [c for c in available if c.profile_depth == "deep"]
            pool = deep if deep else available
            return rnd.choice(pool)

        # 1. Context-driven priority selection (Phase 2 smarter assistant)
        ctx = brief.context
        if ctx:
            # Solo or early-stage: ensure iconic early-stage product visionary
            if ctx.team_size in ("Solo Founder", "2-3 Co-founders") or ctx.stage in (
                "Idea",
                "Prototype",
            ):
                for founder_id in ["paul_graham", "michael_seibel", "dalton_caldwell"]:
                    exp = store.get_expert_by_id(founder_id)
                    if exp and add_candidate(exp):
                        break

            # B2B / Enterprise: ensure enterprise sales / GTM specialist
            if ctx.target_market in ("B2B", "Enterprise"):
                gtm_experts = store.search_experts(
                    "enterprise sales b2b go-to-market distribution", limit=10
                )
                gtm_pick = pick_best(gtm_experts)
                if gtm_pick:
                    add_candidate(gtm_pick)

            # Bootstrapped runway: prioritize unit economics & capital efficiency
            if ctx.runway_budget == "Bootstrapped":
                unit_econ_experts = store.get_experts_by_archetype(
                    "capital"
                ) or store.get_experts_by_archetype("operator")
                econ_pick = pick_best(unit_econ_experts)
                if econ_pick:
                    add_candidate(econ_pick)

        # 2. Primary Sector Specialists (up to 2)
        for sector in brief.detected_sectors:
            if len(chosen) >= 3:
                break
            sector_experts = store.get_experts_by_sector(sector)
            if sector_experts:
                pick = pick_best(sector_experts)
                if pick:
                    add_candidate(pick)

        # 2. Mandatory Archetypes: Skeptic, Unit Economics, Product, Contrarian
        for arch_name, arch_keywords in cls.REQUIRED_ARCHETYPES:
            if len(chosen) >= target_size:
                break

            matched_archetype_experts: List[ExpertProfile] = []
            for kw in arch_keywords:
                matched_archetype_experts.extend(store.get_experts_by_archetype(kw))

            pick = pick_best(matched_archetype_experts)
            if pick:
                add_candidate(pick)
            else:
                logger.warning(
                    "Could not fill required archetype '%s' from indexed store.", arch_name
                )

        # 3. If slots remain, add iconic generalists / deep profiles
        curated_icons = [
            "paul_graham",
            "michael_seibel",
            "dalton_caldwell",
            "geoff_ralston",
            "tobi_lutke",
            "sam_altman",
            "jensen_huang",
            "peter_thiel",
            "charlie_munger",
        ]
        rnd.shuffle(curated_icons)
        for icon_id in curated_icons:
            if len(chosen) >= target_size:
                break
            icon_exp = store.get_expert_by_id(icon_id)
            if icon_exp:
                add_candidate(icon_exp)

        # 4. Fallback guarantee: fill up to target_size from full store
        if len(chosen) < target_size:
            all_experts = [e for e in store.get_all_experts() if e.id not in chosen_ids]
            # Prefer deep profiles
            all_deep = [e for e in all_experts if e.profile_depth == "deep"]
            fill_pool = all_deep if len(all_deep) >= (target_size - len(chosen)) else all_experts
            rnd.shuffle(fill_pool)
            for exp in fill_pool:
                if len(chosen) >= target_size:
                    break
                add_candidate(exp)

        # Final safety verification: enforce 5-7 size
        return chosen[:target_size]
