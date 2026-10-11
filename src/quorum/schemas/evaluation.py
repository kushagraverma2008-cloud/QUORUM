from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class PillarScores(BaseModel):
    market_demand: float = Field(..., ge=0.0, le=10.0, description="Reachable customer need")
    differentiation: float = Field(..., ge=0.0, le=10.0, description="Moat vs alternatives")
    feasibility: float = Field(..., ge=0.0, le=10.0, description="Practical delivery feasibility")
    financial_viability: float = Field(..., ge=0.0, le=10.0, description="Unit economics & margins")
    execution_risk: float = Field(..., ge=0.0, le=10.0, description="Execution safety (10=safest/lowest risk)")
    regulatory_legal_risk: float = Field(..., ge=0.0, le=10.0, description="Legal safety (10=safest/lowest risk)")
    market_timing: float = Field(..., ge=0.0, le=10.0, description="'Why now' timing alignment")
    defensibility_scale: float = Field(..., ge=0.0, le=10.0, description="Long-term scale defensibility")

class ExpertVerdict(BaseModel):
    expert_id: str
    expert_name: str
    role_or_title: Optional[str] = None
    stance_archetype: str
    overall_score: float = Field(..., ge=0.0, le=10.0)
    verdict_label: str = Field(..., description="Strong, Promising, Risky, Not viable")
    pillar_ratings: PillarScores
    opinion_critique: str = Field(..., description="Brutal, authentic perspective grounded in public record")
    specific_warnings: List[str] = Field(default_factory=list)
    actionable_tips: List[str] = Field(default_factory=list)
    kill_question: str = Field(..., description="The single make-or-break question from this expert")
    first_question_to_founder: str
    cited_sources: List[str] = Field(default_factory=list)
    is_dissenting: bool = Field(default=False)
    weight: float = Field(default=1.0)
