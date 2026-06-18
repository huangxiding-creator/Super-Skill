"""Tests for proposal-forge scoring (maturity, tenx, scorecard). Run: python test_scoring.py"""
import sys, pathlib, traceback
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import maturity_index as mi  # noqa: E402
import tenx_delta_index as tx  # noqa: E402
import scorecard as sc  # noqa: E402


# ---- maturity_index ----
def test_maturity_mature_repo():
    s = mi.score_repo({"stars": 50000, "forks": 4000, "open_issues": 200,
                       "updated_at": "2026-06-01T00:00:00Z", "language": "TypeScript",
                       "license": "MIT", "topics": ["x", "y", "z", "a", "b"]})
    assert s.score >= mi.MATURE
    assert s.verdict == "mature"
    assert s.components["license"] == 1.0


def test_maturity_immature_repo():
    s = mi.score_repo({"stars": 5, "forks": 0, "open_issues": 30,
                       "updated_at": "2024-01-01T00:00:00Z", "language": "",
                       "license": "NONE", "topics": []})
    assert s.score < mi.VIABLE
    assert s.verdict == "immature"


def test_maturity_license_map():
    assert mi._license("GPL-3.0") == 0.5
    assert mi._license("Apache-2.0") == 1.0
    assert mi._license("NONE") == 0.3


def test_landscape_aggregate_and_feasibility():
    repos = [
        {"stars": 50000, "forks": 4000, "open_issues": 200, "updated_at": "2026-06-01T00:00:00Z", "language": "TS", "license": "MIT", "topics": ["a"]},
        {"stars": 50, "forks": 3, "open_issues": 2, "updated_at": "2026-04-01T00:00:00Z", "language": "Go", "license": "Apache-2.0", "topics": []},
    ]
    land = mi.score_landscape(repos)
    assert land.n == 2
    assert land.best.verdict == "mature"
    feas = mi.derive_feasibility(land)
    assert 0.3 <= feas <= 0.95


def test_empty_landscape():
    land = mi.score_landscape([])
    assert land.best is None
    assert mi.derive_feasibility(land) == 0.5


# ---- tenx_delta_index ----
def test_tenx_qualified_when_10x_on_an_axis():
    # deploy_cost lower_better: ours 1, baseline 16 => delta 16 => log10 1.2
    r = tx.score({"deploy_cost": {"ours": 1, "baseline": 16}})
    assert r.verdict == "tenx_qualified"
    assert r.best_axis == "deploy_cost"
    assert r.multiplier >= 10


def test_tenx_incremental():
    # 2x better => log10(2)=0.3 => incremental
    r = tx.score({"price": {"ours": 5, "baseline": 10}})
    assert r.verdict == "incremental"


def test_tenx_red_ocean_when_worse():
    # higher_better, ours worse => delta <1 => log10 negative
    r = tx.score({"dev_efficiency": {"ours": 1, "baseline": 5}})
    assert r.verdict == "red_ocean"


def test_tenx_skips_missing_or_zero():
    r = tx.score({"unknown_axis": {"ours": 1, "baseline": 1},
                  "latency": {"ours": 0, "baseline": 5}})
    assert r.axes == []
    assert r.verdict == "red_ocean"


def test_tenx_lower_better_direction():
    # cac lower_better: ours 2, baseline 8 => 4x => incremental-ish
    r = tx.score({"cac": {"ours": 2, "baseline": 8}})
    assert r.tenx > 0
    assert r.axes[0].better is True


# ---- scorecard ----
def test_scorecard_proceed():
    card = sc.compute(feasibility=0.9, user_value=0.95, monetization=0.85, tenx=0.9)
    assert card.verdict == "proceed"
    assert card.weighted >= sc.GATE_PROCEED


def test_scorecard_reject():
    card = sc.compute(0.2, 0.2, 0.1, 0.1)
    assert card.verdict == "reject"
    assert card.weighted < sc.GATE_REVISE


def test_scorecard_revise():
    card = sc.compute(0.6, 0.6, 0.5, 0.5)
    assert card.verdict == "revise"


def test_scorecard_clamps_and_weakest():
    card = sc.compute(1.5, 0.9, 0.9, 0.1)  # feasibility clamps to 1.0
    assert card.feasibility == 1.0
    assert sc.weakest_dim(card) == "tenx"


def test_scorecard_weights_sum_to_one():
    assert abs(sum(sc.WEIGHTS.values()) - 1.0) < 1e-9


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1; print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
