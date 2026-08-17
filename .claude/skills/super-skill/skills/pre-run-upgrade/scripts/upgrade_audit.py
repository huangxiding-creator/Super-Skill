#!/usr/bin/env python3
"""Per-sub-skill upgrade audit (pre-run-upgrade skill).

Audits every `skills/<name>/SKILL.md` for the qualities a well-upgraded
sub-skill must have:

- frontmatter parses; `name` matches the directory name
- `description` present, trigger-useful (>= 40 chars), within the Claude Code
  limit (<= 1024 chars)
- body within the progressive-disclosure budget (<= 500 lines)
- relative Markdown links resolve to real files (per-skill attribution)

Errors fail the audit (exit 1); warnings are reported but non-fatal.

Usage:
    python upgrade_audit.py [skills-root] [--json] [--skill NAME]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
KEY_VALUE_RE = re.compile(r"^(?P<key>[A-Za-z_-]+)\s*:\s*(?P<value>.*)$", re.MULTILINE)
LINK_RE = re.compile(r"\]\((?P<target>[^)\s]+)\)")

MIN_DESCRIPTION_CHARS = 40
MAX_DESCRIPTION_CHARS = 1024
MAX_BODY_LINES = 500


def _force_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return {}
    return {
        m.group("key").strip(): m.group("value").strip()
        for m in KEY_VALUE_RE.finditer(match.group(1))
    }


def frontmatter_line_count(text: str) -> int:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return 0
    return text[: match.end()].count("\n")


FENCE_RE = re.compile(r"^(?P<marker>```+|~~~+)[ \t]*(?P<info>[^`\s]*)[ \t]*$")


def check_links(text: str, skill_md: Path) -> list[str]:
    """Return error strings for relative links that do not resolve.

    Skips fenced code blocks (CommonMark-aware: a fence closes only at a
    line of the same marker with >= length): templates and examples inside
    them contain placeholder links like {badge_url} or ./docs/API.md that
    describe a *generated* project, not this skill's own files.
    """
    errors: list[str] = []
    open_fence: tuple[str, int] | None = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if match is not None:
            marker = match.group("marker")
            char, length = marker[0], len(marker)
            if open_fence is None:
                open_fence = (char, length)
            elif char == open_fence[0] and length >= open_fence[1] and not match.group("info"):
                open_fence = None
            continue
        if open_fence is not None:
            continue
        for link_match in LINK_RE.finditer(line):
            target = link_match.group("target")
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            if target.startswith("{") or "<" in target:
                continue  # template placeholder, not a path
            path_part = target.split("#")[0]
            if not path_part:
                continue
            resolved = (skill_md.parent / path_part).resolve()
            if not resolved.exists():
                errors.append(f"line {lineno}: unresolved link '{target}'")
    return errors


def audit_skill(skill_dir: Path) -> dict:
    result: dict = {"dir": skill_dir.name, "errors": [], "warnings": []}
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        result["errors"].append("SKILL.md missing")
        return result

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)

    if not fm:
        result["errors"].append("frontmatter missing or unparseable")
        return result

    if "name" not in fm:
        result["errors"].append("frontmatter key 'name' missing")
    elif fm["name"] != skill_dir.name:
        result["errors"].append(
            f"name '{fm['name']}' does not match directory '{skill_dir.name}'"
        )

    if "description" not in fm:
        result["errors"].append("frontmatter key 'description' missing")
    else:
        desc_len = len(fm["description"])
        if desc_len > MAX_DESCRIPTION_CHARS:
            result["errors"].append(
                f"description is {desc_len} chars (> {MAX_DESCRIPTION_CHARS} limit)"
            )
        elif desc_len < MIN_DESCRIPTION_CHARS:
            result["warnings"].append(
                f"description is only {desc_len} chars "
                f"(< {MIN_DESCRIPTION_CHARS}; too thin to trigger reliably)"
            )

    body_lines = len(text.splitlines()) - frontmatter_line_count(text)
    result["body_lines"] = body_lines
    if body_lines > MAX_BODY_LINES:
        result["warnings"].append(
            f"body is {body_lines} lines (> {MAX_BODY_LINES} progressive-disclosure budget)"
        )

    result["errors"].extend(check_links(text, skill_md))
    return result


def audit_all(skills_root: Path, only: str | None = None) -> dict:
    results = []
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        if only and skill_dir.name != only:
            continue
        results.append(audit_skill(skill_dir))
    return {
        "skills_root": str(skills_root),
        "audited": len(results),
        "error_count": sum(len(r["errors"]) for r in results),
        "warning_count": sum(len(r["warnings"]) for r in results),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    here = Path(__file__).resolve().parent
    default_root = here.parent.parent  # skills/pre-run-upgrade/scripts -> skills/

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skills_root", nargs="?", default=str(default_root))
    parser.add_argument("--skill", help="audit only this sub-skill")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    report = audit_all(Path(args.skills_root), args.skill)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"upgrade_audit: {report['audited']} sub-skills under {report['skills_root']}")
        for r in report["results"]:
            status = "OK" if not r["errors"] and not r["warnings"] else (
                "ERROR" if r["errors"] else "WARN"
            )
            body = r.get("body_lines", "-")
            print(f"  [{status}] {r['dir']} (body {body} lines)")
            for err in r["errors"]:
                print(f"      error:   {err}")
            for warn in r["warnings"]:
                print(f"      warning: {warn}")
        print(
            f"upgrade_audit: {report['error_count']} error(s), "
            f"{report['warning_count']} warning(s)"
        )

    return 1 if report["error_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
