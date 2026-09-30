#!/usr/bin/env python3
"""ACE-style playbook: an evolving, itemised replacement for prose Cerebrum.

Design sources
--------------
* ACE "Agentic Context Engineering" (Apache-2.0): context is a playbook of
  small *bullets* with helpful/harmful counters, grown by incremental delta
  operations instead of monolithic rewrites (avoids context collapse).
* ExpeL: insights are up/down-voted; persistently harmful ones are pruned.
* Graphiti: facts are *invalidated* (superseded), never deleted.

Storage
-------
``<project>/.super-skill/playbook.jsonl`` is an append-only op log. The
current view is materialised by replaying every op in order::

    {ts, op: add|update|helpful|harmful|supersede, id,
     section?, text?, pattern?, block?, source?, superseded_by?}

Bullet view::

    {id, section, text, pattern, block, helpful, harmful,
     created, last_used, superseded_by, source}

A bullet is *active* when it is not superseded and not pruned
(pruned == ``harmful > helpful + 2``).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import append_jsonl, force_utf8_stdio, now_iso, read_jsonl, sdir, short_hash  # noqa: E402

PLAYBOOK_FILE = "playbook.jsonl"
SECTIONS = ("do-not-repeat", "preferences", "learnings", "decisions")
DEDUP_THRESHOLD = 0.9
PRUNE_MARGIN = 2

SECTION_TITLES = {
    "do-not-repeat": "Do-Not-Repeat",
    "preferences": "User Preferences",
    "learnings": "Key Learnings",
    "decisions": "Decision Log",
}
_TITLE_TO_SECTION = {
    "do-not-repeat": "do-not-repeat",
    "do not repeat": "do-not-repeat",
    "donotrepeat": "do-not-repeat",
    "dnr": "do-not-repeat",
    "user preferences": "preferences",
    "preferences": "preferences",
    "key learnings": "learnings",
    "learnings": "learnings",
    "decision log": "decisions",
    "decisions": "decisions",
}

_CJK_RE = re.compile(
    r"[぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]"
)
_WORD_RE = re.compile(r"[a-z0-9_]+")


# ---------------------------------------------------------------- helpers

def playbook_path(root: Path) -> Path:
    return sdir(root) / PLAYBOOK_FILE


def tokens(text: str) -> set:
    """Token set for Jaccard: each CJK char is a token, plus lowercase words."""
    text = (text or "").lower()
    out = set(_CJK_RE.findall(text))
    out.update(_WORD_RE.findall(_CJK_RE.sub(" ", text)))
    return out


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta and not tb:
        return 1.0 if (a or "").strip() == (b or "").strip() else 0.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def normalize_section(section: str | None) -> str:
    s = (section or "learnings").strip()
    key = s.lower().replace("_", "-")
    if key in _TITLE_TO_SECTION:
        return _TITLE_TO_SECTION[key]
    key2 = key.replace("-", " ")
    return _TITLE_TO_SECTION.get(key2, key)


def _new_id(section: str, text: str) -> str:
    return "pb-" + short_hash(f"{section}|{text}|{now_iso()}|{os.urandom(6).hex()}", 10)


def _valid_regex(pattern: str | None) -> bool:
    if not pattern:
        return False
    try:
        re.compile(pattern)
        return True
    except (re.error, TypeError, ValueError, OverflowError, RecursionError):
        return False


def _append(root: Path, rec: dict) -> dict:
    rec = {"ts": now_iso(), **rec}
    append_jsonl(playbook_path(root), rec)
    return rec


def is_active(b: dict) -> bool:
    return not b.get("superseded_by") and not is_pruned(b)


def is_pruned(b: dict) -> bool:
    return int(b.get("harmful", 0)) > int(b.get("helpful", 0)) + PRUNE_MARGIN


# ---------------------------------------------------------------- replay

def _replay(root: Path) -> dict:
    """Materialise ``{id: bullet}`` preserving insertion order."""
    view: dict[str, dict] = {}
    for op in read_jsonl(playbook_path(root)):
        kind = op.get("op")
        bid = op.get("id")
        if not bid or not isinstance(bid, str):
            continue
        ts = op.get("ts") or ""
        if kind == "add":
            if bid in view:
                continue
            view[bid] = {
                "id": bid,
                "section": normalize_section(op.get("section")),
                "text": str(op.get("text") or ""),
                "pattern": op.get("pattern") or None,
                "block": bool(op.get("block", False)),
                "helpful": 0,
                "harmful": 0,
                "created": ts,
                "last_used": ts,
                "superseded_by": None,
                "source": op.get("source"),
            }
            continue
        b = view.get(bid)
        if b is None:
            continue
        if kind == "update":
            if op.get("text") is not None:
                b["text"] = str(op["text"])
            if "pattern" in op:
                b["pattern"] = op.get("pattern") or None
            if "block" in op:
                b["block"] = bool(op.get("block"))
            if op.get("section"):
                b["section"] = normalize_section(op["section"])
            b["last_used"] = ts or b["last_used"]
        elif kind == "helpful":
            b["helpful"] += 1
            b["last_used"] = ts or b["last_used"]
        elif kind == "harmful":
            b["harmful"] += 1
            b["last_used"] = ts or b["last_used"]
        elif kind == "supersede":
            b["superseded_by"] = op.get("superseded_by") or "?"
    return view


# ---------------------------------------------------------------- API

def bullets(root: Path, include_inactive: bool = False) -> list:
    view = _replay(Path(root))
    out = []
    for b in view.values():
        b = dict(b)
        b["active"] = is_active(b)
        b["pruned"] = is_pruned(b)
        if include_inactive or b["active"]:
            out.append(b)
    return out


def get(root: Path, bid: str) -> dict | None:
    for b in bullets(root, include_inactive=True):
        if b["id"] == bid:
            return b
    return None


def find_similar(root: Path, section: str, text: str,
                 threshold: float = DEDUP_THRESHOLD) -> dict | None:
    section = normalize_section(section)
    best, best_sim = None, 0.0
    for b in bullets(root):
        if b["section"] != section:
            continue
        sim = jaccard(b["text"], text)
        if sim >= threshold and sim > best_sim:
            best, best_sim = b, sim
    return best


def add(root: Path, section: str, text: str, pattern: str | None = None,
        block: bool = False, source: str | None = None) -> str:
    """Add a bullet; returns the id of the new or the near-duplicate bullet."""
    root = Path(root)
    text = (text or "").strip()
    if not text:
        raise ValueError("bullet text must not be empty")
    section = normalize_section(section)
    dup = find_similar(root, section, text)
    if dup is not None:
        return dup["id"]
    bid = _new_id(section, text)
    rec: dict[str, Any] = {"op": "add", "id": bid, "section": section, "text": text,
                           "pattern": pattern or None, "block": bool(block)}
    if source:
        rec["source"] = source
    _append(root, rec)
    return bid


def _require(root: Path, bid: str) -> dict:
    b = get(root, bid)
    if b is None:
        raise KeyError(f"unknown playbook bullet: {bid}")
    return b


def update(root: Path, bid: str, text: str | None = None, pattern: Any = ...,
           block: Any = ...) -> dict:
    root = Path(root)
    _require(root, bid)
    rec: dict[str, Any] = {"op": "update", "id": bid}
    if text is not None:
        rec["text"] = text.strip()
    if pattern is not ...:
        rec["pattern"] = pattern or None
    if block is not ...:
        rec["block"] = bool(block)
    _append(root, rec)
    return _require(root, bid)


def vote(root: Path, bid: str, helpful: bool) -> dict:
    root = Path(root)
    _require(root, bid)
    _append(root, {"op": "helpful" if helpful else "harmful", "id": bid})
    return _require(root, bid)


def supersede(root: Path, old_id: str, new_id: str) -> dict:
    root = Path(root)
    _require(root, old_id)
    _require(root, new_id)
    if old_id == new_id:
        raise ValueError("a bullet cannot supersede itself")
    _append(root, {"op": "supersede", "id": old_id, "superseded_by": new_id})
    return _require(root, old_id)


def _rank_key(b: dict):
    return (int(b.get("helpful", 0)) - int(b.get("harmful", 0)),
            b.get("last_used") or "", b.get("created") or "")


def top(root: Path, k: int = 10, section: str | None = None,
        max_chars: int = 2000) -> list:
    items = bullets(root)
    if section:
        sec = normalize_section(section)
        items = [b for b in items if b["section"] == sec]
    items.sort(key=_rank_key, reverse=True)
    out, used = [], 0
    for b in items:
        if len(out) >= k:
            break
        cost = len(b["text"]) + len(b.get("pattern") or "")
        if out and used + cost > max_chars:
            break
        if not out and cost > max_chars:
            b = dict(b)
            b["text"] = b["text"][: max(0, max_chars - 1)] + "…"
            cost = max_chars
        out.append(b)
        used += cost
    return out


def dnr_rules(root: Path) -> list:
    return [b for b in bullets(root)
            if b["section"] == "do-not-repeat" and _valid_regex(b.get("pattern"))]


def check_text(root: Path, text: str) -> list:
    hits = []
    for b in dnr_rules(root):
        try:
            m = re.search(b["pattern"], text or "", re.MULTILINE)
        except (re.error, RecursionError):
            continue
        if m:
            hits.append({"id": b["id"], "text": b["text"], "block": bool(b["block"]),
                         "pattern": b["pattern"], "match": m.group(0)[:200]})
    return hits


# ---------------------------------------------------------------- markdown

_HEADING_RE = re.compile(r"^\s{0,3}#{2,6}\s+(.+?)\s*#*\s*$")
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*\S)\s*$")
_DNR_RE = re.compile(r"^`(?P<pat>(?:[^`]|``)+?)`\s*(?:→|->|=>|—|:)\s*(?P<msg>.*)$")


def parse_cerebrum_md(md: str) -> list:
    """Return ``[{section, text, pattern, block}]`` from legacy cerebrum markdown."""
    out = []
    section = None
    in_fence = False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        h = _HEADING_RE.match(line)
        if h:
            title = re.sub(r"\s*\(.*?\)\s*$", "", h.group(1)).strip()
            section = normalize_section(title)
            continue
        if section is None:
            continue
        m = _BULLET_RE.match(line)
        if not m:
            continue
        body = re.sub(r"\s*<!--.*?-->\s*$", "", m.group(1)).strip()
        if not body or (body.startswith("[") and body.endswith("]") and "→" in body):
            continue  # template placeholder like "[pattern → explanation]"
        pattern, block = None, False
        if body.lower().startswith("[block]"):
            block, body = True, body[7:].strip()
        if section == "do-not-repeat":
            d = _DNR_RE.match(body)
            if d:
                pattern = d.group("pat").strip()
                body = d.group("msg").strip() or pattern
                if body.lower().startswith("[block]"):
                    block, body = True, body[7:].strip()
        out.append({"section": section, "text": body, "pattern": pattern, "block": block})
    return out


def import_cerebrum_md(root: Path, md_path) -> dict:
    md = Path(md_path).read_text(encoding="utf-8", errors="replace")
    before = {b["id"] for b in bullets(root, include_inactive=True)}
    ids = []
    for item in parse_cerebrum_md(md):
        ids.append(add(root, item["section"], item["text"], pattern=item["pattern"],
                       block=item["block"], source=f"cerebrum:{Path(md_path).name}"))
    new = [i for i in ids if i not in before]
    return {"parsed": len(ids), "added": len(set(new)), "ids": ids}


def export_md(root: Path) -> str:
    items = bullets(root)
    order = list(SECTIONS) + sorted({b["section"] for b in items} - set(SECTIONS))
    lines = ["# Playbook", "", f"> Exported {now_iso()} · {len(items)} active bullets", ""]
    for sec in order:
        group = sorted([b for b in items if b["section"] == sec], key=_rank_key, reverse=True)
        title = SECTION_TITLES.get(sec, sec.replace("-", " ").title())
        lines.append(f"## {title}")
        lines.append("")
        for b in group:
            prefix = "[block] " if b["block"] else ""
            score = f"  <!-- {b['id']} +{b['helpful']}/-{b['harmful']} -->"
            if b.get("pattern"):
                lines.append(f"- `{b['pattern']}` → {prefix}{b['text']}{score}")
            else:
                lines.append(f"- {prefix}{b['text']}{score}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- CLI

def _fmt(b: dict) -> str:
    flags = []
    if b.get("block"):
        flags.append("BLOCK")
    if b.get("superseded_by"):
        flags.append(f"superseded→{b['superseded_by']}")
    if b.get("pruned"):
        flags.append("pruned")
    pat = f" `{b['pattern']}`" if b.get("pattern") else ""
    fl = f" [{', '.join(flags)}]" if flags else ""
    return f"{b['id']} [{b['section']}] +{b['helpful']}/-{b['harmful']}{fl}{pat} {b['text']}"


def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="playbook.py", description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add")
    p.add_argument("--section", "-s", default="learnings")
    p.add_argument("--text", "-t", required=True)
    p.add_argument("--pattern", "-p")
    p.add_argument("--block", action="store_true")
    p.add_argument("--source")

    p = sub.add_parser("list")
    p.add_argument("--all", action="store_true", help="include superseded/pruned")
    p.add_argument("--section")

    p = sub.add_parser("vote")
    p.add_argument("id")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--helpful", action="store_true")
    g.add_argument("--harmful", action="store_true")

    p = sub.add_parser("update")
    p.add_argument("id")
    p.add_argument("--text", "-t", required=True)

    p = sub.add_parser("supersede")
    p.add_argument("old_id")
    p.add_argument("new_id")

    p = sub.add_parser("top")
    p.add_argument("-k", type=int, default=10)
    p.add_argument("--section")
    p.add_argument("--max-chars", type=int, default=2000)

    p = sub.add_parser("check", help="exit 2 if a blocking rule matches")
    p.add_argument("target", help="file path or literal text ('-' = stdin)")

    p = sub.add_parser("import-md")
    p.add_argument("path")

    p = sub.add_parser("export-md")
    p.add_argument("--out")

    a = ap.parse_args(argv)
    root = Path(a.root)

    def out(data, text):
        print(json.dumps(data, ensure_ascii=False, indent=2) if a.json else text)

    try:
        if a.cmd == "add":
            bid = add(root, a.section, a.text, a.pattern, a.block, a.source)
            out({"id": bid}, bid)
        elif a.cmd == "list":
            items = bullets(root, include_inactive=a.all)
            if a.section:
                items = [b for b in items if b["section"] == normalize_section(a.section)]
            out(items, "\n".join(_fmt(b) for b in items) or "(empty playbook)")
        elif a.cmd == "vote":
            b = vote(root, a.id, helpful=a.helpful)
            out(b, _fmt(b))
        elif a.cmd == "update":
            b = update(root, a.id, a.text)
            out(b, _fmt(b))
        elif a.cmd == "supersede":
            b = supersede(root, a.old_id, a.new_id)
            out(b, _fmt(b))
        elif a.cmd == "top":
            items = top(root, a.k, a.section, a.max_chars)
            out(items, "\n".join(_fmt(b) for b in items) or "(empty playbook)")
        elif a.cmd == "check":
            if a.target == "-":
                text = sys.stdin.read()
            elif os.path.isfile(a.target):
                text = Path(a.target).read_text(encoding="utf-8", errors="replace")
            else:
                text = a.target
            hits = check_text(root, text)
            out(hits, "\n".join(
                f"{'BLOCK' if h['block'] else 'WARN'} {h['id']} `{h['pattern']}` → {h['text']}"
                for h in hits) or "no do-not-repeat hits")
            return 2 if any(h["block"] for h in hits) else 0
        elif a.cmd == "import-md":
            res = import_cerebrum_md(root, a.path)
            out(res, f"parsed {res['parsed']} bullets, added {res['added']} new")
        elif a.cmd == "export-md":
            md = export_md(root)
            if a.out:
                Path(a.out).write_text(md, encoding="utf-8")
                out({"out": a.out}, f"wrote {a.out}")
            else:
                sys.stdout.write(md)
    except (KeyError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
