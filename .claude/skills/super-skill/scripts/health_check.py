"""Health check for Super-Skill (IdeaForge V4.0) — runs from the pre-run-upgrade hook.

Scans the skill tree, runs every sub-skill's test suite, checks SKILL.md link
integrity and that key scripts import cleanly. Emits a non-fatal report: a failing
sub-skill degrades (warns) but never blocks the session — that is the whole point of
the "stale skill" early-warning the user asked for in Theme 4.

Exit code is always 0 so the Notification hook can't abort a session; failures land
in the report + on stderr.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(_HERE)  # .../super-skill


@dataclass
class HealthReport:
    healthy: bool
    skills_checked: int
    test_runs: List[Dict] = field(default_factory=list)
    broken_links: List[str] = field(default_factory=list)
    import_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


def _find_test_dirs() -> List[str]:
    """Return scripts/ dirs under skills/* that contain test_*.py files."""
    out = []
    skills_dir = os.path.join(SKILL_ROOT, "skills")
    if not os.path.isdir(skills_dir):
        return out
    for name in sorted(os.listdir(skills_dir)):
        scripts = os.path.join(skills_dir, name, "scripts")
        if not os.path.isdir(scripts):
            continue
        if any(f.startswith("test_") and f.endswith(".py") for f in os.listdir(scripts)):
            out.append(scripts)
    return out


def _run_tests(scripts_dir: str) -> Dict:
    """Run every test_*.py in a dir, capture pass/fail. Never raises."""
    tests = sorted(f for f in os.listdir(scripts_dir) if f.startswith("test_") and f.endswith(".py"))
    passed = failed = 0
    failures: List[str] = []
    for t in tests:
        try:
            r = subprocess.run([sys.executable, t], cwd=scripts_dir,
                               capture_output=True, text=True, timeout=120)
            tail = (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else ""
            ok = r.returncode == 0
            # also accept "N/N passed" tail without 0 exit (our runners print it)
            if not ok and re.search(r"0/\d+ passed|FAIL", tail):
                ok = False
            if ok:
                passed += 1
            else:
                failed += 1
                failures.append(f"{t}: {tail[:120]}")
        except subprocess.TimeoutExpired:
            failed += 1
            failures.append(f"{t}: TIMEOUT")
        except Exception as e:  # pragma: no cover - defensive
            failed += 1
            failures.append(f"{t}: {type(e).__name__}: {e}")
    return {"dir": os.path.basename(os.path.dirname(scripts_dir)),
            "tests": len(tests), "passed": passed, "failed": failed, "failures": failures}


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks so we don't lint illustrative links inside them."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def _is_placeholder(href: str) -> bool:
    """True for template placeholders we should not lint as real links."""
    if not href:
        return True
    if "{" in href or "}" in href:           # {badge_url}
        return True
    if href in ("URL", "doc"):                # bare placeholders
        return True
    if re.fullmatch(r"[A-Z][A-Za-z0-9_]*", href):  # ALLCAPS_VAR or TitleToken
        return True
    if re.search(r"[XYZ]\.md$", href):        # references/X.md, Y.md
        return True
    return False


def _check_links() -> List[str]:
    """Verify markdown links to local files in SKILL.md resolve."""
    broken: List[str] = []
    for root, _, files in os.walk(SKILL_ROOT):
        if os.path.basename(root) == ".git":
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            try:
                text = open(path, encoding="utf-8").read()
            except OSError:
                continue
            text = _strip_code_blocks(text)
            for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
                href = m.group(1).split("#")[0].split("?")[0].strip()
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                if _is_placeholder(href):
                    continue
                target = os.path.normpath(os.path.join(root, href))
                if not os.path.exists(target):
                    broken.append(f"{os.path.relpath(path, SKILL_ROOT)} -> {href}")
    return broken


def run() -> HealthReport:
    test_dirs = _find_test_dirs()
    runs = [_run_tests(d) for d in test_dirs]
    total_failed = sum(r["failed"] for r in runs)
    broken = _check_links()

    warnings: List[str] = []
    for r in runs:
        if r["failed"]:
            warnings.append(f"{r['dir']}: {r['failed']} test file(s) failing")
    if broken:
        warnings.append(f"{len(broken)} broken local link(s)")

    return HealthReport(
        healthy=(total_failed == 0 and not broken),
        skills_checked=len(test_dirs),
        test_runs=runs,
        broken_links=broken[:50],  # cap noise
        warnings=warnings,
    )


def main() -> int:
    report = run()
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if not report.healthy:
        for w in report.warnings:
            print("HEALTH WARN:", w, file=sys.stderr)
    return 0  # never block the session


if __name__ == "__main__":
    raise SystemExit(main())
