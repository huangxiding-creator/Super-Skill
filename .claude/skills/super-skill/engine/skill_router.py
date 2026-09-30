#!/usr/bin/env python3
"""Voyager-style sub-skill retrieval: pick the few relevant skills for a task.

Indexes ``<skill>/skills/*/SKILL.md`` frontmatter (``name``, ``description``,
``tags``) plus the body's heading lines, and ranks them with a pure-Python
Okapi BM25. Tokens: lowercase ASCII words (light suffix stemming, name parts
split on ``-``) and, for CJK text, character bigrams; common Chinese task
words are also expanded to English keywords (``ZH_EXPANSIONS``).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import SKILL_DIR, force_utf8_stdio  # noqa: E402

DEFAULT_SKILLS_DIR = SKILL_DIR / "skills"
K1, B = 1.5, 0.75
NAME_WEIGHT, DESC_WEIGHT, TAG_WEIGHT, HEAD_WEIGHT = 3, 2, 2, 1
MAX_HEADINGS = 40

_CJK_RUN_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]+")
_WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "a an the and or of to in on for with by from at as is are be this that it its into "
    "use using used when how what which my our your i we you can do does should".split()
)
_VOWELS = set("aeiou")

# Sub-skill docs are mostly English; expand common Chinese task words so
# Chinese queries still route. Chinese characters stay in the query as well.
ZH_EXPANSIONS = {
    "调试": "debug debugging", "排错": "debug troubleshoot", "排查": "debug root cause",
    "错误": "error bug", "报错": "error bug debug", "异常": "error exception",
    "缺陷": "bug", "修复": "fix bug", "失败": "fail failing", "根因": "root cause",
    "测试": "test testing", "单元测试": "unit test", "验证": "verify verification",
    "安全": "security", "漏洞": "vulnerability security", "扫描": "scan",
    "性能": "performance", "优化": "optimize optimization", "缓存": "cache",
    "部署": "deploy deployment", "持续集成": "ci cd pipeline", "流水线": "pipeline",
    "文档": "documentation docs", "国际化": "i18n internationalization",
    "多语言": "i18n internationalization translation", "翻译": "translation i18n",
    "无障碍": "accessibility a11y", "上下文": "context", "压缩": "compress compression",
    "记忆": "memory", "搜索": "search", "检索": "search retrieval index", "索引": "index",
    "需求": "requirement idea", "想法": "idea brainstorm", "头脑风暴": "brainstorm",
    "方案": "proposal design", "提案": "proposal", "研究": "research", "调研": "research",
    "提示词": "prompt", "智能体": "agent", "多智能体": "multi agent orchestration",
    "监控": "monitor monitoring observability", "日志": "log logging",
    "状态": "state", "状态管理": "state management", "数据库": "database data",
    "接口": "api", "实时": "real time websocket", "推送": "real time",
    "文件上传": "file storage upload", "存储": "storage", "支付": "monetization payment",
    "变现": "monetization", "功能开关": "feature flag", "重构": "refactor transformation",
    "代码转换": "code transformation", "推理": "reasoning", "进化": "evolution",
    "令牌": "token", "消耗": "token usage", "代理": "proxy", "仓库": "git repository",
}


def stem(w: str) -> str:
    """Tiny suffix stripper: debugging->debug, tests->test, failing->fail."""
    if len(w) <= 3:
        return w
    for suf in ("ation", "ing", "ers", "er", "ed", "ies", "es", "s", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            if suf == "s" and w.endswith("ss"):
                return w
            base = w[: -len(suf)]
            if suf == "ies":
                base += "y"
            elif len(base) >= 2 and base[-1] == base[-2] and base[-1] not in _VOWELS \
                    and base[-1] not in "lsz":
                base = base[:-1]  # debugg -> debug
            return base
    return w


def tokenize(text: str, drop_stop: bool = True) -> list:
    text = (text or "").lower()
    out = []
    for run in _CJK_RUN_RE.findall(text):
        # bigrams carry the meaning; lone chars (的/一/个) are too noisy to index
        if len(run) == 1:
            out.append(run)
        else:
            out.extend(run[i:i + 2] for i in range(len(run) - 1))
    for w in _WORD_RE.findall(_CJK_RUN_RE.sub(" ", text)):
        if drop_stop and w in STOPWORDS:
            continue
        out.append(stem(w))
    return out


# ---------------------------------------------------------------- parsing

def parse_frontmatter(text: str) -> tuple:
    """Minimal YAML frontmatter reader: scalars, quoted strings, ``>``/``|``
    blocks and ``[a, b]`` lists. Returns ``(meta, body)``."""
    meta: dict = {}
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return meta, text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return meta, text
    key, buf = None, []

    def flush():
        if key is not None and buf:
            meta[key] = " ".join(s.strip() for s in buf if s.strip())

    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            flush()
            key, val = m.group(1).lower(), m.group(2).strip()
            buf = []
            if val in (">", "|", ">-", "|-", ">+", "|+", ""):
                continue
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            if val.startswith("[") and val.endswith("]"):
                meta[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
                key = None
                continue
            buf = [val]
        elif key is not None:
            s = line.strip()
            if s.startswith("- "):
                s = s[2:]
            buf.append(s)
    flush()
    return meta, "\n".join(lines[end + 1:])


def load_skills(skills_dir=None) -> list:
    root = Path(skills_dir) if skills_dir else DEFAULT_SKILLS_DIR
    docs = []
    for md in sorted(root.glob("*/SKILL.md")):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = parse_frontmatter(text)
        name = str(meta.get("name") or md.parent.name).strip()
        desc = meta.get("description") or ""
        if isinstance(desc, list):
            desc = " ".join(desc)
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t for t in re.split(r"[,\s]+", tags) if t]
        heads = [re.sub(r"^#+\s*", "", ln).strip() for ln in body.splitlines()
                 if re.match(r"^#{1,3}\s+\S", ln)][:MAX_HEADINGS]
        toks = []
        name_text = f"{name} {md.parent.name}".replace("-", " ").replace("_", " ")
        toks += tokenize(name_text) * NAME_WEIGHT
        toks += tokenize(str(desc)) * DESC_WEIGHT
        toks += tokenize(" ".join(map(str, tags))) * TAG_WEIGHT
        toks += tokenize(" ".join(heads)) * HEAD_WEIGHT
        docs.append({"name": name, "path": str(md), "description": str(desc).strip(),
                     "tokens": toks})
    return docs


# ---------------------------------------------------------------- BM25

class BM25:
    def __init__(self, corpus: list):
        self.n = len(corpus)
        self.tf = []
        self.len = []
        df: dict = {}
        for toks in corpus:
            counts: dict = {}
            for t in toks:
                counts[t] = counts.get(t, 0) + 1
            self.tf.append(counts)
            self.len.append(len(toks))
            for t in counts:
                df[t] = df.get(t, 0) + 1
        self.avg = (sum(self.len) / self.n) if self.n else 0.0
        self.idf = {t: math.log(1 + (self.n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def score(self, query: list, i: int) -> float:
        tf, dl = self.tf[i], self.len[i]
        s = 0.0
        for t in set(query):
            f = tf.get(t)
            if not f:
                continue
            denom = f + K1 * (1 - B + B * dl / (self.avg or 1))
            s += self.idf.get(t, 0.0) * f * (K1 + 1) / denom
        return s


_CACHE: dict = {}


def _index(skills_dir):
    root = Path(skills_dir) if skills_dir else DEFAULT_SKILLS_DIR
    try:
        sig = tuple((p.as_posix(), p.stat().st_mtime) for p in sorted(root.glob("*/SKILL.md")))
    except OSError:
        sig = ()
    key = str(root.resolve()) if root.exists() else str(root)
    hit = _CACHE.get(key)
    if hit and hit[0] == sig:
        return hit[1], hit[2]
    docs = load_skills(root)
    bm = BM25([d["tokens"] for d in docs])
    _CACHE[key] = (sig, docs, bm)
    return docs, bm


def route(query: str, k: int = 5, skills_dir=None) -> list:
    """Return up to ``k`` skills ``[{name, path, score, description}]``, best first."""
    docs, bm = _index(skills_dir)
    query = query or ""
    extra = [en for zh, en in ZH_EXPANSIONS.items() if zh in query]
    if extra:
        query = query + " " + " ".join(extra)
    q = tokenize(query)
    if not q:
        q = tokenize(query, drop_stop=False)
    if not q or not docs:
        return []
    scored = []
    for i, d in enumerate(docs):
        s = bm.score(q, i)
        if s > 0:
            scored.append({"name": d["name"], "path": d["path"], "score": round(s, 4),
                           "description": d["description"]})
    scored.sort(key=lambda r: (-r["score"], r["name"]))
    return scored[:max(1, int(k))]


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="skill_router.py", description=__doc__.splitlines()[0])
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--skills-dir", default=None)
    ap.add_argument("--root", default=os.getcwd(), help="unused; accepted for CLI uniformity")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    hits = route(a.query, a.k, a.skills_dir)
    if a.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        for h in hits:
            desc = h["description"]
            desc = desc if len(desc) <= 100 else desc[:99] + "…"
            print(f"{h['score']:7.3f}  {h['name']:<28} {desc}")
        if not hits:
            print("no matching skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
