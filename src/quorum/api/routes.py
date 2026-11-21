import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from quorum.config import settings
from quorum.engine import CouncilEvaluator, CouncilRouter, ExpertStore, get_gemini_adapter
from quorum.parser.document import DocumentParser
from quorum.schemas import (
    ContextPills,
    CouncilReport,
    ExpertProfile,
    ExpertVerdict,
    IdeaBrief,
    IdeaInput,
)

logger = logging.getLogger("quorum.api.routes")
router = APIRouter(prefix="/api", tags=["Quorum Council"])

_reports_cache: Dict[str, CouncilReport] = {}
_briefs_cache: Dict[str, IdeaBrief] = {}


class ChatRequest(BaseModel):
    expert_id: str
    user_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class EvaluateRequest(BaseModel):
    brief: IdeaBrief
    expert_ids: Optional[List[str]] = None
    panel_size: Optional[int] = 6
    fresh: Optional[bool] = False


class RebuttalRequest(BaseModel):
    brief: IdeaBrief
    expert_id: str
    kill_question: str
    answer: str


@router.get("/health")
async def health_check():
    store = ExpertStore.get_instance()
    adapter = get_gemini_adapter()
    return {
        "status": "healthy",
        "service": "QUORUM",
        "mode": "LIVE" if adapter._is_ready else "OFFLINE",
        "experts_loaded": store.count(),
        "version": settings.app_version,
    }


@router.get("/sectors")
async def list_sectors():
    store = ExpertStore.get_instance()
    sectors_map: Dict[str, int] = {}
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
        raise HTTPException(status_code=404, detail=f"Expert '{expert_id}' not found")
    return exp


@router.post("/ideas/analyze", response_model=IdeaBrief)
async def analyze_idea(submission: IdeaInput):
    """Analyzes text pitch input and normalizes it into a structured IdeaBrief."""
    if len(submission.pitch) > settings.max_brief_length:
        submission.pitch = submission.pitch[: settings.max_brief_length]

    brief = CouncilRouter.create_brief_from_input(submission)
    _briefs_cache[brief.id] = brief
    return brief


@router.post("/ideas/upload-and-analyze", response_model=IdeaBrief)
async def upload_and_analyze_idea(
    title: Optional[str] = Form("Untitled Venture"),
    pitch: Optional[str] = Form(""),
    stage: Optional[str] = Form("Idea"),
    target_market: Optional[str] = Form("B2B"),
    team_size: Optional[str] = Form("Solo Founder"),
    runway_budget: Optional[str] = Form("Bootstrapped"),
    primary_goal: Optional[str] = Form("Validate Urgency & Demand"),
    geography: Optional[str] = Form("Global"),
    file: Optional[UploadFile] = File(None),
):
    """Upload pitch deck / PDF / DOCX / TXT document and synthesize an IdeaBrief with security checks."""
    extracted_text = ""
    file_name = ""

    if file:
        file_name = file.filename or ""
        max_bytes = settings.max_upload_mb * 1024 * 1024
        content = await file.read()

        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file size ({len(content) / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {settings.max_upload_mb} MB",
            )

        try:
            extracted_text = DocumentParser.parse_file(file_name, content)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Document parsing error: {e}")

    full_pitch = ((pitch or "") + "\n" + extracted_text).strip()
    if len(full_pitch) > settings.max_brief_length:
        full_pitch = full_pitch[: settings.max_brief_length]

    submission = IdeaInput(
        title=title or "Untitled Venture",
        pitch=full_pitch,
        context=ContextPills(
            stage=stage,
            target_market=target_market,
            team_size=team_size,
            runway_budget=runway_budget,
            primary_goal=primary_goal,
            geography=geography,
        ),
        uploaded_files=[file_name] if file_name else [],
    )
    brief = CouncilRouter.create_brief_from_input(submission, parsed_text=extracted_text)
    _briefs_cache[brief.id] = brief
    return brief


@router.post("/council/recommend-panel", response_model=List[ExpertProfile])
async def recommend_panel(
    brief: IdeaBrief,
    panel_size: int = Query(6, ge=5, le=7),
    seed: Optional[int] = Query(
        None, description="Deterministic seed for reproducible council composition or re-rolling"
    ),
):
    """Recommends a balanced 5-7 member adversarial council with deterministic seeding."""
    return CouncilRouter.recommend_panel(brief, panel_size=panel_size, seed=seed)


@router.post("/council/evaluate", response_model=CouncilReport)
async def evaluate_council(req: EvaluateRequest):
    """Direct synchronous evaluation of an idea by the council."""
    store = ExpertStore.get_instance()
    panel: List[ExpertProfile] = []

    if req.expert_ids:
        for eid in req.expert_ids:
            exp = store.get_expert_by_id(eid)
            if exp and exp not in panel:
                panel.append(exp)

    if not panel:
        panel = CouncilRouter.recommend_panel(req.brief, panel_size=req.panel_size or 6)

    # Ensure strictly 5-7 size
    panel = panel[:7]
    if len(panel) < 5:
        all_exp = store.get_all_experts()
        for e in all_exp:
            if e not in panel:
                panel.append(e)
            if len(panel) >= 5:
                break

    evaluator = CouncilEvaluator()
    report = evaluator.run_council_evaluation(req.brief, panel, fresh=bool(req.fresh))
    _reports_cache[report.id] = report
    return report


@router.post("/council/evaluate/stream")
async def evaluate_council_stream(req: EvaluateRequest):
    """Streams live deliberation events via Server-Sent Events (SSE)."""
    store = ExpertStore.get_instance()
    panel: List[ExpertProfile] = []

    if req.expert_ids:
        for eid in req.expert_ids:
            exp = store.get_expert_by_id(eid)
            if exp and exp not in panel:
                panel.append(exp)

    if not panel:
        panel = CouncilRouter.recommend_panel(req.brief, panel_size=req.panel_size or 6)

    panel = panel[:7]
    if len(panel) < 5:
        for e in store.get_all_experts():
            if e not in panel:
                panel.append(e)
            if len(panel) >= 5:
                break

    evaluator = CouncilEvaluator()
    return StreamingResponse(
        evaluator.stream_council_evaluation(req.brief, panel, fresh=bool(req.fresh)),
        media_type="text/event-stream",
    )


@router.get("/council/reports/{report_id}", response_model=CouncilReport)
async def get_report(report_id: str):
    if report_id not in _reports_cache:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return _reports_cache[report_id]


@router.post("/council/expert-chat")
async def chat_with_expert(req: ChatRequest):
    """Cross-examine any individual expert persona with follow-up questions."""
    store = ExpertStore.get_instance()
    expert = store.get_expert_by_id(req.expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail=f"Expert '{req.expert_id}' not found")

    adapter = get_gemini_adapter()
    reply = adapter.chat_follow_up(
        expert=expert,
        conversation_history=req.conversation_history or [],
        user_message=req.user_message,
    )
    return {"expert_id": expert.id, "expert_name": expert.name, "reply": reply}


# ==============================================================================
# PHASE 7: KILL-QUESTION REBUTTAL LOOP
# ==============================================================================


@router.post("/rebut", response_model=ExpertVerdict)
async def rebut_kill_question(req: RebuttalRequest):
    """Allows founder to answer an expert's kill question and receive an updated score."""
    store = ExpertStore.get_instance()
    expert = store.get_expert_by_id(req.expert_id)
    if not expert:
        raise HTTPException(status_code=404, detail=f"Expert '{req.expert_id}' not found")

    adapter = get_gemini_adapter()

    # Create modified brief with rebuttal context injected
    rebuttal_pitch = (
        f"{req.brief.solution_description}\n\n"
        f"--- FOUNDER REBUTTAL TO KILL QUESTION ---\n"
        f'Kill Question Raised by {expert.name}: "{req.kill_question}"\n'
        f'Founder Answer: "{req.answer.strip()}"'
    )

    modified_brief = req.brief.model_copy(update={"solution_description": rebuttal_pitch})

    # Re-evaluate with fresh=True so rebuttal gets fresh scoring
    updated_verdict = await adapter.evaluate_expert_async(expert, modified_brief, fresh=True)
    return updated_verdict
