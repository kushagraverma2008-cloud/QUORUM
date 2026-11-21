import json
import os
from pathlib import Path
import sys

# Ensure src in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quorum.schemas import IdeaInput, ContextPills
from quorum.engine import CouncilRouter, CouncilEvaluator

def generate_samples():
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    evaluator = CouncilEvaluator()

    # Sample 1: AegisHealth AI (Solo Healthcare B2B)
    idea1 = IdeaInput(
        title="AegisHealth AI",
        pitch="An ambient listening and clinical intelligence agent for solo general practitioners in community clinics. Aegis securely transcribes patient encounters into structured SOAP notes, cross-references regional pharmaceutical formularies, and highlights contraindications before prescriptions are finalized.",
        context=ContextPills(
            stage="Prototype",
            target_market="Healthcare B2B",
            team_size="Solo Founder",
            runway_budget="Bootstrapped",
            primary_goal="Validate Urgency & Demand",
            geography="North America"
        )
    )
    brief1 = CouncilRouter.create_brief_from_input(idea1)
    panel1 = CouncilRouter.recommend_panel(brief1, panel_size=6, seed=101)
    report1 = evaluator.run_council_evaluation(brief1, panel1)

    file1 = examples_dir / "sample_report_1.json"
    with open(file1, "w", encoding="utf-8") as f:
        json.dump(report1.model_dump(), f, indent=2)
    print(f"Generated {file1} (score: {report1.overall_score}, verdict: {report1.verdict_label})")

    # Sample 2: LogiFleet Dynamic (Enterprise Freight)
    idea2 = IdeaInput(
        title="LogiFleet Dynamic",
        pitch="Autonomous freight coordination platform connecting mid-sized regional trucking carriers to optimize empty backhaul miles. Real-time telematics integration matches idle trailers with enterprise spot-freight auctions, cutting empty deadhead miles by 24% while preserving dispatcher control.",
        context=ContextPills(
            stage="MVP",
            target_market="Enterprise Logistics",
            team_size="2-3 Co-founders",
            runway_budget="Seed (<$500k)",
            primary_goal="Secure Pilot LOIs",
            geography="Global"
        )
    )
    brief2 = CouncilRouter.create_brief_from_input(idea2)
    panel2 = CouncilRouter.recommend_panel(brief2, panel_size=6, seed=202)
    report2 = evaluator.run_council_evaluation(brief2, panel2)

    file2 = examples_dir / "sample_report_2.json"
    with open(file2, "w", encoding="utf-8") as f:
        json.dump(report2.model_dump(), f, indent=2)
    print(f"Generated {file2} (score: {report2.overall_score}, verdict: {report2.verdict_label})")

if __name__ == "__main__":
    generate_samples()

