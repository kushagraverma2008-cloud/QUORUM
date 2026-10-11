from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ContextPills(BaseModel):
    stage: Optional[str] = Field(default="Idea", description="Idea, Prototype, MVP, Early Revenue, Scaling")
    target_market: Optional[str] = Field(default="B2B", description="B2B, B2C, B2B2C, Enterprise, D2C")
    geography: Optional[str] = Field(default="Global", description="Global, North America, India, Europe, SEA")
    budget: Optional[str] = Field(default="Bootstrapped", description="Bootstrapped, Pre-seed, Seed, Series A+")

class IdeaInput(BaseModel):
    title: Optional[str] = Field(default="Untitled Venture", description="Short title of the idea")
    pitch: str = Field(..., description="Unvarnished pitch or description of the venture")
    context: Optional[ContextPills] = Field(default_factory=ContextPills)
    uploaded_files: Optional[List[str]] = Field(default_factory=list, description="Names of uploaded pitch decks/documents")

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
