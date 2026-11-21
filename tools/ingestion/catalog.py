import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from quorum.schemas.expert import ExpertProfile
from quorum.config import settings

class CatalogIngestor:
    """Ingests the 19-sector EXPERT LIST.xlsx file into structured ExpertProfiles."""

    @staticmethod
    def _read_excel_xml(xlsx_path: Path) -> Dict[str, List[List[str]]]:
        """Fast XML parser for xlsx files using standard library (zero external dependency)."""
        sheets_data = {}
        if not xlsx_path.exists():
            return sheets_data

        with zipfile.ZipFile(xlsx_path) as z:
            # 1. Read shared strings
            shared_strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                for si in tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                    t_nodes = si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                    text = "".join(t.text for t in t_nodes if t.text)
                    shared_strings.append(text)

            # 2. Get sheet names and targets
            wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
            rels_tree = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
            rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels_tree}

            sheets_nodes = wb_tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet")
            for s in sheets_nodes:
                name = s.attrib["name"].strip()
                r_id = s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
                target = rel_map[r_id]
                if not target.startswith("xl/"):
                    target = "xl/" + target

                if target in z.namelist():
                    sheet_tree = ET.fromstring(z.read(target))
                    rows_nodes = sheet_tree.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row")
                    
                    rows_list = []
                    for row in rows_nodes:
                        row_vals = []
                        for c in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                            t = c.attrib.get("t")
                            v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                            val = v.text if v is not None else ""
                            if t == "s" and val.isdigit():
                                val = shared_strings[int(val)]
                            row_vals.append(val.strip())
                        if any(row_vals):
                            rows_list.append(row_vals)
                    sheets_data[name] = rows_list

        return sheets_data

    @classmethod
    def ingest_catalog(cls, excel_path: Optional[Path] = None) -> List[ExpertProfile]:
        path = excel_path or settings.excel_catalog_path
        sheets_data = cls._read_excel_xml(path)
        
        profiles: List[ExpertProfile] = []
        seen_ids = set()

        # Map common archetypes based on tags
        def infer_archetype(tags: str, name: str) -> str:
            lower = (tags + " " + name).lower()
            if any(k in lower for k in ["fundrais", "vc", "invest", "capital"]):
                return "Capital & Growth Strategist"
            elif any(k in lower for k in ["product", "wedge", "design", "ux"]):
                return "Product Wedge Specialist"
            elif any(k in lower for k in ["operat", "supply", "execut", "scale", "manuf"]):
                return "Rigorous Operator"
            elif any(k in lower for k in ["skeptic", "risk", "legal", "complian"]):
                return "Risk & Moat Skeptic"
            elif any(k in lower for k in ["ai", "deep tech", "science", "engineer"]):
                return "Deep Tech Architect"
            return "Analytical Founder"

        for sheet_name, rows in sheets_data.items():
            if len(rows) < 2:
                continue

            header = [h.lower() for h in rows[0]]
            # Find expert column index
            expert_col = 1
            for idx, h in enumerate(header):
                if "expert" in h:
                    expert_col = idx
                    break

            # Find tags or domain column
            tags_col = 2 if len(rows[0]) > 2 else -1
            sources_col = 3 if len(rows[0]) > 3 else -1

            for r in rows[1:]:
                if len(r) <= expert_col:
                    continue
                name = r[expert_col].strip()
                if not name or name.startswith("=") or len(name) < 2:
                    continue
                
                # Clean aliases (e.g. Tobias Lütke?)
                clean_name = name.rstrip("?").strip()
                expert_id = clean_name.lower().replace(" ", "_").replace(".", "").replace("-", "_")

                if expert_id in seen_ids:
                    # Update secondary sector
                    for p in profiles:
                        if p.id == expert_id:
                            if sheet_name not in p.secondary_sectors and sheet_name != p.primary_sector:
                                p.secondary_sectors.append(sheet_name)
                    continue

                tags_text = r[tags_col] if tags_col != -1 and len(r) > tags_col else ""
                sources_text = r[sources_col] if sources_col != -1 and len(r) > sources_col else ""

                tags_list = [t.strip() for t in tags_text.split(",") if t.strip()]
                sources_list = [s.strip() for s in sources_text.split(";") if s.strip()] or ([sources_text] if sources_text else [])

                profile = ExpertProfile(
                    id=expert_id,
                    name=clean_name,
                    role_or_title=f"Industry Leader in {sheet_name}",
                    primary_sector=sheet_name,
                    secondary_sectors=[],
                    function_tags=tags_list,
                    stance_archetype=infer_archetype(tags_text, clean_name),
                    core_principles=[],
                    common_warnings=[],
                    decision_heuristics=[],
                    first_questions=[],
                    high_value_sources=sources_list,
                    bio_snippet=f"Documented expert in {sheet_name} with focus on {tags_text or 'industry leadership'}."
                )
                profiles.append(profile)
                seen_ids.add(expert_id)

        return profiles

    @classmethod
    def save_catalog_json(cls, output_path: Optional[Path] = None) -> Path:
        out = output_path or (settings.data_dir / "expert_catalog.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        profiles = cls.ingest_catalog()
        from quorum.ingestion.library import LibraryIngestor
        enriched = LibraryIngestor.enrich_profiles(profiles)
        data = [p.model_dump() for p in enriched]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return out
