import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List

from quorum.schemas import (
    ConsensusDissentMap,
    CouncilReport,
    DisagreementPoint,
    ExpertVerdict,
    IdeaBrief,
    KillQuestion,
    NetworkEdge,
    NetworkGraph,
    NetworkNode,
    PillarScores,
    TacticalRoadmap,
    TopTip,
    TopWarning,
)


class CouncilSynthesizer:
    """Consolidates individual expert verdicts into a rigorous, grounded executive consensus report."""

    @classmethod
    def synthesize_report(cls, brief: IdeaBrief, verdicts: List[ExpertVerdict]) -> CouncilReport:
        if not verdicts:
            raise ValueError("Cannot synthesize council report with zero verdicts.")

        # 1. Deterministic Pillar Averages & Composite Score
        total_weight = sum(v.weight for v in verdicts) or 1.0

        p_demand = round(
            sum(v.pillar_ratings.market_demand * v.weight for v in verdicts) / total_weight, 1
        )
        p_diff = round(
            sum(v.pillar_ratings.differentiation * v.weight for v in verdicts) / total_weight, 1
        )
        p_feas = round(
            sum(v.pillar_ratings.feasibility * v.weight for v in verdicts) / total_weight, 1
        )
        p_fin = round(
            sum(v.pillar_ratings.financial_viability * v.weight for v in verdicts) / total_weight, 1
        )
        p_exec = round(
            sum(v.pillar_ratings.execution_risk * v.weight for v in verdicts) / total_weight, 1
        )
        p_reg = round(
            sum(v.pillar_ratings.regulatory_legal_risk * v.weight for v in verdicts) / total_weight,
            1,
        )
        p_timing = round(
            sum(v.pillar_ratings.market_timing * v.weight for v in verdicts) / total_weight, 1
        )
        p_defens = round(
            sum(v.pillar_ratings.defensibility_scale * v.weight for v in verdicts) / total_weight, 1
        )

        pillar_scores = PillarScores(
            market_demand=p_demand,
            differentiation=p_diff,
            feasibility=p_feas,
            financial_viability=p_fin,
            execution_risk=p_exec,
            regulatory_legal_risk=p_reg,
            market_timing=p_timing,
            defensibility_scale=p_defens,
        )

        all_pillars = [p_demand, p_diff, p_feas, p_fin, p_exec, p_reg, p_timing, p_defens]
        overall_score = round(sum(all_pillars) / len(all_pillars), 1)

        # 2. Verdict Band Thresholds
        if overall_score >= 7.5:
            verdict_label = "Strong"
        elif overall_score >= 5.5:
            verdict_label = "Promising but risky"
        elif overall_score >= 4.0:
            verdict_label = "Weak"
        else:
            verdict_label = "Do not build as-is"

        # 3. Source Detection ("Honest Fallback" check)
        is_all_llm = all(v.source == "llm" for v in verdicts)
        report_source = "llm" if is_all_llm else "offline"

        # 4. Synthesize Warnings & Tips Ranked by Occurrence / Impact
        warning_counts = Counter()
        warning_sources: Dict[str, List[str]] = {}
        for v in verdicts:
            for w in v.specific_warnings:
                w_clean = w.strip()
                if w_clean:
                    warning_counts[w_clean] += 1
                    warning_sources.setdefault(w_clean, []).append(v.expert_name)

        top_warnings: List[TopWarning] = []
        for w_text, count in warning_counts.most_common(5):
            top_warnings.append(
                TopWarning(
                    warning=w_text,
                    severity="Critical" if count >= 2 or overall_score < 6.0 else "High",
                    experts_count=count,
                    flagged_by=warning_sources.get(w_text, []),
                )
            )

        tip_counts = Counter()
        tip_sources: Dict[str, List[str]] = {}
        for v in verdicts:
            for t in v.actionable_tips:
                t_clean = t.strip()
                if t_clean:
                    tip_counts[t_clean] += 1
                    tip_sources.setdefault(t_clean, []).append(v.expert_name)

        top_tips: List[TopTip] = []
        for t_text, count in tip_counts.most_common(5):
            top_tips.append(
                TopTip(tip=t_text, experts_count=count, recommended_by=tip_sources.get(t_text, []))
            )

        # 5. Kill Questions from Each Expert
        kill_questions: List[KillQuestion] = [
            KillQuestion(
                question=v.kill_question,
                raised_by=v.expert_name,
                rationale=f"Stance: {v.stance_archetype}. Score: {v.overall_score}/10.",
            )
            for v in verdicts
            if v.kill_question
        ]

        # 6. Disagreements (Score Delta >= 3.0 on any pillar)
        disagreements: List[DisagreementPoint] = []
        pillar_names = [
            ("Market Demand", "market_demand"),
            ("Differentiation", "differentiation"),
            ("Feasibility", "feasibility"),
            ("Financial Viability", "financial_viability"),
            ("Execution Risk", "execution_risk"),
            ("Regulatory & Legal Safety", "regulatory_legal_risk"),
            ("Market Timing", "market_timing"),
            ("Defensibility at Scale", "defensibility_scale"),
        ]

        for p_label, p_attr in pillar_names:
            scores_with_experts = [
                (getattr(v.pillar_ratings, p_attr), v.expert_name) for v in verdicts
            ]
            scores_with_experts.sort(key=lambda x: x[0])
            min_score, skeptic_name = scores_with_experts[0]
            max_score, bull_name = scores_with_experts[-1]

            if (max_score - min_score) >= 3.0:
                disagreements.append(
                    DisagreementPoint(
                        topic=f"{p_label} Split ({min_score} vs {max_score})",
                        optimist_view=f"{bull_name} views {p_label.lower()} as a distinct competitive strength ({max_score}/10).",
                        optimists=[bull_name],
                        skeptic_view=f"{skeptic_name} flags major structural vulnerability in {p_label.lower()} ({min_score}/10).",
                        skeptics=[skeptic_name],
                    )
                )

        consensus_points = [
            f"The council concurs with an average score of {p_val}/10 on {label}."
            for label, p_attr in pillar_names
            if (p_val := getattr(pillar_scores, p_attr)) >= 7.0 or p_val <= 4.5
        ]
        if not consensus_points:
            consensus_points.append(
                "The council is divided across the majority of fundamental operational pillars."
            )

        consensus_map = ConsensusDissentMap(
            consensus_points=consensus_points[:4], sharp_disagreements=disagreements[:4]
        )

        # 7. Grounded Tactical Roadmap from Real Tips & Warnings
        raw_tips = [t.tip for t in top_tips]
        raw_warnings = [w.warning for w in top_warnings]

        roadmap_30 = [
            f'Directly stress-test primary kill question: "{kill_questions[0].question}"'
            if kill_questions
            else "Interview 20 target users on urgent pain.",
            raw_tips[0] if raw_tips else "Build smallest concierge MVP to test willingness to pay.",
            f"De-risk existential warning: {raw_warnings[0]}"
            if raw_warnings
            else "Secure first 5 paying LOIs before engineering.",
        ]
        roadmap_90 = [
            raw_tips[1] if len(raw_tips) > 1 else "Validate unit economics with live cohorts.",
            f"Overcome secondary friction point: {raw_warnings[1]}"
            if len(raw_warnings) > 1
            else "Achieve repeatable organic referral loops.",
            "Establish quantifiable moat against copycats.",
        ]
        roadmap_180 = [
            "Formalize proprietary data loops and compounding distribution advantages.",
            "Scale gross margins above 70% while defending against competitor price-slashing.",
        ]

        roadmap = TacticalRoadmap(
            days_30=roadmap_30[:3], days_90=roadmap_90[:3], days_180=roadmap_180[:2]
        )

        # 8. Tailored Actions for Founder's Specific Situation (Phase 2 Smarter Assistant)
        ctx = brief.context
        tailored: List[str] = []
        if ctx.team_size == "Solo Founder":
            tailored.append(
                f"As a solo founder, avoid premature automation. Personally execute initial customer interactions in {ctx.geography} before writing scalable code."
            )
        elif ctx.team_size in ("2-3 Co-founders", "Small Team (4-10)"):
            tailored.append(
                f"Divide ownership clearly: assign one co-founder 100% to customer discovery in {ctx.target_market} and one to rapid product iteration."
            )

        if ctx.runway_budget == "Bootstrapped":
            tailored.append(
                "With bootstrapped runway, aim for negative cashflow duration under 60 days. Demand upfront deposits or pre-orders to self-fund delivery."
            )
        elif ctx.runway_budget in ("Pre-Seed ($50k-$250k)", "Seed ($250k-$2M)"):
            tailored.append(
                "Deploy capital strictly toward proving retention and distribution efficiency. Do not increase burn until payback period is under 12 months."
            )

        if ctx.primary_goal == "Validate Urgency & Demand":
            tailored.append(
                f"Immediate validation priority: interview 15 target users in {ctx.geography} focused on testing: '{kill_questions[0].question if kill_questions else 'customer willingness to pay'}'."
            )
        elif ctx.primary_goal == "Secure Pilot LOIs":
            tailored.append(
                "Draft a 1-page pilot term sheet outlining 3 quantifiable success criteria to secure signed LOIs without custom feature bloat."
            )
        elif ctx.primary_goal == "Raise Angel/Pre-Seed":
            tailored.append(
                f"Prepare pitch defense addressing the top existential risk: '{top_warnings[0].warning if top_warnings else 'defensibility'}'. Investors will probe this first."
            )
        else:
            tailored.append(
                f"Target launch benchmark: reach 20 daily active operators in {ctx.target_market} achieving >40% retention."
            )

        # Prompt injection security check (Phase 3 Security)
        raw_check = (brief.raw_pitch + " " + brief.solution_description).lower()
        injection_phrases = [
            "ignore previous instructions",
            "ignore all previous",
            "system prompt",
            "you are now",
            "disregard all",
            "override instructions",
        ]
        all_pillars_max = all(
            getattr(pillar_scores, k) >= 9.5
            for k in [
                "market_demand",
                "differentiation",
                "feasibility",
                "financial_viability",
                "execution_risk",
                "regulatory_legal_risk",
                "market_timing",
                "defensibility_scale",
            ]
        )
        is_suspicious = any(phrase in raw_check for phrase in injection_phrases) or all_pillars_max

        # 9. 2D Network Graph (Clean layout without backend x/y/z)
        nodes: List[NetworkNode] = []
        edges: List[NetworkEdge] = []

        # Color mapping by score
        for v in verdicts:
            color = (
                "#AFF833"
                if v.overall_score >= 7.0
                else ("#00E5FF" if v.overall_score >= 5.5 else "#FF3B30")
            )
            nodes.append(
                NetworkNode(
                    id=v.expert_id,
                    name=v.expert_name,
                    archetype=v.stance_archetype,
                    score=v.overall_score,
                    color=color,
                )
            )

        # Compute Pairwise Tension Edges
        total_divergence = 0.0
        edge_count = 0
        for i in range(len(verdicts)):
            for j in range(i + 1, len(verdicts)):
                v_a = verdicts[i]
                v_b = verdicts[j]

                # Manhattan distance across the 8 pillars
                score_deltas = [
                    abs(v_a.pillar_ratings.market_demand - v_b.pillar_ratings.market_demand),
                    abs(v_a.pillar_ratings.differentiation - v_b.pillar_ratings.differentiation),
                    abs(v_a.pillar_ratings.feasibility - v_b.pillar_ratings.feasibility),
                    abs(
                        v_a.pillar_ratings.financial_viability
                        - v_b.pillar_ratings.financial_viability
                    ),
                    abs(v_a.pillar_ratings.execution_risk - v_b.pillar_ratings.execution_risk),
                    abs(
                        v_a.pillar_ratings.regulatory_legal_risk
                        - v_b.pillar_ratings.regulatory_legal_risk
                    ),
                    abs(v_a.pillar_ratings.market_timing - v_b.pillar_ratings.market_timing),
                    abs(
                        v_a.pillar_ratings.defensibility_scale
                        - v_b.pillar_ratings.defensibility_scale
                    ),
                ]
                mean_delta = sum(score_deltas) / len(score_deltas)
                tension = round(min(1.0, mean_delta / 4.0), 2)
                total_divergence += tension
                edge_count += 1

                reason = (
                    "Strong alignment"
                    if tension < 0.25
                    else ("Moderate debate" if tension < 0.55 else "Sharp philosophical divergence")
                )

                edges.append(
                    NetworkEdge(
                        source=v_a.expert_id, target=v_b.expert_id, tension=tension, reason=reason
                    )
                )

        overall_tension = round(total_divergence / max(1, edge_count), 2)
        network_graph = NetworkGraph(
            nodes=nodes,
            edges=edges,
            tension_index=overall_tension,
            cluster_tags=brief.detected_sectors,
        )

        # 9. Concise Executive Summary & One-Paragraph Verdict
        critique_snippets = [
            f'{v.expert_name}: "{v.opinion_critique[:120].strip()}..."' for v in verdicts[:3]
        ]
        exec_summary = (
            f"Council Verdict: {verdict_label} ({overall_score}/10.0). "
            f"Evaluated across 8 pillars by {len(verdicts)} domain personas. "
            f"Primary strengths centered on {pillar_names[max(range(8), key=lambda k: all_pillars[k])][0]} ({max(all_pillars)}/10), "
            f"while primary risk concentrated in {pillar_names[min(range(8), key=lambda k: all_pillars[k])][0]} ({min(all_pillars)}/10)."
        )
        council_p = " | ".join(critique_snippets)

        return CouncilReport(
            id=f"rep_{uuid.uuid4().hex[:8]}",
            idea_id=brief.id,
            title=brief.title,
            source=report_source,
            overall_score=overall_score,
            verdict_label=verdict_label,
            confidence_index=0.88,
            consensus_percentage=round(max(20.0, 100.0 - (overall_tension * 60.0)), 1),
            executive_summary=exec_summary,
            council_in_one_paragraph=council_p,
            pillar_scores=pillar_scores,
            top_warnings=top_warnings,
            top_tips=top_tips,
            kill_questions=kill_questions,
            tailored_actions=tailored,
            is_suspicious_input=is_suspicious,
            consensus_dissent=consensus_map,
            tactical_roadmap=roadmap,
            expert_roster=verdicts,
            network_graph=network_graph,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
