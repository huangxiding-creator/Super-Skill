"""Ambiguity scorer for the Idea Intake stage (IdeaForge / Super-Skill V4.0).

Deterministic core that quantifies how underspecified a raw idea is across five
fields, then recommends whether to (a) proceed autonomously, (b) ask up to three
clarifying questions, or (c) send the user back to sharpen the idea.

Design notes
------------
- The authoritative entry point is :func:`score_fields`, which scores an
  already-extracted field dict. The LLM (per SKILL.md) extracts fields from the
  raw idea and calls this.
- :func:`score_text` is a heuristic fallback that detects field signals from
  free-form text when structured extraction is unavailable. It is deliberately
  conservative and never over-scores.
- All thresholds are module-level constants so they can be tuned in one place.

Scoring rubric (per field, 0/1/2)
    0 = missing or empty
    1 = present but generic / non-actionable
    2 = present and specific / actionable
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Mapping, Sequence

# Five canonical fields that an investment-worthy idea must pin down.
FIELDS: Sequence[str] = ("persona", "pain", "constraints", "success_form", "value_hypothesis")

# Auto-proceed threshold: >= AUTO_PROCEED_SCORE => no questions asked.
AUTO_PROCEED_SCORE = 8
# Sharpen threshold: <= SHARPEN_SCORE => idea too vague, push back to user.
SHARPEN_SCORE = 3
# Between => ask up to MAX_QUESTIONS questions on the weakest fields.
MAX_QUESTIONS = 3

# Signal lexicons for the text heuristic. Generic terms score 1; specific terms
# bump the field toward 2. Order matters only for readability.
_GENERIC_PERSONA = ("用户", "客户", "人", "大家", "别人", "user", "people", "everyone", "anyone")
_SPECIFIC_PERSONA = ("开发者", "设计师", "学生", "医生", "律师", "运维", "研究员", "教师",
                     "自媒体", "跨境电商", "创业者", "developer", "designer", "researcher",
                     "founder", "student", "marketer", "pm", "sre", "researcher")
_PAIN_TERMS = ("痛点", "问题", "麻烦", "慢", "贵", "耗时", "低效", "容易错", "无法", "难",
               "抱怨", "pain", "problem", "slow", "expensive", "frustrat", "can't", "cannot",
               "struggle", "manual", "tedious")
_CONSTRAINT_TERMS = ("必须", "不能", "约束", "限制", "兼容", "平台", "预算", "预算",
                     "合规", "gdpr", "等保", "离线", "实时", "私有", "on-prem", "budget",
                     "must", "constraint", "compliance", "offline", "realtime", "real-time")
_FORM_TERMS = ("app", "应用", "网站", "web", "工具", "tool", "saas", "插件", "extension",
               "平台", "platform", "bot", "机器人", "dashboard", "仪表盘", "api", "cli",
               "脚本", "script", "小程序", "桌面", "desktop", "mobile", "ios", "android")
_VALUE_TERMS = ("十倍", "10倍", "10x", "更快", "更便宜", "更省", "更低成本", "为什么现在",
                "why now", "difference", "different", "better", "cheaper", "faster",
                "颠覆", "创新", "差异化", "数量级", "order of magnitude")

_MAX_LEN_SPECIFIC = 12  # field value longer than this (CJK chars) counts as "specific"


@dataclass(frozen=True)
class FieldScore:
    field: str
    score: int            # 0, 1, or 2
    reason: str           # human-readable why


@dataclass(frozen=True)
class ScoreResult:
    score: int                       # sum 0..10
    fields: List[FieldScore]
    action: str                      # "auto" | "ask" | "sharpen"
    questions_on: List[str]          # fields to ask about (when action == "ask")
    assumptions: List[str]           # fields with score 0 that will be assumed
    max_questions: int = MAX_QUESTIONS

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "fields": [asdict(f) for f in self.fields],
        }


def _clip(v: int) -> int:
    return 0 if v < 0 else 2 if v > 2 else v


def score_field_value(raw: object) -> int:
    """Score a single already-extracted field value (0/1/2).

    Generic / very short values score 1; specific / substantive values score 2;
    empty / missing score 0.
    """
    if raw is None:
        return 0
    text = str(raw).strip()
    if not text or text.lower() in {"none", "null", "n/a", "na", "未知", "无"}:
        return 0
    # Strip surrounding list/markdown noise to gauge substance.
    cleaned = re.sub(r"[\[\]\-•*]", " ", text).strip()
    tokens = [t for t in re.split(r"[\s,，、;；/]+", cleaned) if len(t) > 1]
    if len(cleaned) >= _MAX_LEN_SPECIFIC or len(tokens) >= 2:
        return 2
    return 1


def _assemble(raw_scores: Mapping[str, int]) -> ScoreResult:
    """Assemble a ScoreResult from an already-computed 0/1/2 score per field."""
    field_scores: List[FieldScore] = []
    for name in FIELDS:
        s = _clip(int(raw_scores.get(name, 0)))
        reason = "specific" if s == 2 else "generic" if s == 1 else "missing"
        field_scores.append(FieldScore(field=name, score=s, reason=reason))
    total = sum(fs.score for fs in field_scores)
    action = _decide(total)
    weak = [fs.field for fs in field_scores if fs.score <= 1]
    questions_on = [f for f, _ in zip(weak, range(MAX_QUESTIONS))]
    assumptions = [fs.field for fs in field_scores if fs.score == 0]
    return ScoreResult(
        score=total,
        fields=field_scores,
        action=action,
        questions_on=questions_on,
        assumptions=assumptions,
    )


def _decide(total: int) -> str:
    if total >= AUTO_PROCEED_SCORE:
        return "auto"
    if total <= SHARPEN_SCORE:
        return "sharpen"
    return "ask"


def score_fields(fields: Mapping[str, object]) -> ScoreResult:
    """Score an extracted field mapping (string values). Deterministic & pure."""
    raw_scores = {name: score_field_value(fields.get(name)) for name in FIELDS}
    return _assemble(raw_scores)


def score_text(text: str) -> ScoreResult:
    """Heuristic field detection from free-form text. Conservative fallback.

    Used only when structured extraction is unavailable. Never scores a field 2
    unless a specific signal is present.
    """
    if not text:
        return score_fields({})
    low = text.lower()

    def _detect(terms_generic: Sequence[str], terms_specific: Sequence[str]) -> int:
        if any(t in low for t in terms_specific):
            return 2
        if any(t in low for t in terms_generic):
            return 1
        return 0

    fields = {
        "persona": _detect(_GENERIC_PERSONA, _SPECIFIC_PERSONA),
        "pain": _detect(_PAIN_TERMS, _PAIN_TERMS),  # any pain term => 2 (pain is inherently specific)
        "constraints": _detect(_CONSTRAINT_TERMS, _CONSTRAINT_TERMS),
        "success_form": _detect(_FORM_TERMS, _FORM_TERMS),
        "value_hypothesis": _detect(_VALUE_TERMS, _VALUE_TERMS),
    }
    return _assemble(fields)


def render_questions(result: ScoreResult) -> List[str]:
    """Produce crisp default questions for the weak fields (action == 'ask')."""
    templates = {
        "persona": "目标用户是谁？给一个具体人群（职业/场景）。",
        "pain": "他们最痛的具体问题是什么？什么时候、在哪里发生？",
        "constraints": "有没有不可妥协的硬约束（平台/合规/预算/必须离线）？",
        "success_form": "做成什么形态算成功？(SaaS / 工具 / 插件 / API / 桌面…)",
        "value_hypothesis": "为什么是现在做、凭什么能比现有方案好十倍？",
    }
    return [templates[f] for f in result.questions_on if f in templates]


def main(argv: Sequence[str]) -> int:
    """CLI: read an idea (file path or - for stdin) -> print ScoreResult JSON."""
    if len(argv) < 2:
        sys.stderr.write("usage: ambiguity_scorer.py <idea.txt|-> [--fields]\n")
        return 2
    src = argv[1]
    use_fields = "--fields" in argv
    raw = sys.stdin.read() if src == "-" else open(src, "r", encoding="utf-8").read()
    if use_fields:
        try:
            data = json.loads(raw) if raw.strip().startswith("{") else None
        except json.JSONDecodeError:
            data = None
        result = score_fields(data or {}) if data else score_text(raw)
    else:
        result = score_text(raw)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.action == "ask":
        print("\nSuggested questions:", file=sys.stderr)
        for q in render_questions(result):
            print("  - " + q, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
