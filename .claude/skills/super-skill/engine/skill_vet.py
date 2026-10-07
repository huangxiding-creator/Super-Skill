#!/usr/bin/env python3
"""Pre-install vetting for third-party agent skills (static, offline, stdlib).

Answers one question before ``npx skills add`` / copying a skill folder:
"is this skill safe to install?"  Skills run with the agent's full trust, so a
SKILL.md that says "ignore previous instructions" or a helper script that pipes
``~/.ssh`` to a URL is a supply-chain attack, not a feature.

Borrowed pattern (no code copied):
- NVIDIA/SkillSpector (Apache-2.0): rule categories for skills (prompt
  injection, exfiltration, supply chain, dangerous code, hidden triggers),
  a 0-100 risk score with severity labels, fail-closed resource bounds and
  rule suppression so re-scans surface only what is new.  SkillSpector adds
  AST/taint/YARA/LLM stages; this is the small regex first stage only — a
  CLEAN result is "nothing obvious", never "proven safe".
- Also from SkillSpector: content it cannot inspect (binary/opaque artifacts)
  is reported, never silently skipped.  Files are classified by content, not
  by an extension allowlist: native executables / compiled code (BIN1),
  opaque binaries and archives (BIN2) and symlinks escaping the bundle (LNK1)
  are findings, and every other text file is scanned whatever its extension.

Usage::

    python skill_vet.py <skill-dir-or-file> [--json] [--fail-on high] [--ignore RULE]

Exit code 1 when the verdict is at or above ``--fail-on`` (default ``high``).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_WEIGHT = {"low": 3, "medium": 8, "high": 20, "critical": 40}
LEVELS = ["clean", "low", "medium", "high", "critical"]
MAX_HITS_PER_RULE = 3          # one noisy rule cannot dominate the score
MAX_FILES = 2000               # fail-closed bounds: refuse to call huge bundles clean
MAX_TOTAL_BYTES = 20 * 1024 * 1024
MAX_FILE_BYTES = 1024 * 1024
SNIFF_BYTES = 8192             # head read to tell text from binary
TEXT_EXT = {
    "", ".md", ".mdx", ".txt", ".py", ".sh", ".bash", ".zsh", ".ps1", ".psm1",
    ".bat", ".cmd", ".js", ".mjs", ".cjs", ".ts", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".rb", ".pl",
}
# Inert data the agent does not execute: only checked for disguised executables.
MEDIA_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".avif", ".tif", ".tiff",
    ".pdf", ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".mp3", ".wav", ".ogg", ".mp4", ".webm", ".mov",
    ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp",
}
# Compiled or host-executed code: the source cannot be reviewed, so never CLEAN.
EXEC_EXT = {
    ".exe", ".dll", ".so", ".dylib", ".sys", ".msi", ".scr", ".node", ".wasm",
    ".jar", ".class", ".pyc", ".pyo", ".pyd",
    ".vbs", ".vbe", ".jse", ".wsf", ".wsh", ".hta", ".lnk",
    ".apk", ".deb", ".rpm", ".appimage",
}
# PE, ELF, Mach-O (both endians, 32/64, fat/Java class), WebAssembly.
_EXEC_MAGIC = (b"MZ", b"\x7fELF", b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe",
               b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\x00asm")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

_I = re.IGNORECASE
# (rule id, category, severity, compiled regex, human message)
RULES = [
    ("PI1", "prompt-injection", "high",
     re.compile(r"\b(ignore|disregard|forget)\s+(all\s+|any\s+)?(previous|prior|above|earlier|system)\s+"
                r"(instructions|rules|prompts?|guidelines)", _I),
     "instruction-override phrase"),
    ("PI2", "prompt-injection", "high",
     re.compile(r"\b(do\s+not|don't|never)\s+(tell|inform|reveal\s+to|mention\s+to|notify)\s+the\s+user", _I),
     "asks the agent to hide actions from the user"),
    ("PI3", "prompt-injection", "medium",
     re.compile(r"\bwithout\s+(asking|telling|confirming\s+with|notifying)\s+the\s+user", _I),
     "acts without user confirmation"),
    ("EX1", "exfiltration", "critical",
     re.compile(r"(curl|wget|invoke-webrequest|invoke-restmethod|\biwr\b|requests\.(post|put)|fetch\s*\()"
                r"[^\n]{0,200}(\$\{?\w*(token|secret|password|api_?key)\w*|\.ssh|\.aws|\.netrc|\.env\b|credentials)",
                _I),
     "network call carrying secrets or credential files"),
    ("EX2", "exfiltration", "high",
     re.compile(r"(~|\$home|%userprofile%|\$env:userprofile)[/\\]\.(ssh|aws|gnupg|kube|docker)\b|\bid_(rsa|ed25519)\b"
                r"|\.netrc\b", _I),
     "reads credential stores"),
    ("OB1", "obfuscation", "critical",
     re.compile(r"base64\s+(-d|--decode)[^\n]*\|\s*(sudo\s+)?(ba|z|da)?sh\b"
                r"|\b(eval|exec)\s*\([^\n]*(b64decode|atob|frombase64string)", _I),
     "decodes and executes hidden payload"),
    ("RC1", "supply-chain", "high",
     re.compile(r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b"
                r"|\biex\b[^\n]*(downloadstring|invoke-webrequest|\biwr\b)", _I),
     "pipes a remote script straight into a shell"),
    ("DS1", "destructive", "high",
     re.compile(r"\brm\s+-[a-z]*r[a-z]*\s+(/|~|\$home)(\s|$|\*)|\bmkfs(\.\w+)?\s"
                r"|\bdd\s+if=[^\n]*of=/dev/(sd|nvme|disk)"
                r"|remove-item[^\n]*-recurse[^\n]*(c:\\\s|\$env:userprofile\b)", _I),
     "wipes home, root or a disk"),
    ("PS1", "persistence", "high",
     re.compile(r"authorized_keys|\bcrontab\s+-|\bschtasks\s+/create|\blaunchctl\s+load", _I),
     "installs persistence or remote access"),
    ("PS2", "agent-tampering", "medium",
     re.compile(r"(>>?|write|edit|modify|overwrite)[^\n]{0,80}(\.claude[/\\]settings(\.local)?\.json|\.bashrc|\.zshrc"
                r"|\.profile\b|claude_desktop_config\.json)", _I),
     "rewrites agent or shell configuration"),
    ("PE1", "excessive-agency", "medium",
     re.compile(r"--dangerously-skip-permissions|allowed-tools:[^\n]*Bash\(\*\)|\bchmod\s+(-R\s+)?777\b", _I),
     "requests blanket permissions"),
    ("HU1", "hidden-trigger", "high",
     re.compile("[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]"),
     "zero-width or bidi control characters (hidden text)"),
]


def _iter_files(target: Path):
    if target.is_file():
        yield target
        return
    for p in sorted(target.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(target).parts):
            continue
        if p.is_symlink() or p.is_file():
            yield p


def _head(path: Path):
    try:
        with open(path, "rb") as fh:
            return fh.read(SNIFF_BYTES)
    except OSError:
        return None


def _escapes(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return False
    except (ValueError, OSError, RuntimeError):
        return True


def _level(score: int, worst: str) -> str:
    if worst == "critical":
        return "critical"
    if worst == "high" or score >= 40:
        return "high"
    if score >= 10:
        return "medium"
    if score > 0:
        return "low"
    return "clean"


def scan(target, ignore=()) -> dict:
    """Scan a skill folder or file. Returns {target, files, score, level, findings}."""
    target = Path(target)
    ignore = {r.upper() for r in ignore}
    findings, files, total = [], 0, 0
    if not target.exists():
        raise FileNotFoundError(str(target))
    root = target.resolve() if target.is_dir() else None

    def flag(rule, category, severity, rel, message):
        if rule not in ignore:
            findings.append({"rule": rule, "category": category, "severity": severity,
                             "file": rel, "line": 0, "message": message})

    for path in _iter_files(target):
        rel = str(path.relative_to(target)) if root is not None else path.name
        if root is not None and path.is_symlink():
            # In-bundle links are scanned via their real file; never follow a link out.
            if _escapes(path, root):
                flag("LNK1", "opaque-artifact", "high", rel,
                     "symlink points outside the skill folder — would expose host files after install")
            continue
        suffix = path.suffix.lower()
        head = _head(path)
        if head is None:
            continue
        if suffix in EXEC_EXT or (b"\0" in head and head.startswith(_EXEC_MAGIC)):
            flag("BIN1", "opaque-artifact", "high", rel,
                 "executable or compiled code — source not inspectable, review manually")
            continue
        if suffix in MEDIA_EXT:
            continue
        if suffix not in TEXT_EXT and b"\0" in head:
            flag("BIN2", "opaque-artifact", "medium", rel,
                 "opaque binary or archive — not scanned, review manually")
            continue
        files += 1
        size = path.stat().st_size
        total += size
        if files > MAX_FILES or total > MAX_TOTAL_BYTES:
            findings.append({"rule": "BND1", "category": "bounds", "severity": "high",
                             "file": rel, "line": 0,
                             "message": "bundle exceeds scan bounds — review manually (fail-closed)"})
            break
        if size > MAX_FILE_BYTES:
            findings.append({"rule": "BND2", "category": "bounds", "severity": "medium",
                             "file": rel, "line": 0,
                             "message": "file too large to scan — review manually"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for rid, cat, sev, rx, msg in RULES:
                if rid in ignore or not rx.search(line):
                    continue
                findings.append({"rule": rid, "category": cat, "severity": sev, "file": rel,
                                 "line": lineno, "message": msg, "excerpt": line.strip()[:160]})
    counted, score, worst = {}, 0, "clean"
    for f in findings:
        counted[f["rule"]] = counted.get(f["rule"], 0) + 1
        if counted[f["rule"]] <= MAX_HITS_PER_RULE:
            score += SEVERITY_WEIGHT[f["severity"]]
        if LEVELS.index(f["severity"]) > LEVELS.index(worst):
            worst = f["severity"]
    score = min(100, score)
    return {"target": str(target), "files": files, "score": score,
            "level": _level(score, worst), "findings": findings}


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Static pre-install vetting for agent skills.")
    ap.add_argument("target", help="skill directory or single file")
    ap.add_argument("--json", action="store_true", help="print the full JSON report")
    ap.add_argument("--fail-on", default="high", choices=LEVELS[1:],
                    help="exit 1 at or above this level (default: high)")
    ap.add_argument("--ignore", action="append", default=[], metavar="RULE",
                    help="suppress a reviewed rule id (repeatable), e.g. --ignore PE1")
    args = ap.parse_args(argv)
    try:
        report = scan(args.target, args.ignore)
    except FileNotFoundError as exc:
        print(f"skill_vet: not found: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"skill_vet: {report['level'].upper()} (score {report['score']}/100, "
              f"{report['files']} files, {len(report['findings'])} findings)")
        for f in report["findings"][:40]:
            print(f"  [{f['severity']}] {f['rule']} {f['file']}:{f['line']} — {f['message']}")
    return 1 if LEVELS.index(report["level"]) >= LEVELS.index(args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
