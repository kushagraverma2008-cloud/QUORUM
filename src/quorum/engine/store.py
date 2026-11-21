import json
import logging
from typing import Dict, List, Optional, Set

from quorum.config import settings
from quorum.schemas import ExpertProfile

logger = logging.getLogger("quorum.engine.store")


class ExpertStore:
    """In-memory high-speed cache and pre-indexed search engine for all 709 expert profiles."""

    _instance: Optional["ExpertStore"] = None

    def __init__(self):
        self.profiles: List[ExpertProfile] = []
        self._profiles_by_id: Dict[str, ExpertProfile] = {}
        self._profiles_by_sector: Dict[str, List[ExpertProfile]] = {}
        self._profiles_by_archetype: Dict[str, List[ExpertProfile]] = {}
        self._deep_profile_ids: Set[str] = set()
        self._load_profiles()
        self._build_indexes()

    @classmethod
    def get_instance(cls) -> "ExpertStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_profiles(self):
        catalog_path = settings.data_dir / "expert_catalog.json"
        if not catalog_path.exists():
            raise FileNotFoundError(f"Expert catalog not found at: {catalog_path}")

        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Scan distilled profiles directory to flag deep knowledge personas
        dist_dir = settings.distilled_dir
        if not dist_dir.exists():
            # Fallback check inside tools or data
            alt_dir = settings.base_dir / "data" / "distilled_profiles"
            if alt_dir.exists():
                dist_dir = alt_dir

        distilled_map: Dict[str, Dict] = {}
        if dist_dir.exists():
            for f in dist_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        dist_data = json.load(jf)
                        slug = f.stem.lower()
                        distilled_map[slug] = dist_data
                except Exception as e:
                    logger.warning("Could not read distilled profile %s: %s", f, e)

        raw_profiles: List[ExpertProfile] = []
        for p_dict in data:
            profile = ExpertProfile(**p_dict)
            p_slug = profile.id.lower().replace("-", "_")
            p_name_slug = profile.name.lower().replace(" ", "_")

            matched = None
            if p_slug in distilled_map:
                matched = distilled_map[p_slug]
            elif p_name_slug in distilled_map:
                matched = distilled_map[p_name_slug]
            else:
                for k, v in distilled_map.items():
                    if k in p_slug or p_slug in k or k in p_name_slug:
                        matched = v
                        break

            if matched:
                profile.profile_depth = "deep"
                self._deep_profile_ids.add(profile.id)
                for pr in matched.get("core_principles", []):
                    if pr and pr not in profile.core_principles:
                        profile.core_principles.append(pr)
                for wr in matched.get("common_warnings", []):
                    if wr and wr not in profile.common_warnings:
                        profile.common_warnings.append(wr)
                for ct in matched.get("contrarian_theses", []):
                    if ct and ct not in profile.contrarian_theses:
                        profile.contrarian_theses.append(ct)
                for sq in matched.get("signature_quotes", []):
                    if sq and sq not in profile.signature_quotes:
                        profile.signature_quotes.append(sq)
                if matched.get("adversarial_lens") and not profile.adversarial_lens:
                    profile.adversarial_lens = matched["adversarial_lens"]
            else:
                profile.profile_depth = "basic"

            # Assign contrarian archetype to iconic thinkers or those with contrarian theses
            contrarian_icon_ids = {
                "naval_ravikant",
                "vinod_khosla",
                "peter_thiel",
                "marc_andreessen",
                "brian_armstrong",
                "chamath_palihapitiya",
            }
            if profile.id in contrarian_icon_ids or (
                profile.contrarian_theses
                and profile.stance_archetype
                in ("Analytical Founder", "Capital & Growth Strategist")
            ):
                profile.stance_archetype = "Contrarian Philosopher"

            raw_profiles.append(profile)

        self.profiles = raw_profiles

    def _build_indexes(self):
        """Build domain, sector, and archetype lookup tables once at startup."""
        self._profiles_by_id.clear()
        self._profiles_by_sector.clear()
        self._profiles_by_archetype.clear()

        for p in self.profiles:
            self._profiles_by_id[p.id] = p

            # Sector indexing
            s_clean = p.primary_sector.strip().lower()
            self._profiles_by_sector.setdefault(s_clean, []).append(p)
            for sec in p.secondary_sectors:
                sec_clean = sec.strip().lower()
                self._profiles_by_sector.setdefault(sec_clean, []).append(p)

            # Archetype indexing
            arch = p.stance_archetype.strip().lower()
            self._profiles_by_archetype.setdefault(arch, []).append(p)

    def get_expert_by_id(self, expert_id: str) -> Optional[ExpertProfile]:
        return self._profiles_by_id.get(expert_id)

    def get_all_experts(self) -> List[ExpertProfile]:
        return self.profiles

    def count(self) -> int:
        return len(self.profiles)

    def get_experts_by_sector(self, sector_name: str) -> List[ExpertProfile]:
        """Fast lookup using pre-built sector index."""
        target = sector_name.strip().lower()
        matched: List[ExpertProfile] = []
        for s_key, experts in self._profiles_by_sector.items():
            if target in s_key or s_key in target:
                matched.extend(experts)

        # Deduplicate preserving order
        seen = set()
        deduped = []
        for e in matched:
            if e.id not in seen:
                seen.add(e.id)
                deduped.append(e)
        return deduped

    def get_experts_by_archetype(self, archetype_pattern: str) -> List[ExpertProfile]:
        """Fast lookup using pre-built archetype index."""
        target = archetype_pattern.strip().lower()
        matched: List[ExpertProfile] = []
        for arch_key, experts in self._profiles_by_archetype.items():
            if target in arch_key or arch_key in target:
                matched.extend(experts)

        seen = set()
        deduped = []
        for e in matched:
            if e.id not in seen:
                seen.add(e.id)
                deduped.append(e)
        return deduped

    def search_experts(self, query: str, limit: int = 25) -> List[ExpertProfile]:
        q = query.lower().strip()
        if not q:
            return self.profiles[:limit]

        scored: List[tuple[int, ExpertProfile]] = []
        for p in self.profiles:
            score = 0
            if q in p.name.lower():
                score += 15
            if q in p.primary_sector.lower():
                score += 8
            if q in p.stance_archetype.lower():
                score += 6
            for tag in p.function_tags:
                if q in tag.lower():
                    score += 4
            for principle in p.core_principles:
                if q in principle.lower():
                    score += 2
            for warning in p.common_warnings:
                if q in warning.lower():
                    score += 2
            if p.profile_depth == "deep":
                score += 1

            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]
