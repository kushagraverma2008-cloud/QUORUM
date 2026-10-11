import uuid
from typing import List, Dict, Any, Optional
from quorum.schemas.idea import IdeaInput, IdeaBrief, ContextPills
from quorum.schemas.expert import ExpertProfile
from quorum.brains.store import ExpertStore

class CouncilRouter:
    """Classifies ideas, selects relevant sectors, and convenes curated expert panels."""

    SECTOR_KEYWORDS = {
        "technology and software": ["saas", "software", "app", "api", "cloud", "developer", "platform", "b2b", "workflow", "crm", "database", "web"],
        "A.I. M.L. DATA SCIENCE": ["ai", "machine learning", "llm", "neural", "vision", "nlp", "agent", "generative", "model", "data"],
        "Telecom & Connectivity": ["telecom", "5g", "network", "satellite", "broadband", "iot", "wireless"],
        "Deep Tech, Space & Defence": ["aerospace", "quantum", "defense", "drone", "space", "robotics", "hardware"],
        "Manufacturing & Hardware": ["hardware", "manufacturing", "electronics", "factory", "3d printing", "devices"],
        "Finance & Fintech": ["fintech", "payment", "banking", "lending", "credit", "crypto", "defi", "investment", "insurance"],
        "Professional Services": ["consulting", "legal", "recruiting", "hr", "accounting", "agency"],
        "E-commerce & Retail": ["ecommerce", "store", "d2c", "retail", "marketplace", "checkout", "shipping", "cart"],
        "Consumer Goods & FMCG": ["fmcg", "packaged goods", "household", "consumer", "appliance"],
        "Fashion, Beauty & Personal Care": ["fashion", "beauty", "cosmetics", "skincare", "apparel", "luxury", "clothing"],
        " Food & Beverage": ["food", "beverage", "restaurant", "cloud kitchen", "drink", "snack", "dining"],
        "Agriculture & Agritech": ["agritech", "farming", "crop", "dairy", "agriculture", "fertilizer", "soil"],
        "Travel & Hospitality": ["travel", "hotel", "hospitality", "tourism", "airline", "booking", "flight"],
        "Media, Entertainment & Gaming": ["gaming", "media", "entertainment", "music", "video", "creator", "streaming", "ott"],
        "Sports & Fitness": ["fitness", "gym", "sport", "workout", "athlete", "wellness"],
        "Home, Lifestyle & Pets": ["pet", "home", "interior", "furniture", "lifestyle", "decor"],
        "Healthcare & Life Sciences": ["health", "biotech", "pharma", "medical", "clinic", "hospital", "patient", "wellness"],
        "Education & EdTech": ["edtech", "education", "student", "learning", "course", "tutor", "school", "college"],
        "Social Impact & Public Sector": ["social impact", "ngo", "non-profit", "government", "policy", "sustainability", "civic"]
    }

    @classmethod
    def create_brief_from_input(cls, submission: IdeaInput, parsed_text: Optional[str] = None) -> IdeaBrief:
        full_pitch = (parsed_text or "") + "\n" + submission.pitch
        full_pitch = full_pitch.strip()
        
        detected_sectors = cls.detect_sectors(full_pitch)
        if not detected_sectors:
            detected_sectors = ["technology and software"]

        # Extract title or fallback
        title = submission.title if submission.title and submission.title != "Untitled Venture" else full_pitch.split("\n")[0][:60]
        one_liner = full_pitch.split("\n")[0][:120] if full_pitch else "Innovative startup solving key friction point."
        
        brief = IdeaBrief(
            id=f"idea_{uuid.uuid4().hex[:8]}",
            title=title.strip(),
            one_liner=one_liner.strip(),
            problem_statement="High customer friction and inefficient workflow in the target sector.",
            target_customer=submission.context.target_market if submission.context else "B2B Operators",
            solution_description=full_pitch[:400] if len(full_pitch) > 400 else full_pitch,
            revenue_model="SaaS Subscription / Usage-based Fees",
            key_assumptions=[
                "Target users experience acute, daily pain from this problem",
                "Organic distribution or wedge acquisition is feasible",
                "Unit margins remain positive after scaling customer acquisition"
            ],
            detected_sectors=detected_sectors,
            detected_functions=["Product Wedge", "Distribution", "Unit Economics", "Fundraising"],
            raw_pitch=full_pitch,
            context=submission.context or ContextPills()
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
    def recommend_panel(cls, brief: IdeaBrief, panel_size: int = 15) -> List[ExpertProfile]:
        store = ExpertStore.get_instance()
        chosen: List[ExpertProfile] = []
        seen_ids = set()

        # 1. Primary sector experts
        for sector in brief.detected_sectors:
            sector_experts = store.get_experts_by_sector(sector)
            for e in sector_experts:
                if e.id not in seen_ids and len(chosen) < (panel_size - 4):
                    chosen.append(e)
                    seen_ids.add(e.id)

        # 2. Add foundational tech & functional titans (Paul Graham, Michael Seibel, Dalton Caldwell)
        foundational_ids = ["paul_graham", "michael_seibel", "dalton_caldwell", "geoff_ralston", "tobi_lutke", "sam_altman"]
        for fid in foundational_ids:
            exp = store.get_expert_by_id(fid)
            if exp and exp.id not in seen_ids and len(chosen) < panel_size:
                chosen.append(exp)
                seen_ids.add(exp.id)

        # 3. Fill remaining with general store search if needed
        if len(chosen) < panel_size:
            extra = store.search_experts(brief.title + " " + " ".join(brief.detected_sectors), limit=panel_size)
            for e in extra:
                if e.id not in seen_ids and len(chosen) < panel_size:
                    chosen.append(e)
                    seen_ids.add(e.id)

        return chosen
