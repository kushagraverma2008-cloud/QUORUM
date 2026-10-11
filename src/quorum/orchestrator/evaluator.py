import asyncio
import json
from typing import List, AsyncGenerator, Dict, Any
from quorum.schemas.idea import IdeaBrief
from quorum.schemas.expert import ExpertProfile
from quorum.schemas.evaluation import ExpertVerdict
from quorum.schemas.report import CouncilReport
from quorum.brains.gemini import GeminiBrainAdapter
from quorum.orchestrator.synthesizer import CouncilSynthesizer

class CouncilEvaluator:
    """Executes multi-expert deliberations with live event streaming and final synthesis."""

    def __init__(self, gemini_adapter: GeminiBrainAdapter | None = None):
        self.adapter = gemini_adapter or GeminiBrainAdapter()

    def evaluate_expert_sync(self, expert: ExpertProfile, brief: IdeaBrief) -> ExpertVerdict:
        return self.adapter.evaluate_expert(expert, brief)

    def run_council_evaluation(self, brief: IdeaBrief, panel: List[ExpertProfile]) -> CouncilReport:
        """Synchronous / Direct evaluation of the entire panel."""
        verdicts: List[ExpertVerdict] = []
        for expert in panel:
            v = self.evaluate_expert_sync(expert, brief)
            verdicts.append(v)
        return CouncilSynthesizer.synthesize_report(brief, verdicts)

    async def stream_council_evaluation(
        self, 
        brief: IdeaBrief, 
        panel: List[ExpertProfile]
    ) -> AsyncGenerator[str, None]:
        """Async generator streaming SSE events for real-time frontend deliberation theater."""
        
        # 1. Panel Assembled Event
        init_event = {
            "type": "panel_assembled",
            "idea_id": brief.id,
            "title": brief.title,
            "total_experts": len(panel),
            "sectors": brief.detected_sectors,
            "panel": [
                {
                    "id": e.id, 
                    "name": e.name, 
                    "role": e.role_or_title, 
                    "archetype": e.stance_archetype,
                    "sector": e.primary_sector
                } 
                for e in panel
            ]
        }
        yield f"data: {json.dumps(init_event)}\n\n"
        await asyncio.sleep(0.05)

        # 2. Step through experts and yield live progress
        verdicts: List[ExpertVerdict] = []
        
        for idx, expert in enumerate(panel, start=1):
            deliberating_event = {
                "type": "expert_deliberating",
                "expert_id": expert.id,
                "expert_name": expert.name,
                "archetype": expert.stance_archetype,
                "current_step": idx,
                "total": len(panel)
            }
            yield f"data: {json.dumps(deliberating_event)}\n\n"
            
            # Run evaluation in threadpool so async loop isn't blocked
            loop = asyncio.get_event_loop()
            verdict = await loop.run_in_executor(None, self.evaluate_expert_sync, expert, brief)
            verdicts.append(verdict)

            concluded_event = {
                "type": "expert_concluded",
                "expert_id": expert.id,
                "expert_name": expert.name,
                "overall_score": verdict.overall_score,
                "verdict_label": verdict.verdict_label,
                "kill_question": verdict.kill_question,
                "completed": idx,
                "total": len(panel)
            }
            yield f"data: {json.dumps(concluded_event)}\n\n"
            await asyncio.sleep(0.02)

        # 3. Synthesis event
        yield f"data: {json.dumps({'type': 'synthesis_started'})}\n\n"
        await asyncio.sleep(0.05)

        # 4. Final Council Report
        report = CouncilSynthesizer.synthesize_report(brief, verdicts)
        complete_event = {
            "type": "report_complete",
            "report": report.model_dump()
        }
        yield f"data: {json.dumps(complete_event)}\n\n"
