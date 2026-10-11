import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from quorum.schemas.idea import IdeaInput, IdeaBrief, ContextPills
from quorum.schemas.expert import ExpertProfile
from quorum.schemas.report import CouncilReport
from quorum.parser.document import DocumentParser
from quorum.brains.store import ExpertStore
from quorum.brains.gemini import GeminiBrainAdapter
from quorum.orchestrator.router import CouncilRouter
from quorum.orchestrator.evaluator import CouncilEvaluator

router = APIRouter(prefix="/api", tags=["Quorum Council"])

# In-memory store for generated reports in this session
_reports_cache: Dict[str, CouncilReport] = {}
_briefs_cache: Dict[str, IdeaBrief] = {}

class ChatRequest(BaseModel):
    expert_id: str
    user_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class EvaluateRequest(BaseModel):
    brief: IdeaBrief
    expert_ids: Optional[List[str]] = None
    panel_size: Optional[int] = 15

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Quorum AI Expert Council",
        "experts_loaded": len(ExpertStore.get_instance().get_all_experts()),
        "engine": "Google Gemini 2.5/2.0 Flash"
    }

@router.get("/sectors")
async def list_sectors():
    store = ExpertStore.get_instance()
    sectors_map = {}
    for p in store.get_all_experts():
        s = p.primary_sector.strip()
        sectors_map[s] = sectors_map.get(s, 0) + 1
    return {"sectors": [{"name": k, "expert_count": v} for k, v in sorted(sectors_map.items())]}

@router.get("/experts", response_model=List[ExpertProfile])
async def list_experts(sector: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    store = ExpertStore.get_instance()
    if q:
        return store.search_experts(q, limit=limit)
    elif sector:
        return store.get_experts_by_sector(sector)[:limit]
    return store.get_all_experts()[:limit]

@router.get("/experts/{expert_id}", response_model=ExpertProfile)
async def get_expert(expert_id: str):
    store = ExpertStore.get_instance()
    exp = store.get_expert_by_id(expert_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Expert profile not found")
    return exp

@router.post("/ideas/analyze", response_model=IdeaBrief)
async def analyze_idea(submission: IdeaInput):
    """Analyzes text pitch input and normalizes it into an IdeaBrief."""
    brief = CouncilRouter.create_brief_from_input(submission)
    _briefs_cache[brief.id] = brief
    return brief

@router.post("/ideas/upload-and-analyze", response_model=IdeaBrief)
async def upload_and_analyze_idea(
    title: Optional[str] = Form("Untitled Venture"),
    pitch: Optional[str] = Form(""),
    stage: Optional[str] = Form("Idea"),
    target_market: Optional[str] = Form("B2B"),
    geography: Optional[str] = Form("Global"),
    budget: Optional[str] = Form("Bootstrapped"),
    file: Optional[UploadFile] = File(None)
):
    """Upload pitch deck / PDF / DOCX / TXT document and synthesize an IdeaBrief."""
    extracted_text = ""
    file_name = ""
    if file:
        file_name = file.filename
        content = await file.read()
        extracted_text = DocumentParser.parse_file(file.filename, content)

    submission = IdeaInput(
        title=title,
        pitch=pitch or "",
        context=ContextPills(stage=stage, target_market=target_market, geography=geography, budget=budget),
        uploaded_files=[file_name] if file_name else []
    )
    brief = CouncilRouter.create_brief_from_input(submission, parsed_text=extracted_text)
    _briefs_cache[brief.id] = brief
    return brief

@router.post("/council/recommend-panel", response_model=List[ExpertProfile])
async def recommend_panel(brief: IdeaBrief, panel_size: int = 15):
    """Recommends a balanced panel of domain experts and functional mentors."""
    return CouncilRouter.recommend_panel(brief, panel_size=panel_size)

@router.post("/council/evaluate", response_model=CouncilReport)
async def evaluate_council(req: EvaluateRequest):
    """Direct, synchronous evaluation of an idea by the council."""
    store = ExpertStore.get_instance()
    panel: List[ExpertProfile] = []

    if req.expert_ids:
        for eid in req.expert_ids:
            exp = store.get_expert_by_id(eid)
            if exp:
                panel.append(exp)
    
    if not panel:
        panel = CouncilRouter.recommend_panel(req.brief, panel_size=req.panel_size or 15)

    evaluator = CouncilEvaluator()
    report = evaluator.run_council_evaluation(req.brief, panel)
    _reports_cache[report.id] = report
    return report

@router.post("/council/evaluate/stream")
async def evaluate_council_stream(req: EvaluateRequest):
    """Streams live deliberation theater events via Server-Sent Events (SSE)."""
    store = ExpertStore.get_instance()
    panel: List[ExpertProfile] = []

    if req.expert_ids:
        for eid in req.expert_ids:
            exp = store.get_expert_by_id(eid)
            if exp:
                panel.append(exp)

    if not panel:
        panel = CouncilRouter.recommend_panel(req.brief, panel_size=req.panel_size or 15)

    evaluator = CouncilEvaluator()
    return StreamingResponse(
        evaluator.stream_council_evaluation(req.brief, panel),
        media_type="text/event-stream"
    )

@router.get("/council/reports/{report_id}", response_model=CouncilReport)
async def get_report(report_id: str):
    if report_id not in _reports_cache:
        raise HTTPException(status_code=404, detail="Report not found")
    return _reports_cache[report_id]

@router.post("/council/expert-chat")
async def chat_with_expert(req: ChatRequest):
    """Cross-examine any individual expert persona with follow-up questions."""
    store = ExpertStore.get_instance()
    expert = store.get_expert_by_id(req.expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail=f"Expert '{req.expert_id}' not found")

    adapter = GeminiBrainAdapter()
    reply = adapter.chat_follow_up(
        expert=expert,
        conversation_history=req.conversation_history or [],
        user_message=req.user_message
    )
    return {
        "expert_id": expert.id,
        "expert_name": expert.name,
        "reply": reply
    }
