from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from quorum.schemas.evaluation import PillarScores, ExpertVerdict

class TopWarning(BaseModel):
    warning: str
    severity: str = Field(default="Critical", description="Critical, High, Medium")
    experts_count: int
    flagged_by: List[str]

class TopTip(BaseModel):
    tip: str
    experts_count: int
    recommended_by: List[str]

class KillQuestion(BaseModel):
    question: str
    raised_by: str
    rationale: str

class DisagreementPoint(BaseModel):
    topic: str
    optimist_view: str
    optimists: List[str]
    skeptic_view: str
    skeptics: List[str]

class ConsensusDissentMap(BaseModel):
    consensus_points: List[str]
    sharp_disagreements: List[DisagreementPoint]

class TacticalRoadmap(BaseModel):
    days_30: List[str] = Field(default_factory=list, description="Immediate de-risking actions")
    days_90: List[str] = Field(default_factory=list, description="Validation & initial wedge deployment")
    days_180: List[str] = Field(default_factory=list, description="Defensibility & repeatable engine")

# 3D Cinematic Visualizer Network Graph Schemas
class NetworkNode(BaseModel):
    id: str
    label: str
    category: str = Field(..., description="idea, pillar, expert, warning, moat")
    score: Optional[float] = None
    radius: float = Field(default=12.0)
    color: str = Field(default="#6366f1")
    coords: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NetworkEdge(BaseModel):
    source: str
    target: str
    relation: str = Field(..., description="scores, supports, conflicts, warns, anchors")
    weight: float = Field(default=1.0)
    color: str = Field(default="#94a3b8")
    animated: bool = Field(default=True)
    pulse_rate: float = Field(default=1.0)

class NetworkGraph(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    cluster_tags: List[str]
    tension_index: float = Field(default=0.0, description="Divergence tension in the council")

class CouncilReport(BaseModel):
    id: str
    idea_id: str
    title: str
    overall_score: float = Field(..., ge=0.0, le=10.0)
    verdict_label: str = Field(..., description="Strong, Promising, Risky, Not viable")
    confidence_index: float = Field(..., ge=0.0, le=1.0)
    consensus_percentage: float = Field(..., ge=0.0, le=100.0)
    executive_summary: str
    council_in_one_paragraph: str
    pillar_scores: PillarScores
    top_warnings: List[TopWarning]
    top_tips: List[TopTip]
    kill_questions: List[KillQuestion]
    consensus_dissent: ConsensusDissentMap
    tactical_roadmap: TacticalRoadmap
    expert_roster: List[ExpertVerdict]
    network_graph: NetworkGraph
    created_at: str
