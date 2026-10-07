"""Tests for skill_router.py -- synthetic skills dir + the real sub-skill catalogue."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import skill_router as sr  # noqa: E402


def mk(d: Path, name: str, front: str, body: str = "") -> None:
    p = d / name
    p.mkdir(parents=True)
    (p / "SKILL.md").write_text(f"---\n{front}\n---\n\n{body}", encoding="utf-8")


@pytest.fixture
def skills(tmp_path):
    d = tmp_path / "skills"
    mk(d, "pdf-tools", "name: pdf-tools\ndescription: Extract text and tables from PDF files.",
       "# PDF Tools\n## Merge documents\n")
    mk(d, "db-migrate", "name: db-migrate\ndescription: >\n  Database schema migrations\n"
       "  with rollback support.\ntags: [database, sql]", "# Migrations\n")
    mk(d, "zh-writer", 'name: zh-writer\ndescription: "中文技术文档写作与润色"', "# 中文写作\n")
    mk(d, "no-front", "", "# Nothing here\n")
    (d / "not-a-skill").mkdir()
    return d


def test_frontmatter_parsing():
    meta, body = sr.parse_frontmatter(
        "---\nname: x\ndescription: |\n  line one\n  line two\ntags: [a, 'b']\n---\n# H\n")
    assert meta["name"] == "x"
    assert meta["description"] == "line one line two"
    assert meta["tags"] == ["a", "b"]
    assert body.strip() == "# H"
    assert sr.parse_frontmatter("no frontmatter")[0] == {}


def test_tokenize_and_stem():
    assert sr.stem("debugging") == "debug"
    assert sr.stem("tests") == "test"
    assert sr.stem("failing") == "fail"
    toks = sr.tokenize("Debug the 数据库迁移")
    assert "debug" in toks and "the" not in toks
    assert "数据" in toks and "迁移" in toks


def test_route_synthetic(skills):
    hits = sr.route("extract tables from a pdf", k=3, skills_dir=skills)
    assert hits[0]["name"] == "pdf-tools"
    assert set(hits[0]) == {"name", "path", "score", "description"}
    hits = sr.route("rollback a database migration", skills_dir=skills)
    assert hits[0]["name"] == "db-migrate"
    assert "rollback" in hits[0]["description"]
    hits = sr.route("润色中文文档", skills_dir=skills)
    assert hits[0]["name"] == "zh-writer"
    assert sr.route("", skills_dir=skills) == []
    assert sr.route("zzzqqq", skills_dir=skills) == []
    assert len(sr.route("pdf database 中文", k=2, skills_dir=skills)) == 2


def test_missing_dir(tmp_path):
    assert sr.route("anything", skills_dir=tmp_path / "nope") == []


def test_cache_invalidates(skills):
    assert sr.route("kubernetes", skills_dir=skills) == []
    mk(skills, "k8s", "name: k8s\ndescription: Kubernetes deployment helper")
    assert sr.route("kubernetes", skills_dir=skills)[0]["name"] == "k8s"


REAL = sr.DEFAULT_SKILLS_DIR


@pytest.mark.skipif(not REAL.is_dir(), reason="real skills dir not present")
def test_real_catalogue():
    docs = sr.load_skills()
    assert len(docs) >= 40
    assert all(d["description"] for d in docs)
    top3 = [h["name"] for h in sr.route("debug a failing test", k=3)]
    assert "systematic-debugging" in top3
    assert sr.route("security vulnerability scan", k=1)[0]["name"] == "security-scanning"
    assert sr.route("websocket realtime updates", k=1)[0]["name"] == "real-time-websockets"
    zh = [h["name"] for h in sr.route("调试 报错", k=3)]
    assert "systematic-debugging" in zh
    assert sr.route("多语言 国际化", k=1)[0]["name"] == "internationalization-i18n"


def test_cli(skills, capsys):
    assert sr.main(["extract pdf", "-k", "2", "--skills-dir", str(skills), "--json"]) == 0
    hits = json.loads(capsys.readouterr().out)
    assert hits[0]["name"] == "pdf-tools" and len(hits) <= 2
    assert sr.main(["zzzqqq", "--skills-dir", str(skills)]) == 0
    assert "no matching skills" in capsys.readouterr().out
