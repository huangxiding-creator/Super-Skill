"""Tests for playbook.py -- synthetic data only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import playbook as pb  # noqa: E402

LEGACY_MD = """# Cerebrum

> Sessions contributed: 3

## Do-Not-Repeat

- `catch\\s*\\(\\s*\\w+\\s*\\)\\s*\\{\\s*\\}` → Never use empty catch blocks.
- `console\\.log\\(` -> No console.log in production code.
- `([bad` → invalid regex should be kept as text but skipped by rules
- `rm -rf /` → [block] never wipe the root

## User Preferences

- 回复使用中文
- Prefer pytest over unittest

## Key Learnings

- Windows 控制台默认 GBK，需要 force_utf8_stdio

## Decision Log

- 2026-01-02: use SQLite FTS5 — stdlib only
"""


def ops(root):
    p = root / ".super-skill" / "playbook.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_add_and_list(tmp_path):
    bid = pb.add(tmp_path, "learnings", "Always run tests before commit")
    assert bid.startswith("pb-")
    items = pb.bullets(tmp_path)
    assert len(items) == 1
    b = items[0]
    assert b["text"] == "Always run tests before commit"
    assert b["section"] == "learnings" and b["helpful"] == 0 and b["active"]


def test_dedup_jaccard(tmp_path):
    a = pb.add(tmp_path, "learnings", "Always run the tests before you commit")
    b = pb.add(tmp_path, "learnings", "always run the tests before you commit!")
    assert a == b
    assert len(ops(tmp_path)) == 1
    # different section -> not deduped
    c = pb.add(tmp_path, "preferences", "Always run the tests before you commit")
    assert c != a


def test_dedup_chinese(tmp_path):
    a = pb.add(tmp_path, "preferences", "回复时请使用简体中文")
    b = pb.add(tmp_path, "preferences", "回复时请使用简体中文。")
    assert a == b
    c = pb.add(tmp_path, "preferences", "代码注释使用英文")
    assert c != a
    assert pb.jaccard("数据库迁移", "数据库迁移") == 1.0


def test_update_and_vote_and_prune(tmp_path):
    bid = pb.add(tmp_path, "learnings", "old text")
    pb.update(tmp_path, bid, "new text")
    assert pb.get(tmp_path, bid)["text"] == "new text"
    pb.vote(tmp_path, bid, helpful=True)
    for _ in range(3):
        pb.vote(tmp_path, bid, helpful=False)
    b = pb.get(tmp_path, bid)
    assert (b["helpful"], b["harmful"]) == (1, 3)
    assert b["active"]  # 3 > 1 + 2 is False
    pb.vote(tmp_path, bid, helpful=False)
    assert not pb.get(tmp_path, bid)["active"]
    assert pb.bullets(tmp_path) == []
    assert len(pb.bullets(tmp_path, include_inactive=True)) == 1


def test_supersede_invalidates_not_deletes(tmp_path):
    old = pb.add(tmp_path, "decisions", "Use MySQL")
    new = pb.add(tmp_path, "decisions", "Use PostgreSQL instead")
    pb.supersede(tmp_path, old, new)
    active = [b["id"] for b in pb.bullets(tmp_path)]
    assert active == [new]
    allb = {b["id"]: b for b in pb.bullets(tmp_path, include_inactive=True)}
    assert allb[old]["superseded_by"] == new
    # once superseded, the same text can be re-added as a new bullet
    again = pb.add(tmp_path, "decisions", "Use MySQL")
    assert again != old


def test_top_ranking_and_budget(tmp_path):
    a = pb.add(tmp_path, "learnings", "alpha lesson")
    b = pb.add(tmp_path, "learnings", "beta lesson")
    c = pb.add(tmp_path, "preferences", "gamma pref")
    pb.vote(tmp_path, b, True)
    pb.vote(tmp_path, b, True)
    pb.vote(tmp_path, a, True)
    ids = [x["id"] for x in pb.top(tmp_path, k=10)]
    assert ids[0] == b and ids[1] == a and c in ids
    assert [x["id"] for x in pb.top(tmp_path, k=10, section="preferences")] == [c]
    assert len(pb.top(tmp_path, k=1)) == 1
    small = pb.top(tmp_path, k=10, max_chars=15)
    assert len(small) == 1
    pb.add(tmp_path, "learnings", "x" * 500)
    assert len(pb.top(tmp_path, k=10, section="learnings", max_chars=100)) >= 1


def test_dnr_and_check(tmp_path):
    pb.add(tmp_path, "do-not-repeat", "no console.log", pattern=r"console\.log\(")
    pb.add(tmp_path, "do-not-repeat", "broken", pattern="([bad")
    pb.add(tmp_path, "do-not-repeat", "禁止硬编码密码", pattern=r"password\s*=\s*['\"]", block=True)
    pb.add(tmp_path, "do-not-repeat", "text only rule")
    rules = pb.dnr_rules(tmp_path)
    assert len(rules) == 2  # invalid regex and pattern-less rule skipped
    hits = pb.check_text(tmp_path, "x = 1\nconsole.log('hi')\npassword = 'abc'")
    assert {h["text"] for h in hits} == {"no console.log", "禁止硬编码密码"}
    assert any(h["block"] for h in hits)
    assert pb.check_text(tmp_path, "print('ok')") == []


def test_import_cerebrum_md(tmp_path):
    md = tmp_path / "cerebrum.md"
    md.write_text(LEGACY_MD, encoding="utf-8")
    res = pb.import_cerebrum_md(tmp_path, md)
    assert res["parsed"] == 8
    items = pb.bullets(tmp_path)
    by_sec = {}
    for b in items:
        by_sec.setdefault(b["section"], []).append(b)
    assert len(by_sec["do-not-repeat"]) == 4
    assert len(by_sec["preferences"]) == 2
    assert len(by_sec["learnings"]) == 1
    assert len(by_sec["decisions"]) == 1
    pats = {b["pattern"] for b in by_sec["do-not-repeat"]}
    assert r"console\.log\(" in pats
    blocking = [b for b in by_sec["do-not-repeat"] if b["block"]]
    assert len(blocking) == 1 and blocking[0]["text"] == "never wipe the root"
    assert len(pb.dnr_rules(tmp_path)) == 3
    assert pb.check_text(tmp_path, "try { x() } catch (e) { }")
    # re-import is idempotent thanks to dedup
    res2 = pb.import_cerebrum_md(tmp_path, md)
    assert res2["added"] == 0
    assert len(pb.bullets(tmp_path)) == 8


def test_export_roundtrip(tmp_path):
    md = tmp_path / "cerebrum.md"
    md.write_text(LEGACY_MD, encoding="utf-8")
    pb.import_cerebrum_md(tmp_path, md)
    out = pb.export_md(tmp_path)
    assert "## Do-Not-Repeat" in out and "## User Preferences" in out
    assert "回复使用中文" in out
    other = tmp_path / "other"
    other.mkdir()
    exp = other / "exp.md"
    exp.write_text(out, encoding="utf-8")
    pb.import_cerebrum_md(other, exp)
    a = sorted((b["section"], b["text"], b["pattern"], b["block"]) for b in pb.bullets(tmp_path))
    b = sorted((x["section"], x["text"], x["pattern"], x["block"]) for x in pb.bullets(other))
    assert a == b


def test_corrupt_log_lines_are_skipped(tmp_path):
    bid = pb.add(tmp_path, "learnings", "survives corruption")
    p = tmp_path / ".super-skill" / "playbook.jsonl"
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("{not json\n")
        fh.write(json.dumps({"op": "helpful", "id": "pb-unknown"}) + "\n")
    assert [b["id"] for b in pb.bullets(tmp_path)] == [bid]


def test_cli(tmp_path, capsys):
    root = str(tmp_path)
    assert pb.main(["--root", root, "--json", "add", "-s", "do-not-repeat", "-t", "禁止 eval",
                    "-p", r"\beval\(", "--block"]) == 0
    bid = json.loads(capsys.readouterr().out)["id"]
    assert pb.main(["--root", root, "vote", bid, "--helpful"]) == 0
    capsys.readouterr()
    assert pb.main(["--root", root, "--json", "list"]) == 0
    items = json.loads(capsys.readouterr().out)
    assert items[0]["helpful"] == 1
    assert pb.main(["--root", root, "check", "y = eval(x)"]) == 2
    assert "BLOCK" in capsys.readouterr().out
    f = tmp_path / "code.py"
    f.write_text("print(1)\n", encoding="utf-8")
    assert pb.main(["--root", root, "check", str(f)]) == 0
    capsys.readouterr()
    assert pb.main(["--root", root, "export-md"]) == 0
    assert "禁止 eval" in capsys.readouterr().out
    assert pb.main(["--root", root, "vote", "pb-missing", "--harmful"]) == 1
