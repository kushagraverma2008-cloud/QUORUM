import time
import subprocess
import sys
import os
import re
from pathlib import Path

workspace = Path(__file__).resolve().parent
sys.path.insert(0, str(workspace / "src"))

print("--- POST-UPGRADE MEASUREMENT ---")

# 1. Pytest duration
t0 = time.time()
res = subprocess.run([sys.executable, "-m", "pytest", "tests/"], cwd=str(workspace), capture_output=True, text=True)
t_pytest = time.time() - t0
print(f"PYTEST_TIME: {t_pytest:.2f}s (code: {res.returncode})")

# 2. Package count
res_pip = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
pkg_lines = [line for line in res_pip.stdout.strip().split("\n")[2:] if line.strip()]
print(f"PACKAGE_COUNT: {len(pkg_lines)}")

# 3. Server startup time
t0 = time.time()
from quorum.api.main import app
from quorum.engine import ExpertStore
store = ExpertStore.get_instance()
t_startup = time.time() - t0
print(f"SERVER_STARTUP_TIME: {t_startup:.4f}s (loaded {store.count()} experts, {len(store._deep_profile_ids)} deep)")

# 4. Page weight
static_dir = workspace / "src" / "quorum" / "static"
index_html = (static_dir / "index.html").stat().st_size
app_css = (static_dir / "app.css").stat().st_size
app_js = (static_dir / "app.js").stat().st_size
total_local_bytes = index_html + app_css + app_js

print(f"INDEX_HTML_SIZE: {index_html / 1024:.2f} KB ({index_html} bytes)")
print(f"APP_CSS_SIZE: {app_css / 1024:.2f} KB ({app_css} bytes)")
print(f"APP_JS_SIZE: {app_js / 1024:.2f} KB ({app_js} bytes)")
print(f"TOTAL_FRONTEND_LOCAL_WEIGHT: {total_local_bytes / 1024:.2f} KB ({total_local_bytes} bytes)")

with open(static_dir / "index.html", "r", encoding="utf-8") as f:
    content = f.read()

scripts = re.findall(r'<script\s+src=["\'](.*?)["\']', content)
links = re.findall(r'<link\s+[^>]*href=["\'](.*?)["\']', content)
print(f"EXTERNAL_SCRIPTS: {scripts}")
print(f"EXTERNAL_LINKS: {links}")

# 5. Measure "run council" offline latency
from quorum.schemas import IdeaInput
from quorum.engine import CouncilRouter, CouncilEvaluator, CouncilSynthesizer

submission = IdeaInput(
    title="EcoDeliver Autonomous Cargo Bikes",
    pitch="Urban last-mile parcel delivery causes heavy emissions and traffic. We build autonomous cargo e-bikes reducing last-mile delivery cost and carbon by 60% with B2B delivery fee per drop."
)
brief = CouncilRouter.create_brief_from_input(submission)
panel = CouncilRouter.recommend_panel(brief, panel_size=6, seed=42)
print(f"Recommended panel: {[p.name for p in panel]}")

evaluator = CouncilEvaluator()
t_start = time.time()

# First expert
first_verdict = evaluator.evaluate_expert_sync(panel[0], brief, fresh=True)
t_first = time.time() - t_start
print(f"TIME_TO_FIRST_EXPERT (offline): {t_first:.4f}s (source: {first_verdict.source})")

# Full council
verdicts = [first_verdict]
for p in panel[1:]:
    verdicts.append(evaluator.evaluate_expert_sync(p, brief, fresh=True))

report = CouncilSynthesizer.synthesize_report(brief, verdicts)
t_full = time.time() - t_start
print(f"TIME_TO_FULL_REPORT (offline): {t_full:.4f}s (source: {report.source})")
print(f"Overall score: {report.overall_score}/10, Verdict: {report.verdict_label}")
print(f"Report structure keys: expert_roster={len(report.expert_roster)}, 2D nodes={len(report.network_graph.nodes)}, 2D edges={len(report.network_graph.edges)}")
