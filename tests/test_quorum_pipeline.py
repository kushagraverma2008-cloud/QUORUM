import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient

from quorum.config import settings
from quorum.schemas.idea import IdeaInput, ContextPills
from quorum.brains.store import ExpertStore
from quorum.orchestrator.router import CouncilRouter
from quorum.orchestrator.evaluator import CouncilEvaluator
from quorum.api.main import app

client = TestClient(app)

def test_store_and_catalog():
    store = ExpertStore.get_instance()
    experts = store.get_all_experts()
    assert len(experts) > 500, f"Expected >500 experts, got {len(experts)}"
    
    # Check iconic expert exists and has enriched data
    pg = store.get_expert_by_id("paul_graham")
    assert pg is not None
    assert "Paul Graham" in pg.name
    assert len(pg.core_principles) > 0
    assert len(pg.common_warnings) > 0

def test_router_and_brief_generation():
    idea_input = IdeaInput(
        title="QuikD2C AI",
        pitch="An AI agent that autonomously handles customer support, returns, and inventory forecasts for direct-to-consumer e-commerce fashion brands.",
        context=ContextPills(stage="MVP", target_market="B2B", geography="Global", budget="Bootstrapped")
    )
    brief = CouncilRouter.create_brief_from_input(idea_input)
    assert brief.id.startswith("idea_")
    assert "QuikD2C" in brief.title
    assert len(brief.detected_sectors) > 0
    
    panel = CouncilRouter.recommend_panel(brief, panel_size=10)
    assert len(panel) >= 8
    expert_names = [e.name for e in panel]
    assert any("Paul" in name or "Seibel" in name for name in expert_names)

def test_council_evaluation_and_3d_network_graph():
    idea_input = IdeaInput(
        title="HyperSaaS",
        pitch="Developer API that automates edge deployment for Rust microservices.",
        context=ContextPills(stage="Idea", target_market="B2B")
    )
    brief = CouncilRouter.create_brief_from_input(idea_input)
    panel = CouncilRouter.recommend_panel(brief, panel_size=6)
    
    evaluator = CouncilEvaluator()
    report = evaluator.run_council_evaluation(brief, panel)
    
    # Assertions on scores
    assert 0.0 <= report.overall_score <= 10.0
    assert report.verdict_label in ["Strong", "Promising", "Risky", "Not viable"]
    assert 0.0 <= report.consensus_percentage <= 100.0
    
    # 8 Pillars
    pillars = report.pillar_scores
    assert 0.0 <= pillars.market_demand <= 10.0
    assert 0.0 <= pillars.differentiation <= 10.0
    assert 0.0 <= pillars.feasibility <= 10.0
    assert 0.0 <= pillars.financial_viability <= 10.0
    assert 0.0 <= pillars.execution_risk <= 10.0
    assert 0.0 <= pillars.regulatory_legal_risk <= 10.0
    assert 0.0 <= pillars.market_timing <= 10.0
    assert 0.0 <= pillars.defensibility_scale <= 10.0
    
    # Warnings, Tips, Kill Questions, Roadmap
    assert len(report.top_warnings) > 0
    assert len(report.top_tips) > 0
    assert len(report.kill_questions) > 0
    assert len(report.tactical_roadmap.days_30) > 0
    
    # Assertions on 3D Cinematic Network Graph
    graph = report.network_graph
    assert len(graph.nodes) > 10 # Core idea + 8 pillars + experts + warnings
    assert len(graph.edges) > 10
    
    core_node = next(n for n in graph.nodes if n.id == "core_idea")
    assert core_node.coords == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert core_node.radius > 20.0
    
    pillar_nodes = [n for n in graph.nodes if n.category == "pillar"]
    assert len(pillar_nodes) == 8
    
    # All nodes have 3D coordinates (x, y, z)
    for n in graph.nodes:
        assert "x" in n.coords and "y" in n.coords and "z" in n.coords

def test_api_endpoints():
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["experts_loaded"] > 500

    # 2. Analyze idea
    res = client.post("/api/ideas/analyze", json={
        "title": "CleanEnergy Grid",
        "pitch": "Decentralized battery storage coordination using smart contracts.",
        "context": {"stage": "Prototype", "target_market": "B2B", "geography": "Global", "budget": "Seed"}
    })
    assert res.status_code == 200
    brief_data = res.json()
    assert brief_data["title"] == "CleanEnergy Grid"

    # 3. Recommend panel
    res = client.post("/api/council/recommend-panel?panel_size=8", json=brief_data)
    assert res.status_code == 200
    panel_data = res.json()
    assert len(panel_data) >= 6

    # 4. Evaluate council
    res = client.post("/api/council/evaluate", json={
        "brief": brief_data,
        "panel_size": 5
    })
    assert res.status_code == 200
    report_data = res.json()
    assert "overall_score" in report_data
    assert "network_graph" in report_data
    assert len(report_data["network_graph"]["nodes"]) > 0

    # 5. Expert follow-up chat
    res = client.post("/api/council/expert-chat", json={
        "expert_id": "paul_graham",
        "user_message": "Paul, how do I find my very first 10 battery storage customers?"
    })
    assert res.status_code == 200
    chat_data = res.json()
    assert "reply" in chat_data
    # 6. Static UI routes
    res = client.get("/")
    assert res.status_code == 200
    assert "QUORUM" in res.text

    res = client.get("/war-room")
    assert res.status_code == 200

    res = client.get("/curation")
    assert res.status_code == 200

    res = client.get("/theater")
    assert res.status_code == 200

    res = client.get("/report")
    assert res.status_code == 200


def test_ui_backend_wiring():
    """Verify all static HTML pages have backend wiring scripts injected."""
    from pathlib import Path
    static_dir = Path("src/quorum/static")

    wiring_checks = {
        "index.html": ["/api/ideas/analyze", "/api/council/evaluate", "/api/council/expert-chat"],
        "brief_curation.html": ["quorum_brief", "conveneCouncil", "/api/council/recommend-panel"],
        "war_room_console.html": ["quorum_brief", "advanceToInterrogation", "quorum_panel"],
        "council_theater_analysis.html": ["runCouncilStream", "/api/council/evaluate", "quorum_report"],
        "council_report_stage4.html": ["quorum_report", "populateHeroCard", "generateMarkdownReport"],
    }

    for filename, checks in wiring_checks.items():
        html_path = static_dir / filename
        assert html_path.exists(), f"Missing static file: {filename}"
        content = html_path.read_text(encoding='utf-8')
        for check in checks:
            assert check in content, f"{filename} missing wiring: '{check}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

