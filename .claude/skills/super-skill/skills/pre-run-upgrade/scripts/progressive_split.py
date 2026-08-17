#!/usr/bin/env python3
"""Progressive-disclosure splitter for oversized sub-skill SKILL.md files.

Moves the least-operational sections of a >500-line SKILL.md into
`references/details.md`, keeping the SKILL.md core under budget and leaving
a pointer. Section preference (what moves first):

1. `Version History` / `References` (pure boilerplate)
2. Topic sections, from the LAST backwards (reference-dump tails)
3. `Best Practices` / `Checklist` (only if still over budget)

Always kept: the title/intro, `Integration with Super-Skill`, `Deliverables`.
Relative links inside moved content are re-based with `../` so they keep
resolving from the deeper references/ directory.

Usage:
    python progressive_split.py <skill-dir> [<skill-dir>...] [--dry-run] [--target N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
SECTION_SPLIT_RE = re.compile(r"(?m)^(?=## )")
HEADING_RE = re.compile(r"^## (?P<title>.+?)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\]\((?P<target>[^)\s]+)\)")

KEEP_ALWAYS = {"integration with super-skill", "deliverables"}
MOVE_FIRST = {"version history", "references"}
MOVE_LAST = {"best practices", "best practices checklist", "checklist", "checklists"}
DEFAULT_TARGET = 490
POINTER_MARGIN = 12  # lines the appended Detail Reference pointer will cost


def _force_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def _norm(title: str | None) -> str:
    return title.strip().casefold() if title else ""


def split_sections(body: str) -> list[tuple[str | None, str]]:
    """Split the body into (heading-title, text) pairs; intro has title None.

    Fence-aware: `## ` headings inside ``` / ~~~ blocks (README templates,
    changelog examples) are template content, not real sections — splitting
    there would tear the fence across two files.
    """
    lines = body.splitlines(keepends=True)
    fence_state = scan_fences(lines)
    parts: list[str] = []
    current: list[str] = []
    for line, in_fence in zip(lines, fence_state):
        if not in_fence and line.startswith("## "):
            parts.append("".join(current))
            current = [line]
        else:
            current.append(line)
    parts.append("".join(current))

    sections: list[tuple[str | None, str]] = []
    for part in parts:
        if not part.strip():
            continue
        match = HEADING_RE.match(part)
        title = match.group("title").strip() if match else None
        sections.append((title, part.rstrip() + "\n"))
    return sections


FENCE_RE = re.compile(r"^(?P<marker>```+|~~~+)[ \t]*(?P<info>[^`\s]*)[ \t]*$")


def scan_fences(lines: list[str]) -> list[bool]:
    """Per-line in-fence state, CommonMark-aware (close needs >= open length)."""
    state: list[bool] = []
    open_fence: tuple[str, int] | None = None
    for line in lines:
        match = FENCE_RE.match(line)
        if match is not None:
            marker = match.group("marker")
            char, length = marker[0], len(marker)
            if open_fence is None:
                open_fence = (char, length)
                state.append(True)
            elif char == open_fence[0] and length >= open_fence[1] and not match.group("info"):
                open_fence = None
                state.append(False)
            else:
                state.append(True)
        else:
            state.append(open_fence is not None)
    return state


def plan_moves(
    sections: list[tuple[str | None, str]],
    target: int,
    keep_extra: set[str] | None = None,
) -> tuple[list[tuple[str | None, str]], list[tuple[str | None, str]]]:
    """Return (kept, moved) with kept body + pointer within target."""
    pinned = {_norm(t) for t in (keep_extra or set())}
    # The pointer section costs lines too — budget for it up front.
    effective = target - POINTER_MARGIN
    kept = list(sections)
    moved: list[tuple[str | None, str]] = []

    def body_lines(parts: list[tuple[str | None, str]]) -> int:
        return sum(len(p.splitlines()) for _, p in parts)

    def is_pinned(title_norm: str) -> bool:
        return title_norm in pinned or title_norm in KEEP_ALWAYS

    def move_indices(predicate) -> list[int]:
        return [i for i, (t, _) in enumerate(kept) if t is not None and predicate(_norm(t))]

    # 1. Boilerplate first.
    for i in sorted(move_indices(lambda n: n in MOVE_FIRST), reverse=True):
        if body_lines(kept) > effective:
            moved.insert(0, kept.pop(i))

    # 2. Topic sections from the tail backwards; never the pinned/keep ones.
    while body_lines(kept) > effective:
        candidates = [
            i for i, (t, _) in enumerate(kept)
            if t is not None
            and not is_pinned(_norm(t))
            and _norm(t) not in MOVE_FIRST
            and _norm(t) not in MOVE_LAST
        ]
        if not candidates:
            break
        moved.insert(0, kept.pop(candidates[-1]))

    # 3. Best-practices/checklist only if still over.
    for i in sorted(move_indices(lambda n: n in MOVE_LAST), reverse=True):
        if body_lines(kept) > effective:
            moved.insert(0, kept.pop(i))

    # Keep original relative order in the moved list.
    order = {id(sec): idx for idx, sec in enumerate(sections)}
    moved.sort(key=lambda sec: order[id(sec)])
    return kept, moved


def rebase_links(text: str, skill_dir: Path) -> str:
    """Prefix ../ to relative links that resolve against the skill dir."""
    def fix(match: re.Match) -> str:
        target = match.group("target")
        if target.startswith(("http://", "https://", "mailto:", "#", "/", "{")):
            return match.group(0)
        path_part = target.split("#")[0]
        if not path_part or "<" in target:
            return match.group(0)
        if (skill_dir / path_part).exists():
            return f"](../{target})"
        return match.group(0)

    return LINK_RE.sub(fix, text)


def split_skill(
    skill_dir: Path,
    target: int = DEFAULT_TARGET,
    dry_run: bool = False,
    keep_extra: set[str] | None = None,
) -> dict:
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return {"skill": skill_dir.name, "error": "no frontmatter"}
    fm_text = text[: match.end()]
    body = text[match.end():]

    current_lines = len(text.splitlines()) - fm_text.count("\n")
    if current_lines <= target:
        return {"skill": skill_dir.name, "noop": True, "body_lines": current_lines}

    sections = split_sections(body)
    kept, moved = plan_moves(sections, target, keep_extra)
    if not moved:
        return {
            "skill": skill_dir.name, "error": "over budget but nothing movable",
            "body_lines": current_lines,
        }

    moved_names = [t for t, _ in moved if t]
    details = (
        f"# {skill_dir.name} — Detail Reference\n\n"
        f"Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade "
        f"(SKILL.md stays under the {target}-line budget; this file loads on demand).\n\n"
        + rebase_links("\n".join(p for _, p in moved).strip() + "\n", skill_dir)
    )
    pointer = (
        "\n## Detail Reference\n\n"
        f"Loaded on demand from [references/details.md](references/details.md): "
        + ", ".join(f"`{n}`" for n in moved_names) + ".\n"
    )
    new_text = fm_text + "\n".join(p for _, p in kept).strip() + "\n" + pointer

    if not dry_run:
        refs = skill_dir / "references"
        refs.mkdir(exist_ok=True)
        (refs / "details.md").write_text(details, encoding="utf-8")
        skill_md.write_text(new_text, encoding="utf-8")

    new_lines = len(new_text.splitlines()) - fm_text.count("\n")
    return {
        "skill": skill_dir.name,
        "body_lines": current_lines,
        "new_body_lines": new_lines,
        "moved_sections": moved_names,
        "dry_run": dry_run,
    }


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill_dirs", nargs="+")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET)
    parser.add_argument(
        "--keep",
        default="",
        help="comma-separated section titles to pin in SKILL.md (never moved)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    keep_extra = {t.strip() for t in args.keep.split(",") if t.strip()}
    reports = [
        split_skill(Path(d), args.target, args.dry_run, keep_extra)
        for d in args.skill_dirs
    ]

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for r in reports:
            if "error" in r:
                print(f"  {r['skill']}: ERROR {r['error']}")
            elif r.get("noop"):
                print(f"  {r['skill']}: no-op (body {r['body_lines']} <= {args.target})")
            else:
                mode = "would move" if args.dry_run else "moved"
                print(
                    f"  {r['skill']}: body {r['body_lines']} -> {r['new_body_lines']} "
                    f"({mode}: {', '.join(r['moved_sections'])})"
                )
    return 1 if any("error" in r for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
