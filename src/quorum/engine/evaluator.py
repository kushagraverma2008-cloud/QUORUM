import asyncio
import json
import logging
from typing import AsyncGenerator, List, Optional

from quorum.engine.gemini import GeminiBrainAdapter, get_gemini_adapter
from quorum.engine.synthesizer import CouncilSynthesizer
from quorum.schemas import CouncilReport, ExpertProfile, ExpertVerdict, IdeaBrief

logger = logging.getLogger("quorum.engine.evaluator")


class CouncilEvaluator:
    """Orchestrates parallel expert deliberations using as_completed and real-time SSE event streaming."""

    def __init__(self, gemini_adapter: Optional[GeminiBrainAdapter] = None):
        self.adapter = gemini_adapter or get_gemini_adapter()

    def evaluate_expert_sync(
        self, expert: ExpertProfile, brief: IdeaBrief, fresh: bool = False
    ) -> ExpertVerdict:
        return self.adapter.evaluate_expert(expert, brief, fresh=fresh)

    async def evaluate_expert_async(
        self, expert: ExpertProfile, brief: IdeaBrief, fresh: bool = False
    ) -> ExpertVerdict:
        return await self.adapter.evaluate_expert_async(expert, brief, fresh=fresh)

    def run_council_evaluation(
        self, brief: IdeaBrief, panel: List[ExpertProfile], fresh: bool = False
    ) -> CouncilReport:
        """Synchronous council evaluation."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Direct evaluation loop if inside existing event loop
            verdicts: List[ExpertVerdict] = []
            for p in panel:
                verdicts.append(self.evaluate_expert_sync(p, brief, fresh=fresh))
            return CouncilSynthesizer.synthesize_report(brief, verdicts)
        return asyncio.run(self.run_council_evaluation_async(brief, panel, fresh=fresh))

    async def run_council_evaluation_async(
        self, brief: IdeaBrief, panel: List[ExpertProfile], fresh: bool = False
    ) -> CouncilReport:
        """Asynchronous evaluation of entire council using as_completed."""
        tasks = [
            asyncio.create_task(self.evaluate_expert_async(expert, brief, fresh=fresh))
            for expert in panel
        ]

        verdicts: List[ExpertVerdict] = []
        for coro in asyncio.as_completed(tasks):
            try:
                v = await coro
                verdicts.append(v)
            except Exception as e:
                logger.error("Expert evaluation error: %s", e)

        if not verdicts:
            raise RuntimeError("All expert evaluations failed.")

        return CouncilSynthesizer.synthesize_report(brief, verdicts)

    async def stream_council_evaluation(
        self, brief: IdeaBrief, panel: List[ExpertProfile], fresh: bool = False
    ) -> AsyncGenerator[str, None]:
        """Streams real SSE events as experts finish with a 15-second heartbeat."""
        total = len(panel)

        # 1. Start event
        start_payload = {
            "type": "start",
            "idea_id": brief.id,
            "title": brief.title,
            "total_experts": total,
            "panel": [
                {
                    "id": p.id,
                    "name": p.name,
                    "archetype": p.stance_archetype,
                    "depth": p.profile_depth,
                }
                for p in panel
            ],
        }
        yield f"event: start\ndata: {json.dumps(start_payload)}\n\n"

        # 2. Schedule parallel tasks
        task_map = {
            asyncio.create_task(self.evaluate_expert_async(expert, brief, fresh=fresh)): expert
            for expert in panel
        }

        verdicts: List[ExpertVerdict] = []
        pending = set(task_map.keys())

        while pending:
            # Wait for next task to complete or timeout for heartbeat (15s)
            done, pending = await asyncio.wait(
                pending, timeout=15.0, return_when=asyncio.FIRST_COMPLETED
            )

            if not done:
                # 15s elapsed without a task completing -> send heartbeat
                yield ": heartbeat\n\n"
                continue

            for finished_task in done:
                expert_obj = task_map[finished_task]
                try:
                    verdict = finished_task.result()
                except Exception as e:
                    logger.warning(
                        "Error evaluating %s: %s. Using heuristic fallback.", expert_obj.name, e
                    )
                    verdict = self.adapter._heuristic_expert_evaluation(expert_obj, brief)

                verdicts.append(verdict)

                event_data = {
                    "completed": len(verdicts),
                    "total": total,
                    "progress_label": f"{len(verdicts)} of {total} experts done",
                    "expert": verdict.model_dump(),
                }
                yield f"event: expert\ndata: {json.dumps(event_data)}\n\n"

        # 3. Report Event
        report = CouncilSynthesizer.synthesize_report(brief, verdicts)
        yield f"event: report\ndata: {report.model_dump_json()}\n\n"

        # 4. Done Event
        yield f"event: done\ndata: {json.dumps({'status': 'complete', 'report_id': report.id})}\n\n"
