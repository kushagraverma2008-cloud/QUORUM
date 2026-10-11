from typing import List, Optional
from pydantic import BaseModel, Field

class SourceReference(BaseModel):
    title: str
    source_type: str = Field(default="talk", description="talk, book, essay, interview, podcast")
    url_or_ref: Optional[str] = None
    notes: Optional[str] = None

class ExpertProfile(BaseModel):
    id: str
    name: str
    role_or_title: Optional[str] = None
    primary_sector: str
    secondary_sectors: List[str] = Field(default_factory=list)
    function_tags: List[str] = Field(default_factory=list)
    stance_archetype: str = Field(default="Analytical Operator", description="Skeptic, Operator, Product Wedge, Growth, Capital Efficiency")
    core_principles: List[str] = Field(default_factory=list)
    common_warnings: List[str] = Field(default_factory=list)
    decision_heuristics: List[str] = Field(default_factory=list)
    first_questions: List[str] = Field(default_factory=list)
    contrarian_theses: List[str] = Field(default_factory=list)
    signature_quotes: List[str] = Field(default_factory=list)
    adversarial_lens: Optional[str] = None
    high_value_sources: List[str] = Field(default_factory=list)
    bio_snippet: Optional[str] = None
    avatar_url: Optional[str] = None

