"""Reflective mutation (GEPA-style) + pluggable mutator execution.

The prompt shows the mutator the parent's target text (or the one section most
related to the failures when the file is large), the failed tasks with their
evaluator feedback (GEPA's "actionable side information"), the chosen gene's
strategy lines and the simplicity rule. It is written to
``<variant_ws>/MUTATION_PROMPT.md``; the mutator must edit the target copy in
the variant workspace in place and may write a one-line summary to
``<variant_ws>/MUTATION_DESC.txt``.

Mutators:
* ``--mutator-cmd "<cmd with {prompt} {workspace} {target}>"`` -- any command.
* ``claude`` (built-in, explicit opt-in only) --
  ``claude -p --max-turns 8 --max-budget-usd <b> --permission-mode acceptEdits``
  run with cwd = variant workspace.
"""
from __future__ import annotations

import difflib
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

PROMPT_NAME = "MUTATION_PROMPT.md"
DESC_NAME = "MUTATION_DESC.txt"
MAX_FULL_CHARS = 16000
MAX_FEEDBACK_CHARS = 1500

SIMPLICITY_RULE = [
    "Make the SMALLEST change that could fix the failures.",
    "Change ONE section only; do not rewrite or reformat the rest of the file.",
    "Deleting text that keeps the score is a win (simpler is better).",
    "Every added line costs fitness (mu * lines_added / 100); justify it.",
]


# ------------------------------------------------------------------ prompt

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{2,}|[一-鿿]{2,}")


def split_sections(text: str) -> List[Dict[str, str]]:
    """Split markdown into sections at headings (preamble is section 0)."""
    sections: List[Dict[str, str]] = []
    cur = {"heading": "(preamble)", "body": ""}
    for line in text.splitlines(keepends=True):
        m = _HEADING.match(line.rstrip("\r\n"))
        if m:
            if cur["body"].strip() or cur["heading"] != "(preamble)":
                sections.append(cur)
            cur = {"heading": m.group(2).strip(), "body": line}
        else:
            cur["body"] += line
    sections.append(cur)
    return sections


def pick_section(text: str, feedback_text: str) -> Dict[str, str]:
    """Section whose words overlap the feedback most (first on ties)."""
    words = {w.lower() for w in _WORD.findall(feedback_text)}
    best, best_hits = None, -1
    for sec in split_sections(text):
        sec_words = {w.lower() for w in _WORD.findall(sec["body"])}
        hits = len(words & sec_words)
        if hits > best_hits:
            best, best_hits = sec, hits
    return best or {"heading": "(whole file)", "body": text}


def build_prompt(parent_text: str, target_name: str,
                 per_task: Mapping[str, float], feedback: Mapping[str, str],
                 gene: Mapping, intent: str,
                 max_full_chars: int = MAX_FULL_CHARS) -> str:
    failed = {t: float(s) for t, s in (per_task or {}).items() if float(s) < 1.0}
    lines: List[str] = [
        f"# Mutation request: evolve `{target_name}`",
        "",
        f"Intent: **{intent}** | Gene: `{gene.get('id')}`",
        "",
        f"Edit the file `{target_name}` in this workspace IN PLACE. "
        f"Optionally write a one-line summary of your change to `{DESC_NAME}`.",
        "",
        "## Failed tasks (evaluator feedback)",
        "",
    ]
    if failed:
        for t in sorted(failed):
            fb = str((feedback or {}).get(t, "")).strip().replace("\r", "")
            if len(fb) > MAX_FEEDBACK_CHARS:
                fb = fb[:MAX_FEEDBACK_CHARS] + " ...[truncated]"
            lines.append(f"- `{t}` (score {failed[t]:.2f}): {fb or '(no feedback)'}")
    else:
        lines.append("- none: all tasks pass. Look for a simplification that keeps the "
                     "score (delete redundant text) or reduce token cost.")
    lines += ["", "## Gene strategy", ""]
    lines += [f"- {s}" for s in (gene.get("strategy") or [])]
    lines += ["", "## Simplicity rule", ""]
    lines += [f"- {s}" for s in SIMPLICITY_RULE]
    lines.append("")
    if len(parent_text) <= max_full_chars:
        lines.append(f"## Current content of `{target_name}`")
        body = parent_text
    else:
        fb_text = " ".join(str((feedback or {}).get(t, "")) + " " + t for t in failed)
        sec = pick_section(parent_text, fb_text)
        lines.append(f"## Section to change: `{sec['heading']}` "
                     f"(file is large; only this section is shown)")
        body = sec["body"][:max_full_chars]
    fence = "````" if "```" in body else "```"
    lines += ["", fence, body.rstrip("\n"), fence, ""]
    return "\n".join(lines)


def write_prompt(workspace: Path, prompt: str) -> Path:
    p = Path(workspace) / PROMPT_NAME
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(prompt, encoding="utf-8")
    return p


def read_desc(workspace: Path) -> str:
    try:
        txt = (Path(workspace) / DESC_NAME).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    first = txt.strip().splitlines()
    return first[0].strip()[:200] if first else ""


# ------------------------------------------------------------------ processes

def quote(arg: str) -> str:
    s = str(arg)
    if os.name == "nt":
        return subprocess.list2cmdline([s]) if s else '""'
    return shlex.quote(s)


def fill(template: str, values: Mapping[str, str]) -> str:
    """Replace ``{name}`` placeholders with shell-quoted values (other braces
    in the template are left untouched)."""
    out = template
    for k, v in values.items():
        out = out.replace("{" + k + "}", quote(v))
    return out


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass
    try:
        proc.kill()
    except OSError:
        pass


def run_command(cmd, cwd: Optional[Path], timeout: Optional[float],
                shell: bool = True, stdin_text: Optional[str] = None) -> Dict:
    """Run a command; never raises. Returns {returncode, stdout, stderr, timed_out}."""
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    kwargs = dict(cwd=str(cwd) if cwd else None, shell=shell, env=env,
                  stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.name != "nt":
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except (OSError, ValueError) as exc:
        return {"returncode": -1, "stdout": "", "stderr": f"spawn failed: {exc}",
                "timed_out": False}
    data = stdin_text.encode("utf-8") if stdin_text is not None else None
    try:
        out, err = proc.communicate(input=data, timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=10)
        except (subprocess.TimeoutExpired, OSError, ValueError):
            out, err = b"", b""
        timed_out = True
    return {"returncode": -9 if timed_out else proc.returncode,
            "stdout": (out or b"").decode("utf-8", errors="replace"),
            "stderr": (err or b"").decode("utf-8", errors="replace"),
            "timed_out": timed_out}


def claude_argv(budget_usd: float, max_turns: int = 8) -> List[str]:
    exe = shutil.which("claude") or "claude"
    return [exe, "-p", "--max-turns", str(max_turns), "--max-budget-usd", str(budget_usd),
            "--permission-mode", "acceptEdits"]


def run_mutator(mutator: str, prompt_path: Path, workspace: Path, target: Path,
                timeout: Optional[float] = 900, budget_usd: float = 0.5,
                cwd: Optional[Path] = None) -> Dict:
    """Execute the mutator. ``mutator == "claude"`` selects the built-in
    Claude Code mutator (cwd = workspace); anything else is a command
    template run from ``cwd`` (the invoking directory)."""
    if mutator == "claude":
        instruction = (f"Read {PROMPT_NAME} in the current directory and apply exactly the "
                       f"change it requests to the file {Path(target).name} in this "
                       f"directory. Edit no other file except {DESC_NAME}.")
        return run_command(claude_argv(budget_usd) + [instruction], cwd=workspace,
                           timeout=timeout, shell=False)
    cmd = fill(mutator, {"prompt": str(prompt_path), "workspace": str(workspace),
                         "target": str(target)})
    return run_command(cmd, cwd=cwd, timeout=timeout, shell=True)


def diff_stats(old: str, new: str) -> Dict[str, int]:
    """Count added/removed lines between two texts (difflib unified diff)."""
    added = removed = 0
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0):
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return {"lines_added": added, "lines_removed": removed}


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Debug CLI: print the mutation prompt for a file without running the loop."""
    import argparse
    import json
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from strategies import load_genes  # noqa: E402

    ap = argparse.ArgumentParser(description="Build a reflective mutation prompt.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--result", help="JSON file with {tasks, feedback}")
    ap.add_argument("--gene", help="gene id (default: first gene)")
    ap.add_argument("--intent", default="repair")
    args = ap.parse_args(argv)
    text = Path(args.target).read_text(encoding="utf-8", errors="replace")
    res = json.loads(Path(args.result).read_text(encoding="utf-8")) if args.result else {}
    genes = load_genes()
    gene = next((g for g in genes if g["id"] == args.gene), genes[0])
    sys.stdout.write(build_prompt(text, Path(args.target).name, res.get("tasks") or {},
                                  res.get("feedback") or {}, gene, args.intent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
