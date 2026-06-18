"""Tests for ambiguity_scorer. Run: python -m pytest test_ambiguity_scorer.py -q"""
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ambiguity_scorer import (  # noqa: E402
    score_fields, score_text, render_questions, FIELDS,
    AUTO_PROCEED_SCORE, SHARPEN_SCORE,
)


def test_empty_is_sharpen():
    r = score_fields({})
    assert r.score == 0
    assert r.action == "sharpen"
    assert set(r.assumptions) == set(FIELDS)


def test_all_specific_is_auto():
    fields = {f: "a clearly specified concrete value with detail" for f in FIELDS}
    r = score_fields(fields)
    assert r.score == 10
    assert r.action == "auto"
    assert r.questions_on == []


def test_generic_only_is_ask():
    # single short token => generic => 1 each => total 5 => "ask"
    fields = {f: "x" for f in FIELDS}
    r = score_fields(fields)
    assert r.score == 5
    assert r.action == "ask"
    assert 1 <= len(r.questions_on) <= 3


def test_missing_values_treated_as_zero():
    fields = {"persona": "开发者", "pain": "", "constraints": None,
              "success_form": "n/a", "value_hypothesis": "10x faster and cheaper than tools today"}
    r = score_fields(fields)
    zeros = {fs.field for fs in r.fields if fs.score == 0}
    assert {"pain", "constraints", "success_form"} <= zeros
    assert r.score <= AUTO_PROCEED_SCORE


def test_questions_capped_at_three():
    fields = {f: "x" for f in FIELDS}  # all weak
    r = score_fields(fields)
    assert len(r.questions_on) <= 3
    assert all(q for q in render_questions(r))


def test_text_heuristic_detects_specific_persona():
    text = "我想给独立开发者做一个离线的记账 SaaS，他们的痛点是现有工具都要联网而且很贵，必须兼容 macOS，能比账本快十倍。"
    r = score_text(text)
    assert r.score >= 6  # most fields lit up
    names = {fs.field: fs.score for fs in r.fields}
    assert names["persona"] == 2
    assert names["success_form"] == 2


def test_text_empty():
    assert score_text("").score == 0
    assert score_text("").action == "sharpen"


def test_action_thresholds_boundary():
    # 4 => ask, 8 => auto, 3 => sharpen
    fields_ask = {f: ("ab" if i < 4 else "specific detailed value here") for i, f in enumerate(FIELDS)}
    r_ask = score_fields(fields_ask)
    assert SHARPEN_SCORE < r_ask.score < AUTO_PROCEED_SCORE
    assert r_ask.action == "ask"


if __name__ == "__main__":
    # allow running without pytest
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
