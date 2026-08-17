#!/usr/bin/env python3
"""Tests for upgrade_audit.py (pre-run-upgrade skill).

pytest-compatible; also runnable standalone:
    python test_upgrade_audit.py
Prints "N/N passed" and exits 1 on any failure.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("upgrade_audit", HERE / "upgrade_audit.py")
ua = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ua)

VALID_SKILL_MD = """\
---
name: demo-skill
description: Demonstrate a valid skill with a trigger-rich description long enough to be useful for routing decisions by the model.
---

# Demo Skill

Body content with a [valid link](REFERENCE.md).
"""


def _make_skill(root: Path, name: str, content: str, extra_files: list[str] | None = None) -> Path:
    d = root / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(content, encoding="utf-8")
    for rel in extra_files or []:
        target = d / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# ref\n", encoding="utf-8")
    return d


def test_valid_skill_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "demo-skill", VALID_SKILL_MD, ["REFERENCE.md"])
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert result["errors"] == [] and result["warnings"] == []
        assert result["body_lines"] == 4  # total 8 minus 4 frontmatter lines


def test_name_mismatch_is_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        content = VALID_SKILL_MD.replace("name: demo-skill", "name: other-skill")
        _make_skill(root, "demo-skill", content)
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert any("does not match" in e for e in result["errors"])


def test_missing_description_is_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        content = "---\nname: demo-skill\n---\n\nBody.\n"
        _make_skill(root, "demo-skill", content)
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert any("description" in e and "missing" in e for e in result["errors"])


def test_thin_description_warns() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        content = (
            "---\nname: demo-skill\ndescription: too thin\n---\n\nBody.\n"
        )
        _make_skill(root, "demo-skill", content)
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert result["errors"] == []
        assert any("too thin" in w for w in result["warnings"])


def test_oversized_description_is_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        content = (
            f"---\nname: demo-skill\ndescription: {'x' * 1100}\n---\n\nBody.\n"
        )
        _make_skill(root, "demo-skill", content)
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert any("chars" in e for e in result["errors"])


def test_oversized_body_warns() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        body = "\n".join(f"line {i}" for i in range(600))
        content = (
            "---\nname: demo-skill\n"
            "description: A valid description with plenty of triggering keywords inside it.\n"
            f"---\n\n{body}\n"
        )
        _make_skill(root, "demo-skill", content)
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert result["errors"] == []
        assert any("progressive-disclosure" in w for w in result["warnings"])


def test_broken_link_is_error_but_http_and_anchor_skip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        content = (
            "---\nname: demo-skill\n"
            "description: A valid description with plenty of triggering keywords inside it.\n"
            "---\n\n# Demo\n\nSee [missing](NOPE.md), [fine](OK.md), "
            "[web](https://example.com/a.md), and [anchor](#section).\n"
        )
        _make_skill(root, "demo-skill", content, ["OK.md"])
        result = ua.audit_skill(root / "skills" / "demo-skill")
        link_errors = [e for e in result["errors"] if "unresolved link" in e]
        assert len(link_errors) == 1 and "NOPE.md" in link_errors[0]


def test_links_inside_code_fences_are_skipped() -> None:
    """Template placeholders (e.g. {badge_url}, ./docs/API.md inside a README
    template) live in fenced blocks and must not be treated as this skill's
    own links."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fence = "\n".join([
            "```markdown",
            "[![CI]({badge_url})]({workflow_url})",
            "See [API](./docs/API.md).",
            "```",
        ])
        content = (
            "---\nname: demo-skill\n"
            "description: A valid description with plenty of triggering keywords inside it.\n"
            f"---\n\n# Demo\n\n{fence}\n\nReal [link](REAL.md) outside fences.\n"
        )
        _make_skill(root, "demo-skill", content, ["REAL.md"])
        result = ua.audit_skill(root / "skills" / "demo-skill")
        assert result["errors"] == []


def test_missing_skill_md_is_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        d = root / "skills" / "empty-skill"
        d.mkdir(parents=True)
        result = ua.audit_skill(d)
        assert any("SKILL.md missing" in e for e in result["errors"])


def test_audit_all_aggregates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(root, "good-skill", VALID_SKILL_MD, ["REFERENCE.md"])
        bad = (
            "---\nname: wrong-name\ndescription: tiny\n---\n\n[broken](GONE.md)\n"
        )
        _make_skill(root, "bad-skill", bad)
        report = ua.audit_all(root / "skills")
        assert report["audited"] == 2
        assert report["error_count"] >= 3  # name mismatch + broken link (+ none else)
        assert report["warning_count"] >= 1  # thin description


def test_cli_json_and_exit_codes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_skill(
            root, "good-skill",
            VALID_SKILL_MD.replace("demo-skill", "good-skill"),
            ["REFERENCE.md"],
        )

        proc = subprocess.run(
            [sys.executable, str(HERE / "upgrade_audit.py"),
             str(root / "skills"), "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        )
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert payload["error_count"] == 0

        _make_skill(root, "bad-skill", "---\nname: bad-skill\n---\n\nBody.\n")
        proc = subprocess.run(
            [sys.executable, str(HERE / "upgrade_audit.py"),
             str(root / "skills"), "--skill", "bad-skill"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        )
        assert proc.returncode == 1
        assert "error(s)" in proc.stdout


def test_frontmatter_line_count() -> None:
    assert ua.frontmatter_line_count(VALID_SKILL_MD) == 4
    assert ua.frontmatter_line_count("# no frontmatter\n") == 0


def main() -> int:
    tests = [
        test_valid_skill_passes,
        test_name_mismatch_is_error,
        test_missing_description_is_error,
        test_thin_description_warns,
        test_oversized_description_is_error,
        test_oversized_body_warns,
        test_broken_link_is_error_but_http_and_anchor_skip,
        test_links_inside_code_fences_are_skipped,
        test_missing_skill_md_is_error,
        test_audit_all_aggregates,
        test_cli_json_and_exit_codes,
        test_frontmatter_line_count,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS {test.__name__}")
        except AssertionError as exc:
            print(f"  FAIL {test.__name__}: {exc}")
    print(f"{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
