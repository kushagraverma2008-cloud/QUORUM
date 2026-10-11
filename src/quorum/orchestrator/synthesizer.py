import math
import uuid
from datetime import datetime
from typing import List, Dict, Any
from quorum.schemas.idea import IdeaBrief
from quorum.schemas.evaluation import ExpertVerdict, PillarScores
from quorum.schemas.report import (
    CouncilReport,
    TopWarning,
    TopTip,
    KillQuestion,
    DisagreementPoint,
    ConsensusDissentMap,
    TacticalRoadmap,
    NetworkGraph,
    NetworkNode,
    NetworkEdge
)

class CouncilSynthesizer:
    """Synthesizes individual expert verdicts into an executive CouncilReport and 3D NetworkGraph."""

    @classmethod
    def synthesize_report(cls, brief: IdeaBrief, verdicts: List[ExpertVerdict]) -> CouncilReport:
        if not verdicts:
            raise ValueError("Cannot synthesize report with zero verdicts.")

        # 1. Compute Overall Score and Pillar Averages
        total_weight = sum(v.weight for v in verdicts)
        weighted_overall = sum(v.overall_score * v.weight for v in verdicts) / total_weight
        overall_score = round(weighted_overall, 1)

        # 8 Pillar Scores
        pillar_demand = round(sum(v.pillar_ratings.market_demand * v.weight for v in verdicts) / total_weight, 1)
        pillar_diff = round(sum(v.pillar_ratings.differentiation * v.weight for v in verdicts) / total_weight, 1)
        pillar_feas = round(sum(v.pillar_ratings.feasibility * v.weight for v in verdicts) / total_weight, 1)
        pillar_fin = round(sum(v.pillar_ratings.financial_viability * v.weight for v in verdicts) / total_weight, 1)
        pillar_exec = round(sum(v.pillar_ratings.execution_risk * v.weight for v in verdicts) / total_weight, 1)
        pillar_reg = round(sum(v.pillar_ratings.regulatory_legal_risk * v.weight for v in verdicts) / total_weight, 1)
        pillar_timing = round(sum(v.pillar_ratings.market_timing * v.weight for v in verdicts) / total_weight, 1)
        pillar_defens = round(sum(v.pillar_ratings.defensibility_scale * v.weight for v in verdicts) / total_weight, 1)

        pillars = PillarScores(
            market_demand=pillar_demand,
            differentiation=pillar_diff,
            feasibility=pillar_feas,
            financial_viability=pillar_fin,
            execution_risk=pillar_exec,
            regulatory_legal_risk=pillar_reg,
            market_timing=pillar_timing,
            defensibility_scale=pillar_defens,
        )

        # 2. Verdict Label
        if overall_score >= 8.0:
            verdict_label = "Strong"
        elif overall_score >= 6.0:
            verdict_label = "Promising"
        elif overall_score >= 4.0:
            verdict_label = "Risky"
        else:
            verdict_label = "Not viable"

        # 3. Consensus & Agreement Index
        scores = [v.overall_score for v in verdicts]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)
        
        # Agreement: standard deviation under 1.0 => high consensus
        consensus_pct = round(max(40.0, min(98.0, 100.0 - (std_dev * 18.0))), 1)
        confidence_idx = round(min(0.98, max(0.65, 1.0 - (std_dev / 10.0))), 2)

        # 4. Warnings aggregation
        warning_counts: Dict[str, List[str]] = {}
        for v in verdicts:
            for w in v.specific_warnings:
                w_clean = w.strip()
                if w_clean not in warning_counts:
                    warning_counts[w_clean] = []
                warning_counts[w_clean].append(v.expert_name)

        sorted_warnings = sorted(warning_counts.items(), key=lambda x: len(x[1]), reverse=True)
        top_warnings = [
            TopWarning(
                warning=w_text,
                severity="Critical" if len(experts) > len(verdicts) // 3 else "High",
                experts_count=len(experts),
                flagged_by=experts
            )
            for w_text, experts in sorted_warnings[:5]
        ]

        # 5. Tips aggregation
        tip_counts: Dict[str, List[str]] = {}
        for v in verdicts:
            for t in v.actionable_tips:
                t_clean = t.strip()
                if t_clean not in tip_counts:
                    tip_counts[t_clean] = []
                tip_counts[t_clean].append(v.expert_name)

        sorted_tips = sorted(tip_counts.items(), key=lambda x: len(x[1]), reverse=True)
        top_tips = [
            TopTip(
                tip=t_text,
                experts_count=len(experts),
                recommended_by=experts
            )
            for t_text, experts in sorted_tips[:5]
        ]

        # 6. Kill Questions
        kill_questions = [
            KillQuestion(
                question=v.kill_question,
                raised_by=v.expert_name,
                rationale=f"Highlighted by {v.expert_name} ({v.stance_archetype}) as a decisive make-or-break hurdle."
            )
            for v in verdicts[:5]
        ]

        # 7. Consensus vs Dissent
        optimists = [v.expert_name for v in verdicts if v.overall_score >= 6.5]
        skeptics = [v.expert_name for v in verdicts if v.overall_score < 6.5]
        
        disagreements = []
        if skeptics and optimists:
            disagreements.append(
                DisagreementPoint(
                    topic="Distribution Wedge vs Market Crowding",
                    optimist_view="Believes initial focused wedge can carve out a sticky customer base.",
                    optimists=optimists[:3],
                    skeptic_view="Warns customer acquisition costs will outpace organic word-of-mouth.",
                    skeptics=skeptics[:3]
                )
            )

        consensus_map = ConsensusDissentMap(
            consensus_points=[
                f"Consensus that the initial product scope must be tightly constrained before scaling.",
                f"Agreement that proving customer willingness to pay within 30 days is mandatory.",
                f"The venture's highest upside relies on solving {brief.problem_statement.lower()[:80]}."
            ],
            sharp_disagreements=disagreements
        )

        # 8. Tactical Roadmap
        roadmap = TacticalRoadmap(
            days_30=[
                "Interview 15 target customers specifically about their existing workarounds.",
                "Build a zero-code or lightweight functional prototype testing only the core transaction.",
                "Answer the top kill question: " + (kill_questions[0].question if kill_questions else "Validate demand")
            ],
            days_90=[
                "Acquire first 10 paying customers without relying on paid advertising.",
                "Measure customer retention and weekly active usage frequency.",
                "Address distribution friction identified by the skeptical council members."
            ],
            days_180=[
                "Establish predictable unit economics (LTV/CAC ratio > 3x).",
                "Begin institutional fundraising or sustainable reinvestment of cashflows.",
                "Reinforce defensibility through data moats or network effects."
            ]
        )

        # 9. 3D Cinematic Network Graph Generation
        network_graph = cls._build_3d_network_graph(brief, pillars, verdicts, top_warnings, std_dev)

        council_in_one_p = (
            f"The Council rates '{brief.title}' as {verdict_label} ({overall_score}/10) with {consensus_pct}% panel consensus. "
            f"While feasibility ({pillar_feas}/10) and regulatory safety ({pillar_reg}/10) are solid, the primary vulnerability "
            f"is defensibility ({pillar_defens}/10) and distribution friction. "
            f"Before deploying capital, the team must definitively answer the panel's top kill questions and prove organic customer commitment."
        )

        from datetime import timezone
        report = CouncilReport(
            id=f"rep_{uuid.uuid4().hex[:8]}",
            idea_id=brief.id,
            title=brief.title,
            overall_score=overall_score,
            verdict_label=verdict_label,
            confidence_index=confidence_idx,
            consensus_percentage=consensus_pct,
            executive_summary=f"Evaluation of {brief.title} across {len(verdicts)} verified industry leaders.",
            council_in_one_paragraph=council_in_one_p,
            pillar_scores=pillars,
            top_warnings=top_warnings,
            top_tips=top_tips,
            kill_questions=kill_questions,
            consensus_dissent=consensus_map,
            tactical_roadmap=roadmap,
            expert_roster=verdicts,
            network_graph=network_graph,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        return report

    @classmethod
    def _build_3d_network_graph(
        cls, 
        brief: IdeaBrief, 
        pillars: PillarScores, 
        verdicts: List[ExpertVerdict],
        top_warnings: List[TopWarning],
        std_dev: float
    ) -> NetworkGraph:
        """Constructs a cinematic 3D force/orbital graph structure for Three.js/WebGL renderers."""
        nodes: List[NetworkNode] = []
        edges: List[NetworkEdge] = []

        # 1. Central Core Node (The Venture Idea)
        nodes.append(NetworkNode(
            id="core_idea",
            label=brief.title,
            category="idea",
            score=round(sum(v.overall_score for v in verdicts) / len(verdicts), 1),
            radius=24.0,
            color="#38bdf8", # Radiant cyan
            coords={"x": 0.0, "y": 0.0, "z": 0.0},
            metadata={"one_liner": brief.one_liner, "sectors": brief.detected_sectors}
        ))

        # 2. 8 Pillar Nodes in an inner orbital ring (Radius R=80)
        pillar_list = [
            ("p_demand", "Market Demand", pillars.market_demand, "#10b981"),
            ("p_diff", "Differentiation", pillars.differentiation, "#8b5cf6"),
            ("p_feas", "Feasibility", pillars.feasibility, "#06b6d4"),
            ("p_fin", "Financial Viability", pillars.financial_viability, "#f59e0b"),
            ("p_exec", "Execution Safety", pillars.execution_risk, "#ec4899"),
            ("p_reg", "Legal Safety", pillars.regulatory_legal_risk, "#3b82f6"),
            ("p_timing", "Market Timing", pillars.market_timing, "#a855f7"),
            ("p_defens", "Defensibility", pillars.defensibility_scale, "#6366f1"),
        ]

        for idx, (p_id, p_label, p_score, p_color) in enumerate(pillar_list):
            angle = (2.0 * math.pi * idx) / len(pillar_list)
            r = 90.0
            x = round(r * math.cos(angle), 2)
            y = round(r * math.sin(angle), 2)
            z = round(15.0 * math.sin(angle * 2), 2)

            nodes.append(NetworkNode(
                id=p_id,
                label=p_label,
                category="pillar",
                score=p_score,
                radius=14.0,
                color=p_color,
                coords={"x": x, "y": y, "z": z},
                metadata={"pillar_name": p_label}
            ))

            # Edge from core to pillar
            edges.append(NetworkEdge(
                source="core_idea",
                target=p_id,
                relation="anchors",
                weight=round(p_score / 10.0, 2),
                color=p_color,
                animated=True,
                pulse_rate=1.2
            ))

        # 3. Outer Sphere: Expert Nodes (Radius R=160 to 220)
        n_experts = len(verdicts)
        for idx, v in enumerate(verdicts):
            phi = math.acos(-1.0 + (2.0 * idx) / max(1, n_experts))
            theta = math.sqrt(n_experts * math.pi) * phi
            r_expert = 175.0 + (10.0 * (idx % 3))
            
            x = round(r_expert * math.sin(phi) * math.cos(theta), 2)
            y = round(r_expert * math.sin(phi) * math.sin(theta), 2)
            z = round(r_expert * math.cos(phi), 2)

            is_optimist = v.overall_score >= 6.5
            expert_color = "#22c55e" if is_optimist else "#f43f5e" # emerald for positive, rose for skeptic
            node_id = f"exp_{v.expert_id}"

            nodes.append(NetworkNode(
                id=node_id,
                label=v.expert_name,
                category="expert",
                score=v.overall_score,
                radius=11.0,
                color=expert_color,
                coords={"x": x, "y": y, "z": z},
                metadata={
                    "archetype": v.stance_archetype,
                    "verdict": v.verdict_label,
                    "role": v.role_or_title
                }
            ))

            # Edge from expert to core idea (support or conflict)
            edges.append(NetworkEdge(
                source=node_id,
                target="core_idea",
                relation="supports" if is_optimist else "conflicts",
                weight=round(v.overall_score / 10.0, 2),
                color=expert_color,
                animated=True,
                pulse_rate=1.5 if not is_optimist else 0.8
            ))

            # Connect to closest affinity pillar
            closest_pillar = "p_demand" if "Market" in v.stance_archetype else (
                "p_feas" if "Operator" in v.stance_archetype else "p_diff"
            )
            edges.append(NetworkEdge(
                source=node_id,
                target=closest_pillar,
                relation="scores",
                weight=0.6,
                color="#64748b",
                animated=False,
                pulse_rate=0.5
            ))

        # 4. Satellite Warning Nodes
        for w_idx, w in enumerate(top_warnings[:3]):
            w_id = f"warn_{w_idx}"
            w_r = 130.0
            w_ang = (2.0 * math.pi * w_idx) / 3.0 + 0.5
            nodes.append(NetworkNode(
                id=w_id,
                label=w.warning[:30] + "...",
                category="warning",
                radius=9.0,
                color="#e11d48", # Neon Crimson
                coords={
                    "x": round(w_r * math.cos(w_ang), 2),
                    "y": round(w_r * math.sin(w_ang), 2),
                    "z": 45.0
                },
                metadata={"full_text": w.warning, "flagged_by": w.flagged_by}
            ))
            edges.append(NetworkEdge(
                source="core_idea",
                target=w_id,
                relation="warns",
                weight=0.9,
                color="#e11d48",
                animated=True,
                pulse_rate=2.0
            ))

        return NetworkGraph(
            nodes=nodes,
            edges=edges,
            cluster_tags=brief.detected_sectors + ["Pillars", "Experts", "Hazards"],
            tension_index=round(std_dev, 2)
        )
