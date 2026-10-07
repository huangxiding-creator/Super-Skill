#!/usr/bin/env python3
"""Ralph loop driver (W5): unattended, one task per fresh-context iteration.

Each iteration: breaker check → claim the next ready task → write a prompt →
run the agent (default ``claude -p`` with turn/budget caps) → run the task's
``verify`` command ourselves (ground truth, not the agent's claim) → keep
(git commit, task done, progress note) or discard (attempt recorded, breaker
fed). The loop exits when every task is done AND the agent printed
``EXIT_SIGNAL: true`` on a final confirmation pass (dual-condition exit).

Patterns: snarktank/ralph ``prd.json`` + ``progress.txt`` (MIT),
frankbria/ralph-claude-code circuit breaker + dual exit (MIT),
karpathy/autoresearch keep/discard ledger ``experiments.tsv`` (pattern).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import force_utf8_stdio, ledger, now_iso, sdir  # noqa: E402
import loop_guard  # noqa: E402
import taskgraph  # noqa: E402

DEFAULT_AGENT = "claude -p --max-turns {max_turns} --max-budget-usd {budget} --permission-mode acceptEdits"

PROMPT = """You are one iteration of an unattended Super-Skill Ralph loop.
Work on EXACTLY ONE task, then stop. Do not start other tasks.

## Task {id}: {title}
- covers requirements: {covers}
- files likely involved: {files}
- verify command (must exit 0): `{verify}`
- notes: {notes}

## Rules
1. Implement the smallest change that makes the verify command pass; prefer deleting code to adding it.
2. Run the verify command yourself before finishing.
3. Do not edit .super-skill/state.json or tasks.json — the loop records results.
4. Append 1-3 bullet learnings for future iterations at the end of your reply under "LEARNINGS:".
{pressure}
## Recent progress (tail of progress.txt)
{progress}
"""

CONFIRM = """All tasks of this Super-Skill run pass their verify commands.
Review the repository once: if the work is genuinely complete, reply with a one-line summary
and a final line exactly `EXIT_SIGNAL: true`. If something is missing, describe it and do NOT print the signal."""


def _run_shell(cmd: str, cwd: Path, timeout: int, stdin: str | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, shell=True, cwd=str(cwd), input=stdin, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        return 124, out + "\n[timeout]"


def _progress_tail(root: Path, n: int = 30) -> str:
    path = root / "progress.txt"
    try:
        return "\n".join(path.read_text(encoding="utf-8").splitlines()[-n:]) or "(none yet)"
    except OSError:
        return "(none yet)"


def _append(path: Path, text: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)


def _tsv(root: Path, row: list) -> None:
    path = root / "experiments.tsv"
    if not path.exists():
        _append(path, "ts\titeration\ttask\tstatus\tseconds\tnote\n")
    _append(path, "\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in row) + "\n")


def _commit(root: Path, message: str) -> bool:
    if not (root / ".git").exists():
        return False
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(root), capture_output=True, timeout=60, check=True)
        r = subprocess.run(["git", "commit", "-m", message], cwd=str(root), capture_output=True, timeout=60)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _agent(cmd_tpl: str, prompt: str, root: Path, n: int, max_turns: int, budget: float,
           timeout: int) -> tuple[int, str]:
    work = sdir(root) / "ralph"
    work.mkdir(parents=True, exist_ok=True)
    pfile = work / f"prompt-{n}.md"
    pfile.write_text(prompt, encoding="utf-8")
    # double quotes work in both POSIX sh and Windows cmd.exe
    cmd = cmd_tpl.format(prompt_file=f'"{pfile.as_posix()}"', max_turns=max_turns, budget=budget)
    code, out = _run_shell(cmd, root, timeout, stdin=None if "{prompt_file}" in cmd_tpl else prompt)
    (work / f"output-{n}.txt").write_text(out, encoding="utf-8")
    return code, out


def run(root: Path, agent_cmd: str = DEFAULT_AGENT, max_iterations: int = 30, max_turns: int = 40,
        budget: float = 2.0, agent_timeout: int = 1800, verify_timeout: int = 900,
        commit: bool = True, require_exit_signal: bool = True, sleep: float = 0.0) -> dict:
    root = Path(root)
    summary = {"iterations": 0, "kept": 0, "discarded": 0, "crashed": 0, "exit": "max_iterations"}
    for n in range(1, max_iterations + 1):
        ok, why = loop_guard.can_proceed(root)
        if not ok:
            summary["exit"] = f"breaker: {why}"
            break
        tasks = taskgraph.load(root)["tasks"]
        prog = taskgraph.progress(tasks)
        if prog["total"] and prog["done"] == prog["total"]:
            if not require_exit_signal:
                summary["exit"] = "all_done"
                break
            code, out = _agent(agent_cmd, CONFIRM, root, n, max_turns, budget, agent_timeout)
            summary["iterations"] += 1
            if loop_guard.exit_ok(out, True):
                summary["exit"] = "all_done+exit_signal"
                ledger(root, "note", msg="ralph: all tasks done, EXIT_SIGNAL received")
                break
            loop_guard.record(root, progress=False, error="confirmation without EXIT_SIGNAL")
            _tsv(root, [now_iso(), n, "-", "discard", 0, "confirmation pass: no EXIT_SIGNAL"])
            continue
        task = taskgraph.claim(root, owner="ralph")
        if task is None:
            summary["exit"] = "no_ready_tasks" if not prog["blocked"] else "only_blocked_tasks"
            break
        st = loop_guard.load(root)
        level, advice = loop_guard.pressure(st["consecutive_failures"])
        prompt = PROMPT.format(id=task["id"], title=task["title"], covers=", ".join(task["covers"]) or "—",
                               files=", ".join(task["files"]) or "—", verify=task.get("verify") or "(none)",
                               notes=(task.get("notes") or "—")[-600:],
                               pressure=f"\n## Pressure {level}\n{advice}\n" if advice else "",
                               progress=_progress_tail(root))
        t0 = time.time()
        code, out = _agent(agent_cmd, prompt, root, n, max_turns, budget, agent_timeout)
        summary["iterations"] += 1
        if code != 0 and not task.get("verify"):
            taskgraph.fail(root, task["id"], f"agent exit {code}")
            loop_guard.record(root, progress=False, error=out[-800:])
            summary["crashed"] += 1
            _tsv(root, [now_iso(), n, task["id"], "crash", round(time.time() - t0), f"agent exit {code}"])
            continue
        vcode, vout = (0, "") if not task.get("verify") else _run_shell(task["verify"], root, verify_timeout)
        secs = round(time.time() - t0)
        learnings = out.split("LEARNINGS:", 1)[1].strip()[:800] if "LEARNINGS:" in out else ""
        if vcode == 0:
            taskgraph.set_status(root, task["id"], "done", "verified by ralph")
            committed = commit and _commit(root, f"ralph: {task['id']} {task['title']}")
            loop_guard.record(root, progress=True)
            summary["kept"] += 1
            _append(root / "progress.txt", f"\n## {now_iso()} {task['id']} keep\n{learnings or '- (no learnings reported)'}\n")
            _tsv(root, [now_iso(), n, task["id"], "keep", secs, "committed" if committed else "verified"])
        else:
            taskgraph.fail(root, task["id"], f"verify exit {vcode}: {vout[-300:]}")
            loop_guard.record(root, progress=False, error=vout[-800:])
            summary["discarded"] += 1
            _append(root / "progress.txt", f"\n## {now_iso()} {task['id']} discard (verify exit {vcode})\n"
                                           f"{learnings or '- verify failed'}\n")
            _tsv(root, [now_iso(), n, task["id"], "discard", secs, f"verify exit {vcode}"])
        if sleep:
            time.sleep(sleep)
    ledger(root, "note", msg=f"ralph finished: {json.dumps(summary)}")
    return summary


def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="ralph", description="unattended one-task-per-iteration loop")
    ap.add_argument("--root", default=".")
    ap.add_argument("--agent-cmd", default=DEFAULT_AGENT,
                    help="command run per iteration; prompt via stdin unless it contains {prompt_file}")
    ap.add_argument("--max-iterations", type=int, default=30)
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--budget-usd", type=float, default=2.0, help="per-iteration budget cap")
    ap.add_argument("--agent-timeout", type=int, default=1800)
    ap.add_argument("--verify-timeout", type=int, default=900)
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--no-exit-signal", action="store_true", help="exit on all-done without confirmation")
    ap.add_argument("--sleep", type=float, default=0.0)
    args = ap.parse_args(argv)
    res = run(Path(args.root).resolve(), args.agent_cmd, args.max_iterations, args.max_turns,
              args.budget_usd, args.agent_timeout, args.verify_timeout, not args.no_commit,
              not args.no_exit_signal, args.sleep)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["exit"].startswith("all_done") else 1


if __name__ == "__main__":
    sys.exit(main())
