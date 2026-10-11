import json
from pathlib import Path
from typing import List, Dict, Optional
from quorum.schemas.expert import ExpertProfile
from quorum.config import settings

class ExpertStore:
    """In-memory cache and search index for all 700+ curated expert profiles."""
    
    _instance: Optional["ExpertStore"] = None
    
    def __init__(self):
        self.profiles: List[ExpertProfile] = []
        self._profiles_by_id: Dict[str, ExpertProfile] = {}
        self._profiles_by_sector: Dict[str, List[ExpertProfile]] = {}
        self._load_profiles()

    @classmethod
    def get_instance(cls) -> "ExpertStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_profiles(self):
        catalog_path = settings.data_dir / "expert_catalog.json"
        if not catalog_path.exists():
            from quorum.ingestion.catalog import CatalogIngestor
            from quorum.ingestion.library import LibraryIngestor
            raw = CatalogIngestor.ingest_catalog()
            self.profiles = LibraryIngestor.enrich_profiles(raw)
            CatalogIngestor.save_catalog_json()
        else:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.profiles = [ExpertProfile(**p) for p in data]
            from quorum.ingestion.library import LibraryIngestor
            self.profiles = LibraryIngestor.enrich_with_distilled_knowledge(self.profiles)
            # Save enriched catalog to keep on-disk cache fresh
            with open(catalog_path, "w", encoding="utf-8") as f:
                json.dump([p.model_dump() for p in self.profiles], f, indent=2, ensure_ascii=False)


        for p in self.profiles:
            self._profiles_by_id[p.id] = p
            
            # Map sectors
            s = p.primary_sector.strip()
            if s not in self._profiles_by_sector:
                self._profiles_by_sector[s] = []
            self._profiles_by_sector[s].append(p)
            
            for sec in p.secondary_sectors:
                sec_clean = sec.strip()
                if sec_clean not in self._profiles_by_sector:
                    self._profiles_by_sector[sec_clean] = []
                self._profiles_by_sector[sec_clean].append(p)

    def get_expert_by_id(self, expert_id: str) -> Optional[ExpertProfile]:
        return self._profiles_by_id.get(expert_id)

    def get_all_experts(self) -> List[ExpertProfile]:
        return self.profiles

    def get_experts_by_sector(self, sector_name: str) -> List[ExpertProfile]:
        matched = []
        for s_key, experts in self._profiles_by_sector.items():
            if sector_name.lower() in s_key.lower() or s_key.lower() in sector_name.lower():
                matched.extend(experts)
        # Deduplicate
        seen = set()
        deduped = []
        for e in matched:
            if e.id not in seen:
                seen.add(e.id)
                deduped.append(e)
        return deduped

    def search_experts(self, query: str, limit: int = 25) -> List[ExpertProfile]:
        q = query.lower()
        scored: List[tuple[int, ExpertProfile]] = []
        
        for p in self.profiles:
            score = 0
            if q in p.name.lower():
                score += 10
            if q in p.primary_sector.lower():
                score += 5
            for tag in p.function_tags:
                if q in tag.lower():
                    score += 3
            for principle in p.core_principles:
                if q in principle.lower():
                    score += 2
            for warning in p.common_warnings:
                if q in warning.lower():
                    score += 2
                    
            if score > 0:
                scored.append((score, p))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]
