from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# ==============================================================================
# IDEA SCHEMAS
# ==============================================================================


class ContextPills(BaseModel):
    stage: Optional[str] = Field(
        default="Idea", description="Idea, Prototype, MVP, Early Revenue, Scaling"
    )
    target_market: Optional[str] = Field(
        default="B2B", description="B2B, B2C, B2B2C, Enterprise, D2C"
    )
    team_size: Optional[str] = Field(
        default="Solo Founder",
        description="Solo Founder, 2-3 Co-founders, Small Team (4-10), Growth (10+)",
    )
    runway_budget: Optional[str] = Field(
        default="Bootstrapped",
        description="Bootstrapped, Pre-Seed ($50k-$250k), Seed ($250k-$2M), Series A+",
    )
    primary_goal: Optional[str] = Field(
        default="Validate Urgency & Demand",
        description="Validate Urgency & Demand, Secure Pilot LOIs, Raise Angel/Pre-Seed, Launch Publicly",
    )
    geography: Optional[str] = Field(
        default="Global",
        description="Global, North America, India, Europe, Southeast Asia, Latin America",
    )


class IdeaInput(BaseModel):
    title: Optional[str] = Field(default="Untitled Venture", description="Short title of the idea")
    pitch: str = Field(..., description="Unvarnished pitch or description of the venture")
    context: Optional[ContextPills] = Field(default_factory=ContextPills)
    uploaded_files: Optional[List[str]] = Field(
        default_factory=list, description="Names of uploaded pitch decks/documents"
    )


class IdeaBrief(BaseModel):
    id: str
    title: str
    one_liner: str
    problem_statement: str
    target_customer: str
    solution_description: str
    revenue_model: str
    key_assumptions: List[str]
    detected_sectors: List[str]
    detected_functions: List[str]
    raw_pitch: str
    context: ContextPills


# ==============================================================================
# EXPERT SCHEMAS
# ==============================================================================


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
    stance_archetype: str = Field(
        default="Analytical Operator",
        description="Skeptic, Operator, Product Wedge, Growth, Capital Efficiency",
    )
    profile_depth: str = Field(
        default="basic", description="'deep' if distilled profile exists, else 'basic'"
    )
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


# ==============================================================================
# EVALUATION & PILLAR SCHEMAS
# ==============================================================================


class PillarScores(BaseModel):
    market_demand: float = Field(..., ge=0.0, le=10.0, description="Reachable customer need")
    differentiation: float = Field(..., ge=0.0, le=10.0, description="Moat vs alternatives")
    feasibility: float = Field(..., ge=0.0, le=10.0, description="Practical delivery feasibility")
    financial_viability: float = Field(..., ge=0.0, le=10.0, description="Unit economics & margins")
    execution_risk: float = Field(
        ..., ge=0.0, le=10.0, description="Execution safety (10=safest/lowest risk)"
    )
    regulatory_legal_risk: float = Field(
        ..., ge=0.0, le=10.0, description="Legal safety (10=safest/lowest risk)"
    )
    market_timing: float = Field(..., ge=0.0, le=10.0, description="'Why now' timing alignment")
    defensibility_scale: float = Field(
        ..., ge=0.0, le=10.0, description="Long-term scale defensibility"
    )


class ExpertVerdict(BaseModel):
    expert_id: str
    expert_name: str
    role_or_title: Optional[str] = None
    stance_archetype: str
    profile_depth: str = Field(default="basic", description="'deep' | 'basic'")
    source: str = Field(default="offline", description="'llm' | 'offline'")
    overall_score: float = Field(..., ge=0.0, le=10.0)
    verdict_label: str = Field(
        ..., description="Strong, Promising but risky, Weak, Do not build as-is"
    )
    pillar_ratings: PillarScores
    opinion_critique: str = Field(
        ..., description="Brutal, authentic perspective grounded in public record"
    )
    specific_warnings: List[str] = Field(default_factory=list)
    actionable_tips: List[str] = Field(default_factory=list)
    kill_question: str = Field(
        ..., description="The single make-or-break question from this expert"
    )
    first_question_to_founder: str
    cited_sources: List[str] = Field(default_factory=list)
    is_dissenting: bool = Field(default=False)
    weight: float = Field(default=1.0)


# ==============================================================================
# REPORT & SYNTHESIS SCHEMAS
# ==============================================================================


class TopWarning(BaseModel):
    warning: str
    severity: str = Field(default="Critical", description="Critical, High, Medium")
    experts_count: int = 1
    flagged_by: List[str] = Field(default_factory=list)


class TopTip(BaseModel):
    tip: str
    experts_count: int = 1
    recommended_by: List[str] = Field(default_factory=list)


class KillQuestion(BaseModel):
    question: str
    raised_by: str
    rationale: str = ""


class DisagreementPoint(BaseModel):
    topic: str
    optimist_view: str
    optimists: List[str]
    skeptic_view: str
    skeptics: List[str]


class ConsensusDissentMap(BaseModel):
    consensus_points: List[str] = Field(default_factory=list)
    sharp_disagreements: List[DisagreementPoint] = Field(default_factory=list)


class TacticalRoadmap(BaseModel):
    days_30: List[str] = Field(default_factory=list, description="Immediate de-risking actions")
    days_90: List[str] = Field(
        default_factory=list, description="Validation & initial wedge deployment"
    )
    days_180: List[str] = Field(
        default_factory=list, description="Defensibility & repeatable engine"
    )


class NetworkNode(BaseModel):
    id: str
    name: str
    archetype: str
    score: float = 5.0
    color: str = "#6366f1"
    # Optional metadata or backward compat coords if needed
    coords: Optional[Dict[str, float]] = None
    radius: Optional[float] = None
    category: Optional[str] = None


class NetworkEdge(BaseModel):
    source: str
    target: str
    tension: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Divergence tension between experts"
    )
    reason: str = ""
    # Backward compatibility fields
    relation: Optional[str] = None
    weight: Optional[float] = None


class NetworkGraph(BaseModel):
    nodes: List[NetworkNode] = Field(default_factory=list)
    edges: List[NetworkEdge] = Field(default_factory=list)
    tension_index: float = Field(
        default=0.0, description="Overall divergence tension in the council"
    )
    cluster_tags: List[str] = Field(default_factory=list)


class CouncilReport(BaseModel):
    id: str
    idea_id: str
    title: str
    source: str = Field(default="offline", description="'llm' | 'offline'")
    overall_score: float = Field(..., ge=0.0, le=10.0)
    verdict_label: str = Field(
        ..., description="Strong, Promising but risky, Weak, Do not build as-is"
    )
    confidence_index: float = Field(default=0.85, ge=0.0, le=1.0)
    consensus_percentage: float = Field(default=75.0, ge=0.0, le=100.0)
    executive_summary: str
    council_in_one_paragraph: str
    pillar_scores: PillarScores
    top_warnings: List[TopWarning] = Field(default_factory=list)
    top_tips: List[TopTip] = Field(default_factory=list)
    kill_questions: List[KillQuestion] = Field(default_factory=list)
    tailored_actions: List[str] = Field(
        default_factory=list, description="What to do next for YOUR specific founder situation"
    )
    is_suspicious_input: bool = Field(
        default=False, description="Flagged if prompt injection or adversarial tampering detected"
    )
    consensus_dissent: ConsensusDissentMap = Field(default_factory=ConsensusDissentMap)
    tactical_roadmap: TacticalRoadmap = Field(default_factory=TacticalRoadmap)
    expert_roster: List[ExpertVerdict] = Field(default_factory=list)
    network_graph: NetworkGraph = Field(default_factory=NetworkGraph)
    created_at: str
