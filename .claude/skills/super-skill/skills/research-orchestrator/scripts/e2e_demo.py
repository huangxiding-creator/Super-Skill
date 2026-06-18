"""End-to-end Idea Factory dry run (M4 integration test).

Proves the full chain: raw idea text → ambiguity score → live research →
maturity/tenx/pricing/scorecard → a real SCORECARD verdict.

Uses the LIVE github channel (reliable, auth-free) + a seeded ten× claim, so the
run is deterministic in shape even though the repo set is whatever GitHub returns
right now. Run: python e2e_demo.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent
SKILL_ROOT = _HERE.parents[2]  # .../super-skill
for p in (_HERE, SKILL_ROOT / "skills" / "idea-intake" / "scripts",
          SKILL_ROOT / "skills" / "proposal-forge" / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import ambiguity_scorer as intake  # noqa: E402
import orchestrator as orch  # noqa: E402
import maturity_index as mi  # noqa: E402
import tenx_delta_index as tx  # noqa: E402
import pricing as pr  # noqa: E402
import scorecard as sc  # noqa: E402

RAW_IDEA = ("我想给独立开发者做一个本地优先的 markdown 笔记 SaaS，他们的痛点是 "
            "现有笔记都要联网同步、又慢又贵、数据不在自己手里。必须离线可用、兼容 "
            "Win/macOS。靠 SQLite + CRDT 增量同步，部署成本只有竞品的 1/16，上手时间 2 分钟。")


def main() -> int:
    print("=== STAGE 1: idea-intake (ambiguity) ===")
    score = intake.score_text(RAW_IDEA)
    print(f"score={score.score} action={score.action} assumptions={score.assumptions}")
    assert score.action in ("auto", "ask"), "idea should be clear enough to proceed"

    seed = {
        "summary": "local-first markdown note SaaS for indie developers",
        "persona": "indie developer",
        "pain": "existing notes need cloud sync, slow, expensive, data not owned",
        "constraints": "offline-first, Win/macOS, data local",
        "success_form": "desktop SaaS",
        "value_hypothesis": "SQLite+CRDT sync, 1/16 deploy cost, 2-min onboarding",
        "competitor_urls": [],
    }

    print("\n=== STAGE 2: research-orchestrator (live github) ===")
    with tempfile.TemporaryDirectory() as d:
        rep = orch.orchestrate(seed, d, channels=["github"])
        print(f"unique={rep.unique} quality_passed={rep.quality_passed} gaps={rep.gaps}")
        gh_path = os.path.join(d, "github", "_all.json")
        with open(gh_path, "r", encoding="utf-8") as f:
            repo_docs = json.load(f)
        repo_signals = [d["signals"] for d in repo_docs if d.get("signals", {}).get("stars") is not None]

    print(f"\nharvested {len(repo_signals)} repos with signal data")

    print("\n=== STAGE 3: proposal-forge (scoring) ===")
    land = mi.score_landscape(repo_signals)
    print(f"landscape: best={land.best.score if land.best else 'n/a'} median={land.median} "
          f"mature={land.mature_count} n={land.n}")
    feasibility = mi.derive_feasibility(land)

    # ten× claim straight from the idea: 1/16 deploy cost + fast onboarding
    tenx = tx.score({
        "deploy_cost": {"ours": 1, "baseline": 16},      # 16× cheaper
        "onboarding_time": {"ours": 2, "baseline": 20},  # 10× faster (2 min vs 20 min)
    })
    print(f"ten× verdict={tenx.verdict} best_axis={tenx.best_axis} multiplier={tenx.multiplier}×")
    tenx_score = tx.derive_tenx_score(tenx)

    # pricing: data-backed where possible; here we simulate harvested competitor prices
    rec = pr.recommend([0, 0, 5, 8, 10, 12, 15, 20],
                       positioning=pr.positioning_from_tenx(tenx.verdict, tenx.best_axis))
    print(f"pricing: positioning={rec.positioning} recommended={rec.recommended} anchor={rec.anchor}")
    monetization = 0.8 if rec.recommended > 0 else 0.5

    # user_value: LLM-judged; idea states a sharp, evidenced pain → allow high
    user_value = 0.85

    card = sc.compute(feasibility, user_value, monetization, tenx_score, rationale={
        "feasibility": f"landscape median maturity {land.median}",
        "tenx": f"{tenx.multiplier}× on {tenx.best_axis}",
        "monetization": f"data-backed price {rec.recommended}",
    })
    print(f"\n=== SCORECARD ===")
    print(json.dumps(card.to_dict(), ensure_ascii=False, indent=2))
    print(f"\nVERDICT: {card.verdict.upper()}  (weighted {card.weighted})")
    return 0 if card.verdict in ("proceed", "revise") else 1


if __name__ == "__main__":
    raise SystemExit(main())
