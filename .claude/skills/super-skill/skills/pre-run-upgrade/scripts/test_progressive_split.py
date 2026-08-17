#!/usr/bin/env python3
"""Tests for progressive_split.py (pre-run-upgrade skill).

pytest-compatible; also runnable standalone:
    python test_progressive_split.py
Prints "N/N passed" and exits 1 on any failure.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("progressive_split", HERE / "progressive_split.py")
ps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ps)

DESC = "A valid description with plenty of triggering keywords inside it for routing."


def _skill_md(sections: list[str], name: str = "demo-skill") -> str:
    body = "\n".join(sections)
    return f"---\nname: {name}\ndescription: {DESC}\n---\n\n# Demo\n\n{body}\n"


def test_noop_when_under_target() -> None:
    text = _skill_md(["## One\n\nshort\n"])
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(text, encoding="utf-8")
        report = ps.split_skill(d, target=100)
        assert report.get("noop") is True
        assert not (d / "references").exists()


def test_boilerplate_moves_first() -> None:
    sections = [
        "## Intro Topic\n\n" + "line\n" * 30,
        "## Integration with Super-Skill\n\n" + "line\n" * 5,
        "## Deliverables\n\n- item\n",
        "## Version History\n\n" + "line\n" * 4,
        "## References\n\n" + "line\n" * 4,
    ]
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(_skill_md(sections), encoding="utf-8")
        report = ps.split_skill(d, target=40)
        assert "Version History" in report["moved_sections"]
        assert "References" in report["moved_sections"]
        assert "Integration with Super-Skill" not in report["moved_sections"]
        assert "Deliverables" not in report["moved_sections"]


def test_tail_topic_moves_when_over() -> None:
    sections = [
        "## Topic A\n\n" + "line\n" * 30,
        "## Topic B\n\n" + "line\n" * 30,
        "## Integration with Super-Skill\n\nline\n",
        "## Version History\n\nline\n",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(_skill_md(sections), encoding="utf-8")
        report = ps.split_skill(d, target=50)
        assert "Topic B" in report["moved_sections"]
        assert "Topic A" not in report["moved_sections"]
        assert report["new_body_lines"] <= 50


def test_headings_inside_fences_are_not_sections() -> None:
    fenced = "\n".join([
        "```markdown",
        "## Template Heading",
        "[![CI]({badge_url})]({workflow_url})",
        "```",
    ])
    sections = [
        f"## Real Topic\n\n{fenced}\n\n" + "line\n" * 60,
        "## Integration with Super-Skill\n\nline\n",
        "## Version History\n\nline\n",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(_skill_md(sections), encoding="utf-8")
        kept_text, moved = ps.plan_moves(
            ps.split_sections(_skill_md(sections).split("---\n\n", 1)[1]), 45
        )
        titles = [t for t, _ in moved if t]
        assert "Template Heading" not in titles
        # The fenced block must survive intact inside whichever section holds it.
        joined = "".join(p for _, p in moved) + "".join(p for _, p in kept_text)
        assert "## Template Heading" in joined
        assert "[![CI]({badge_url})]({workflow_url})" in joined


def test_four_backtick_outer_fence_shields_nested() -> None:
    """CommonMark: ``` inside ```` does not close the outer fence."""
    nested = "\n".join([
        "````markdown",
        "## Outer Example",
        "```json",
        '{"a": 1}',
        "```",
        "````",
    ])
    body = f"# Demo\n\n## Topic\n\n{nested}\n\n## Integration with Super-Skill\n\nline\n"
    secs = ps.split_sections(body)
    titles = [t for t, _ in secs if t]
    assert "Outer Example" not in titles
    assert "Topic" in titles
    state = ps.scan_fences(body.splitlines())
    assert state[-1] is False  # balanced


def test_pointer_added_and_details_written() -> None:
    sections = [
        "## Topic A\n\n" + "line\n" * 40,
        "## Integration with Super-Skill\n\nline\n",
        "## Version History\n\nline\n",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        (d / "SKILL.md").write_text(_skill_md(sections), encoding="utf-8")
        ps.split_skill(d, target=50)
        new_text = (d / "SKILL.md").read_text(encoding="utf-8")
        details = (d / "references" / "details.md").read_text(encoding="utf-8")
        assert "## Detail Reference" in new_text
        assert "references/details.md" in new_text
        assert "Version History" in details
        assert "Detail Reference" in details  # provenance header


def test_dry_run_writes_nothing() -> None:
    sections = ["## Topic A\n\n" + "line\n" * 40, "## Version History\n\nline\n"]
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        original = _skill_md(sections)
        (d / "SKILL.md").write_text(original, encoding="utf-8")
        report = ps.split_skill(d, target=30, dry_run=True)
        assert report.get("dry_run") is True
        assert (d / "SKILL.md").read_text(encoding="utf-8") == original
        assert not (d / "references").exists()


def test_keep_extra_pins_sections() -> None:
    sections = [
        "## Precious\n\n" + "line\n" * 40,
        "## Expendable\n\n" + "line\n" * 40,
        "## Version History\n\nline\n",
    ]
    text = _skill_md(sections)
    kept, moved = ps.plan_moves(
        ps.split_sections(text.split("---\n\n", 1)[1]), 50, {"Precious"}
    )
    moved_titles = [t for t, _ in moved if t]
    assert "Precious" not in moved_titles
    assert "Expendable" in moved_titles


def test_moved_relative_links_rebased() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "demo-skill"
        d.mkdir()
        (d / "CHART.md").write_text("# chart\n", encoding="utf-8")
        sections = [
            "## Topic A\n\nSee [chart](CHART.md) and [web](https://x.io).\n\n" + "line\n" * 40,
            "## Version History\n\nline\n",
        ]
        (d / "SKILL.md").write_text(_skill_md(sections), encoding="utf-8")
        ps.split_skill(d, target=50)
        details = (d / "references" / "details.md").read_text(encoding="utf-8")
        assert "(../CHART.md)" in details
        assert "https://x.io" in details


def main() -> int:
    tests = [
        test_noop_when_under_target,
        test_boilerplate_moves_first,
        test_tail_topic_moves_when_over,
        test_headings_inside_fences_are_not_sections,
        test_four_backtick_outer_fence_shields_nested,
        test_pointer_added_and_details_written,
        test_dry_run_writes_nothing,
        test_keep_extra_pins_sections,
        test_moved_relative_links_rebased,
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
