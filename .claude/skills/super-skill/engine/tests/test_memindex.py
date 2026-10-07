"""Tests for memindex.py -- synthetic markdown corpora in tmp_path."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import memindex as mi  # noqa: E402
import playbook as pb  # noqa: E402
from ss_common import append_jsonl  # noqa: E402

MODES = ["auto", "unicode61", "like"]


def _supported(mode):
    if mode in ("auto", "like"):
        return True
    import sqlite3
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(f"CREATE VIRTUAL TABLE t USING fts5(x, tokenize='{mode}')")
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def build(root: Path):
    kb = root / "KNOWLEDGE_BASE" / "arch"
    kb.mkdir(parents=True)
    (kb / "db.md").write_text(
        "# Database\n\nWe use PostgreSQL with pgbouncer connection pooling.\n\n"
        "## Migrations\n\nAlembic handles schema migrations; never edit applied revisions.\n\n"
        "## 缓存策略\n\n热点数据使用 Redis 缓存，过期时间为十分钟。\n",
        encoding="utf-8")
    (root / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n## REQ-001 登录\n\n用户可以使用手机号验证码登录系统。\n\n"
        "## REQ-002 Export\n\nUsers can export reports as CSV files.\n",
        encoding="utf-8")
    sol = root / "docs" / "solutions"
    sol.mkdir(parents=True)
    (sol / "windows-encoding.md").write_text(
        "# Windows 编码问题\n\n```python\n# not a heading\nprint('x')\n```\n\n"
        "控制台默认 GBK 导致中文乱码，调用 force_utf8_stdio 解决。\n",
        encoding="utf-8")
    ss = root / ".super-skill"
    ss.mkdir(exist_ok=True)
    (ss / "handoff.md").write_text("# Handoff\n\nNext step: wire the websocket gateway.\n",
                                   encoding="utf-8")
    (root / "ignored.txt").write_text("websocket gateway secret", encoding="utf-8")


@pytest.fixture(params=MODES)
def corpus(request, tmp_path):
    mode = request.param
    if not _supported(mode):
        pytest.skip(f"sqlite lacks {mode}")
    build(tmp_path)
    st = mi.index(tmp_path, _mode=None if mode == "auto" else mode)
    return tmp_path, st


def test_index_stats(corpus):
    root, st = corpus
    assert st["files"] == 4
    assert st["indexed"] == 4
    assert st["total_chunks"] >= 7
    assert (root / ".super-skill" / "memindex.sqlite").exists()


def test_search_english(corpus):
    root, _ = corpus
    hits = mi.search(root, "connection pooling", k=3)
    assert hits and hits[0]["path"] == "KNOWLEDGE_BASE/arch/db.md"
    assert hits[0]["heading"] == "Database"
    h = mi.search(root, "migrations alembic")[0]
    assert h["heading"] == "Database > Migrations"
    assert set(h) == {"id", "path", "heading", "summary", "score"}
    assert len(h["summary"]) <= 120 and "\n" not in h["summary"]


def test_search_chinese(corpus):
    root, _ = corpus
    hits = mi.search(root, "中文乱码")
    assert hits and hits[0]["path"] == "docs/solutions/windows-encoding.md"
    hits = mi.search(root, "缓存")  # 2-char CJK token (below trigram length)
    assert hits and "缓存策略" in hits[0]["heading"]
    hits = mi.search(root, "手机号验证码登录")
    assert hits and hits[0]["path"] == "REQUIREMENTS.md"
    assert "REQ-001" in hits[0]["heading"]


def test_search_sanitizes_queries(corpus):
    root, _ = corpus
    assert mi.search(root, "") == []
    assert mi.search(root, '"*()^:-') == []
    assert isinstance(mi.search(root, 'AND OR NOT "export" NEAR( csv*'), list)
    assert mi.search(root, "REQ-002 export")[0]["path"] == "REQUIREMENTS.md"


def test_non_default_files_ignored_and_handoff_included(corpus):
    root, _ = corpus
    hits = mi.search(root, "websocket gateway")
    assert hits and all(h["path"] != "ignored.txt" for h in hits)
    assert hits[0]["path"] == ".super-skill/handoff.md"


def test_code_fence_not_heading(corpus):
    root, _ = corpus
    hits = mi.search(root, "not a heading")
    assert all("not a heading" not in h["heading"] for h in hits)


def test_timeline_and_get(corpus):
    root, _ = corpus
    hit = mi.search(root, "Alembic")[0]
    tl = mi.timeline(root, hit["id"], n=2)
    assert [t["current"] for t in tl].count(True) == 1
    assert all(t["path"] == hit["path"] for t in tl)
    assert [t["seq"] for t in tl] == sorted(t["seq"] for t in tl)
    got = mi.get(root, [hit["id"], "m-doesnotexist"])
    assert len(got) == 1 and "Alembic" in got[0]["text"]
    assert mi.timeline(root, "m-nope") == []


def test_incremental_and_deletion(tmp_path):
    build(tmp_path)
    mi.index(tmp_path)
    st = mi.index(tmp_path)
    assert st["indexed"] == 0 and st["skipped"] == 4
    f = tmp_path / "KNOWLEDGE_BASE" / "arch" / "db.md"
    f.write_text("# Database\n\nSwitched to CockroachDB cluster.\n", encoding="utf-8")
    os.utime(f, (time.time() + 5, time.time() + 5))
    st = mi.index(tmp_path)
    assert st["indexed"] == 1
    assert mi.search(tmp_path, "CockroachDB")
    assert not mi.search(tmp_path, "pgbouncer")
    (tmp_path / "REQUIREMENTS.md").unlink()
    st = mi.index(tmp_path)
    assert st["removed"] == 1
    assert not mi.search(tmp_path, "手机号验证码")


def test_long_section_split(tmp_path):
    paras = [f"Paragraph {i} " + ("lorem ipsum " * 40) for i in range(12)]
    (tmp_path / "LONG.md").write_text("# Long\n\n" + "\n\n".join(paras) + "\n", encoding="utf-8")
    mi.index(tmp_path)
    chunks = mi.chunk_markdown((tmp_path / "LONG.md").read_text(encoding="utf-8"))
    assert len(chunks) > 1
    assert all(len(body) <= mi.MAX_CHUNK for _, body in chunks)
    assert all(h == "Long" for h, _ in chunks)
    huge = "# H\n\n" + "字" * 4000
    parts = mi.chunk_markdown(huge)
    assert len(parts) >= 3 and all(len(b) <= mi.MAX_CHUNK for _, b in parts)


def test_virtual_docs_playbook_and_ledger(tmp_path):
    pb.add(tmp_path, "learnings", "向量数据库选型结论：先用 SQLite FTS5")
    old = pb.add(tmp_path, "decisions", "deploy with kubernetes helm charts")
    new = pb.add(tmp_path, "decisions", "deploy with docker compose instead")
    pb.supersede(tmp_path, old, new)
    append_jsonl(tmp_path / ".super-skill" / "ledger.jsonl",
                 {"ts": "2026-01-01T00:00:00+08:00", "kind": "note",
                  "text": "Stakeholder approved the quarterly roadmap"})
    append_jsonl(tmp_path / ".super-skill" / "ledger.jsonl",
                 {"ts": "2026-01-01T00:00:00+08:00", "kind": "transition", "to": "roadmap-x"})
    mi.index(tmp_path)
    hits = mi.search(tmp_path, "向量数据库选型")
    assert hits and hits[0]["path"] == mi.VIRTUAL_PLAYBOOK
    hits = mi.search(tmp_path, "kubernetes helm")
    assert all("kubernetes" not in h["summary"] for h in hits)  # superseded not indexed
    hits = mi.search(tmp_path, "quarterly roadmap")
    assert hits and hits[0]["path"] == mi.VIRTUAL_LEDGER
    assert len([h for h in hits if h["path"] == mi.VIRTUAL_LEDGER]) == 1


def test_recency_boost(tmp_path):
    kb = tmp_path / "KNOWLEDGE_BASE"
    kb.mkdir()
    a, b = kb / "a.md", kb / "b.md"
    a.write_text("# Note\n\nretry policy exponential backoff\n", encoding="utf-8")
    b.write_text("# Note\n\nretry policy exponential backoff\n", encoding="utf-8")
    now = time.time()
    os.utime(a, (now - 86400 * 30, now - 86400 * 30))
    os.utime(b, (now, now))
    hits = mi.search(tmp_path, "exponential backoff")
    assert hits[0]["path"] == "KNOWLEDGE_BASE/b.md"
    assert hits[0]["score"] > hits[1]["score"]


def test_cli(tmp_path, capsys):
    build(tmp_path)
    root = str(tmp_path)
    assert mi.main(["--root", root, "--json", "index"]) == 0
    assert json.loads(capsys.readouterr().out)["indexed"] == 4
    assert mi.main(["--root", root, "--json", "search", "Redis 缓存", "-k", "2"]) == 0
    hits = json.loads(capsys.readouterr().out)
    assert hits and len(hits) <= 2
    assert mi.main(["--root", root, "timeline", hits[0]["id"]]) == 0
    assert ">" in capsys.readouterr().out
    assert mi.main(["--root", root, "--json", "get", hits[0]["id"]]) == 0
    assert "Redis" in json.loads(capsys.readouterr().out)[0]["text"]
