#!/usr/bin/env python3
"""Super-Skill daily self-update (default 22:00 Beijing time, see schedule_daily.py).

Mutual exclusion with the weekly pipeline (which also starts at 22:00 on
Sundays on the maintainer machine) via the shared OS-held lock in
``pipeline_lock.py``. A run killed mid-way (shutdown, time limit) is recovered
by the next preflight: its leftover skill/plugin changes are stashed, never lost.

    D0 preflight  PAUSE flag · lock · clean tree · fast-forward from origin
    D1 radar      GitHub search + watchlist releases + Hacker News (radar.py, no LLM)
    D2 distill    headless `claude -p` studies the candidates and STAGES ≤ N small,
                  high-value improvements in automation/daily_out/ (it never edits the skill)
    D3 apply      deterministic whitelist copy: the verifier (tests, bench, phase
                  contracts, hooks, installer) can never be modified by the run
    D4 record     radar digest + patch version bump + CHANGELOG entry
    D5 gates      full check suite (scripts/run_all_tests.py) + plugin validate;
                  any failure → the whole run is reverted
    D6 commit     one commit, attributed
    D7 install    refresh the global install (install.py --global → doctor)
    D8 push       gh credentials → plain git → api_push.py (fast-forward only)
    D9 report     automation/logs/daily_<date>.md (+ optional webhook)

Portable: stdlib only, every path derives from this file's location, every
external command is resolved on the running machine. Flags: --dry-run,
--no-push, --no-install, --scan-only, --repo, --budget-usd, --max-turns.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

AUTO_DEFAULT = Path(__file__).resolve().parent
sys.path.insert(0, str(AUTO_DEFAULT))
import pipeline_lock  # noqa: E402
import pipeline_recovery as recovery  # noqa: E402
import radar  # noqa: E402

LEGACY_WEEKLY_LOCK = "weekly.lock"  # an untagged one comes from a weekly clone that predates pipeline_lock
LEGACY_STALE_S = 8 * 3600           # the weekly pipeline itself treats an 8 h old weekly.lock as dead
LOCK_POLL_S = 30.0
IN_PROGRESS = recovery.MARKER       # marker: a run may have dirtied the tree (see pipeline_recovery)
RECOVERABLE = recovery.RECOVERABLE

NO_WINDOW = 0x08000000 if os.name == "nt" else 0
MAX_FILES = 12
MAX_BYTES = 200_000
ALLOW_PREFIXES = ("references/", "skills/", "engine/", "agents/", "assets/")
ALLOW_FILES = {"SKILL.md"}
# the verifier and the blast-radius-critical files: never touched unattended
DENY_PREFIXES = ("hooks/", "scripts/", "evals/", "evolver/tests/", "references/radar/")
DENY_FILES = {"install.py", "phases.json", "CHANGELOG.md", "engine/ss_common.py"}
FOOTNOTE = re.compile(r"(\*Super-Skill )(V\d+(?:\.\d+)*)(:)")
DAILY_MARK = re.compile(r"<!-- daily-self-update -->.*?<!-- /daily-self-update -->", re.S)


class Ctx:
    def __init__(self, repo: Path, args):
        self.repo = repo
        self.auto = repo / "automation"
        self.skill = repo / ".claude" / "skills" / "super-skill"
        self.out = self.auto / "daily_out"
        self.logs = self.auto / "logs"
        self.args = args
        self.date = dt.date.today().isoformat()
        self.report: dict = {"date": self.date, "stages": {}}
        self.marked = False                 # True once the run may have dirtied the tree
        self.baseline: frozenset = frozenset()   # paths already dirty then: never ours to undo
        self.ours: dict = {}                # path → sha1 of what this run wrote (see revert)
        self.created_dirs: list = []        # directories this run created (only these may be pruned)
        self.logs.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.logs / f"daily_{self.date}.log", "a", encoding="utf-8", buffering=1)

    def log(self, msg: str) -> None:
        line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
        try:
            print(line, flush=True)
        except (UnicodeEncodeError, OSError):
            pass
        self._fh.write(line + "\n")

    def stage(self, name: str, ok: bool, note: str = "", **extra) -> bool:
        self.report["stages"][name] = {"ok": ok, "note": note, **extra}
        self.log(f"[{name}] {'OK' if ok else 'FAIL'} {note}")
        return ok


# ---------------------------------------------------------------- subprocess

def sh(args, cwd=None, timeout=600, input_text=None, env=None):
    try:
        p = subprocess.run([str(a) for a in args], cwd=str(cwd) if cwd else None, timeout=timeout,
                           input=input_text.encode("utf-8") if input_text is not None else None,
                           capture_output=True, creationflags=NO_WINDOW,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})})
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        return p.returncode, out + (("\n[stderr] " + err) if err.strip() else "")
    except subprocess.TimeoutExpired:
        return 124, f"[timeout after {timeout}s]"
    except OSError as exc:
        return 127, f"[spawn-fail] {exc}"


def git(ctx: Ctx, *args, timeout=180):
    # literal pathspecs: a file named "x[a].md" must never also match "xa.md"
    return sh(["git", *args], cwd=ctx.repo, timeout=timeout, env={"GIT_LITERAL_PATHSPECS": "1"})


def gh_git(ctx: Ctx, *args, timeout=180):
    """git with gh as the one-shot credential helper (does not touch git config)."""
    if not shutil.which("gh"):
        return 127, "gh not installed"
    return git(ctx, "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
               *args, timeout=timeout)


def find_claude() -> list[str]:
    override = os.environ.get("SUPERSKILL_CLAUDE")
    if override:
        return override.split("|")
    exe = shutil.which("claude")
    if exe:
        return [exe]
    ext = Path.home() / ".vscode" / "extensions"
    cands = sorted(ext.glob("anthropic.claude-code-*/resources/native-binary/claude*")) if ext.is_dir() else []
    if cands:
        return [str(cands[-1])]
    return ["claude"]


# ---------------------------------------------------------------- D0 preflight

def _legacy_weekly_lock_age(ctx: Ctx) -> float | None:
    """Age in seconds of a weekly.lock written by an older weekly clone, else None.

    A current weekly tags its weekly.lock (``"os_lock": true``) and also holds
    the OS-held pipeline lock, which ``pipeline_lock.acquire`` waits for — so a
    tagged file is never waited on here (a killed weekly leaves it behind).
    """
    path = ctx.logs / LEGACY_WEEKLY_LOCK
    try:
        age = time.time() - path.stat().st_mtime
        data = json.loads(path.read_text(encoding="utf-8") or "null")
    except OSError:
        return None
    except ValueError:
        data = None
    if isinstance(data, dict) and data.get("os_lock"):
        return None
    return age


def acquire_lock(ctx: Ctx) -> bool:
    """Wait (≤ --wait-minutes) for any other pipeline, then take the shared OS-held lock."""
    deadline = time.monotonic() + max(0.0, ctx.args.wait_minutes) * 60
    announced = False
    while True:
        age = _legacy_weekly_lock_age(ctx)
        if age is None or age > LEGACY_STALE_S:
            break
        if time.monotonic() >= deadline:
            ctx.log(f"[lock] weekly run still active ({age / 60:.0f} min) — skipping today's run")
            return False
        if not announced:
            ctx.log("[lock] weekly pipeline is running — waiting for it to finish")
            announced = True
        time.sleep(max(0.01, min(LOCK_POLL_S, deadline - time.monotonic())))
    left = max(0.0, deadline - time.monotonic())
    return pipeline_lock.acquire(None, "daily", wait_s=left, poll_s=LOCK_POLL_S, log=ctx.log)


def release_lock(ctx: Ctx) -> None:
    pipeline_lock.release(None, "daily")


def _git_fn(ctx: Ctx):
    return lambda *a: git(ctx, *a)


def _mark_in_progress(ctx: Ctx) -> bool:
    """Write the marker — only on a still-clean scope, so everything dirty later is ours or foreign."""
    g = _git_fn(ctx)
    dirty = recovery.dirty_paths(g)
    if dirty is None or dirty:
        return ctx.stage("D0", False, f"tree changed while the radar ran, refusing to mix: {(dirty or ['?'])[:3]}")
    recovery.mark(ctx.logs, g, "daily", ctx.date)
    ctx.marked = True
    return True


def _clear_marker_if_clean(ctx: Ctx) -> None:
    if not ctx.marked:
        return  # a marker we did not write (refused recovery) stays for the human
    recovery.clear_if_clean(ctx.logs, _git_fn(ctx), ignore=getattr(ctx, "baseline", frozenset()))


def _recover_interrupted_run(ctx: Ctx) -> bool:
    """A run killed mid-way (shutdown, time limit) leaves a marker and maybe a dirty tree.

    Its leftovers are stashed (never discarded) only when they provably belong
    to that run; otherwise the run is refused and the marker kept for a human.
    """
    ok, msg = recovery.recover(ctx.repo, ctx.logs, _git_fn(ctx))
    if not ok:
        return ctx.stage("D0", False, msg)
    if msg:
        ctx.log(f"[D0] {msg}")
        ctx.report["recovered"] = msg
    return True


def preflight(ctx: Ctx) -> bool:
    if (ctx.auto / "PAUSE").exists():
        return ctx.stage("D0", False, "PAUSE file present — skipped", skipped=True)
    rc, out = git(ctx, "rev-parse", "--abbrev-ref", "HEAD")
    branch = out.strip().splitlines()[0] if rc == 0 and out.strip() else "?"
    if branch != ctx.args.branch:
        return ctx.stage("D0", False, f"on branch {branch}, expected {ctx.args.branch}")
    if not _recover_interrupted_run(ctx):
        return False
    rc, out = git(ctx, "status", "--porcelain", "--untracked-files=no")
    if out.strip():
        return ctx.stage("D0", False, f"tracked changes present, refusing to mix: {out.strip().splitlines()[:3]}")
    rc, out = git(ctx, "status", "--porcelain", "--", ".claude/skills/super-skill")
    if out.strip():
        return ctx.stage("D0", False, "untracked files inside the skill dir")
    if not ctx.args.no_push:
        rc, out = gh_git(ctx, "fetch", "origin", ctx.args.branch)
        if rc != 0:
            rc, out = git(ctx, "fetch", "origin", ctx.args.branch)
        if rc == 0:
            rc, out = git(ctx, "merge", "--ff-only", f"origin/{ctx.args.branch}")
            if rc != 0:
                return ctx.stage("D0", False, "local branch diverged from origin — needs a human")
        else:
            ctx.log("[D0] fetch failed (offline?) — continuing on local state")
    return ctx.stage("D0", True, f"branch {branch}, clean")


# ---------------------------------------------------------------- D1 radar

def scan(ctx: Ctx):
    state = radar.load_json(ctx.auto / "radar_state.json", {})
    if not state.get("seen"):
        n = radar.seed_from_dossier(state, ctx.repo / "upgrade-workspace" / "research")
        ctx.log(f"[D1] seeded {n} known repos from the research dossier")
    cfg = radar.load_json(ctx.auto / "radar_config.json", {})
    fetch = getattr(ctx.args, "_fetch", None)
    items, new_state = radar.run(cfg, state, fetch=fetch, log=ctx.log)
    ctx.out.mkdir(parents=True, exist_ok=True)
    radar.save_json(ctx.out / "candidates.json", items)
    (ctx.out / "candidates.md").write_text(radar.to_markdown(items, ctx.date), encoding="utf-8")
    ctx.stage("D1", True, f"{len(items)} candidate(s)", candidates=len(items))
    return items, new_state


# ---------------------------------------------------------------- D2 distill

def current_version(skill: Path) -> str:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    found = FOOTNOTE.findall(text)
    return found[-1][1] if found else "V5.0.0"


def next_version(v: str) -> str:
    parts = v.lstrip("V").split(".")
    while len(parts) < 3:
        parts.append("0")
    parts[-1] = str(int(parts[-1]) + 1)
    return "V" + ".".join(parts)


def parse_result(text: str) -> dict | None:
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text or "", re.S)
    for raw in reversed(blocks):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except ValueError:
            continue
    return None


def parse_claude_output(raw: str) -> tuple[str, dict]:
    """Split `claude -p --output-format json` output into (result text, meta).

    Falls back to treating the whole stdout as text (older CLIs, test doubles).
    """
    stdout = (raw or "").split("\n[stderr] ", 1)[0].strip()
    start = stdout.find("{")
    if start >= 0:
        try:
            data, _ = json.JSONDecoder().raw_decode(stdout[start:])
            if isinstance(data, dict) and "result" in data:
                meta = {k: data.get(k) for k in ("total_cost_usd", "num_turns", "is_error", "subtype")}
                return str(data.get("result") or ""), meta
        except ValueError:
            pass
    return stdout, {}


def revert(ctx: Ctx, reason: str = "failed") -> None:
    """Undo this run's skill/plugin changes; anything not provably ours is stashed, never deleted."""
    if not ctx.marked:
        return  # nothing was written yet
    recovery.revert(ctx.repo, _git_fn(ctx), ctx.log, f"daily revert {ctx.date}: {reason}",
                    ours=ctx.ours, baseline=ctx.baseline, created_dirs=ctx.created_dirs)


def _record_ours(ctx: Ctx) -> None:
    """Fingerprint what the run has written so far (D3 apply + D4 digest/bump)."""
    paths = recovery.scoped_dirty(_git_fn(ctx)) or []
    ctx.ours = recovery.fingerprint(ctx.repo, [p for p in paths if p not in ctx.baseline])


SANDBOX_PREFIX = "ss-distill-"


def _make_sandbox(ctx: Ctx) -> Path | None:
    """Detached worktree of HEAD in the temp dir (stale ones from killed runs are removed first)."""
    rc, out = git(ctx, "worktree", "list", "--porcelain")
    for line in out.splitlines() if rc == 0 else []:
        if line.startswith("worktree ") and Path(line[9:].strip()).name.startswith(SANDBOX_PREFIX):
            _drop_sandbox(ctx, Path(line[9:].strip()))
    git(ctx, "worktree", "prune")
    path = Path(tempfile.mkdtemp(prefix=SANDBOX_PREFIX))
    rc, out = git(ctx, "worktree", "add", "--detach", "-q", str(path), "HEAD", timeout=600)
    if rc != 0:
        ctx.log(f"[D2] worktree add failed: {out.strip()[-160:]}")
        shutil.rmtree(path, ignore_errors=True)
        return None
    (path / "automation" / "daily_out").mkdir(parents=True, exist_ok=True)
    for name in ("candidates.json", "candidates.md"):
        if (ctx.out / name).is_file():
            shutil.copyfile(ctx.out / name, path / "automation" / "daily_out" / name)
    return path


def _drop_sandbox(ctx: Ctx, path: Path) -> None:
    git(ctx, "worktree", "remove", "--force", str(path))
    shutil.rmtree(path, ignore_errors=True)
    git(ctx, "worktree", "prune")


def _copy_staging_back(src: Path, dst: Path) -> int:
    """Copy regular files only — a symlink/junction could point at a secret outside the sandbox."""
    n = 0
    for root, dirs, files in os.walk(src, followlinks=False):
        r = Path(root)
        dirs[:] = [d for d in dirs if not (r / d).is_symlink() and not _is_junction(r / d)]
        for f in files:
            p = r / f
            if p.is_symlink() or not p.is_file() or f in ("candidates.json", "candidates.md"):
                continue
            target = dst / p.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            n += 1
    return n


def _is_junction(p: Path) -> bool:
    try:
        return bool(getattr(os.path, "isjunction", lambda _p: False)(p))
    except OSError:
        return True


def distill(ctx: Ctx, items: list[dict]) -> dict | None:
    for child in ctx.out.iterdir() if ctx.out.is_dir() else []:
        if child.name not in ("candidates.json", "candidates.md"):
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    template = (ctx.auto / "daily_research_prompt.md").read_text(encoding="utf-8")
    radar_index = ctx.skill / "references" / "radar" / "README.md"
    prompt = (template.replace("{{DATE}}", ctx.date)
              .replace("{{VERSION}}", current_version(ctx.skill))
              .replace("{{MAX_FILES}}", str(MAX_FILES))
              .replace("{{CANDIDATES}}", (ctx.out / "candidates.md").read_text(encoding="utf-8"))
              .replace("{{RECENT_RADAR}}", radar_index.read_text(encoding="utf-8")[-3000:]
                       if radar_index.is_file() else "(first run)"))
    (ctx.logs / f"daily_{ctx.date}_prompt.md").write_text(prompt, encoding="utf-8")
    # read-only GitHub access only: `gh api` could write to every repo the token can reach
    tools = "Read,Grep,Glob,WebFetch,WebSearch,Write,Edit,Bash(gh search:*),Bash(gh repo view:*)"
    argv = find_claude() + ["-p", "--permission-mode", "acceptEdits", "--output-format", "json",
                            "--max-turns", str(ctx.args.max_turns),
                            "--max-budget-usd", str(ctx.args.budget_usd), "--allowedTools", tools]
    # The model works in a throwaway worktree of HEAD, never in the live tree: whatever it writes
    # there (pipeline scripts, git-ignored tests, settings, a human's files) is discarded; only
    # regular files under automation/daily_out/ are copied back, and D3 whitelists those.
    sandbox = _make_sandbox(ctx)
    if sandbox is None:
        ctx.stage("D2", False, "could not create the distill sandbox (git worktree)")
        return None
    try:
        ctx.log(f"[D2] headless distill in sandbox (budget ${ctx.args.budget_usd}, ≤{ctx.args.max_turns} turns)")
        rc, raw = sh(argv, cwd=sandbox, timeout=ctx.args.timeout, input_text=prompt)
        copied = _copy_staging_back(sandbox / "automation" / "daily_out", ctx.out)
    finally:
        _drop_sandbox(ctx, sandbox)
    ctx.log(f"[D2] {copied} staged file(s) copied back from the sandbox")
    out, meta = parse_claude_output(raw)
    (ctx.logs / f"daily_{ctx.date}_output.md").write_text(out or raw or "", encoding="utf-8")
    cost = meta.get("total_cost_usd")
    ctx.report["cost_usd"] = cost
    if cost is not None:
        ctx.log(f"[D2] model cost ${cost:.2f}, {meta.get('num_turns')} turns")
    result = parse_result(out)
    if rc != 0 or result is None:
        ctx.stage("D2", False, f"claude rc={rc}, result JSON {'missing' if result is None else 'ok'}")
        return None
    spent = f" (${cost:.2f}, {meta.get('num_turns')} turns)" if cost is not None else ""
    ctx.stage("D2", True, str(result.get("summary", ""))[:160] + spent,
              adopted=len(result.get("adopted") or []), rejected=len(result.get("rejected") or []))
    return result


# ---------------------------------------------------------------- D3 apply

def _case_exact(root: Path, parts: list[str]) -> bool:
    """False when a component differs only in case from an existing entry (same file on NTFS)."""
    cur = root
    for part in parts:
        if not cur.is_dir():
            return True
        try:
            names = os.listdir(cur)
        except OSError:
            return False
        if part not in names and any(n.casefold() == part.casefold() for n in names):
            return False
        cur = cur / part
    return True


def validate_entry(skill: Path, out: Path, entry: dict) -> tuple[bool, str]:
    rel = str(entry.get("path", "")).replace("\\", "/").lstrip("/")
    parts = rel.split("/")
    # NTFS/APFS ignore case and trailing dots/spaces: "engine/SS_COMMON.py." IS engine/ss_common.py
    if not rel or ":" in rel or any(p in ("", ".", "..") or p != p.rstrip(". ") for p in parts):
        return False, f"bad path {rel!r}"
    key = rel.casefold()
    if key in {f.casefold() for f in DENY_FILES} or key.startswith(tuple(p.casefold() for p in DENY_PREFIXES)):
        return False, f"protected path {rel} (verifier / blast radius)"
    if not (key in {f.casefold() for f in ALLOW_FILES} or key.startswith(tuple(p.casefold() for p in ALLOW_PREFIXES))):
        return False, f"outside whitelist {rel}"
    if not _case_exact(skill, parts):
        return False, f"case variant of an existing path {rel}"
    src = out / rel
    if not src.is_file():
        return False, f"staged file missing {rel}"
    if src.stat().st_size > MAX_BYTES:
        return False, f"too large {rel}"
    dst = skill / rel
    if "/tests/" in f"/{key}" and dst.exists():
        return False, f"existing test {rel} may not be modified (add new tests instead)"
    if rel == "SKILL.md":
        text = src.read_text(encoding="utf-8", errors="replace")
        if text.count("\n") + 1 >= 500:
            return False, "SKILL.md would reach 500 lines"
        if not FOOTNOTE.search(text):
            return False, "SKILL.md lost its version footnote"
    return True, rel


def _mkdirs(ctx: Ctx, d: Path) -> None:
    missing = [p for p in [d, *d.parents] if not p.exists()]
    d.mkdir(parents=True, exist_ok=True)
    ctx.created_dirs.extend(missing)          # deepest first


def apply(ctx: Ctx) -> list[dict]:
    manifest = radar.load_json(ctx.out / "manifest.json", [])
    if not isinstance(manifest, list):
        ctx.stage("D3", False, "manifest.json is not a list")
        return []
    applied = []
    for entry in manifest[:MAX_FILES]:
        ok, why = validate_entry(ctx.skill, ctx.out, entry if isinstance(entry, dict) else {})
        if not ok:
            ctx.log(f"[D3] REJECT {why}")
            continue
        dst = ctx.skill / why
        _mkdirs(ctx, dst.parent)
        shutil.copy2(ctx.out / why, dst)
        applied.append({**entry, "path": why})
        ctx.log(f"[D3] APPLY {entry.get('action', 'update')} {why} — {str(entry.get('summary', ''))[:80]}")
    if len(manifest) > MAX_FILES:
        ctx.log(f"[D3] manifest truncated to {MAX_FILES} entries")
    ctx.stage("D3", True, f"{len(applied)} file(s) applied", files=[a["path"] for a in applied])
    return applied


# ---------------------------------------------------------------- D4 record

def write_digest(ctx: Ctx, items: list[dict], result: dict, applied: list[dict], version: str) -> str:
    rdir = ctx.skill / "references" / "radar"
    _mkdirs(ctx, rdir)
    lines = [f"# Radar {ctx.date} — {version}", "", f"**Summary:** {result.get('summary', '—')}", "",
             "## Adopted"]
    for a in result.get("adopted") or []:
        lines.append(f"- **{a.get('source', '?')}** — {a.get('idea', '')} → `{', '.join(a.get('files', []))}`"
                     f" ({a.get('license', 'licence n/a')}, {a.get('mode', 'pattern')})")
    if not result.get("adopted"):
        lines.append("- (nothing adopted)")
    lines += ["", "## Reviewed, not adopted"]
    for r in result.get("rejected") or []:
        lines.append(f"- {r.get('source', '?')}: {r.get('reason', '')}")
    lines += ["", "## Files changed"] + [f"- `{a['path']}` — {a.get('summary', '')}" for a in applied]
    lines += ["", radar.to_markdown(items, ctx.date).replace("# Radar candidates", "## Candidates", 1)]
    name, n = f"{ctx.date}.md", 2
    while (rdir / name).exists():  # several runs on one day must never overwrite a digest
        name, n = f"{ctx.date}-{n}.md", n + 1
    (rdir / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    index = rdir / "README.md"
    head = "# Radar log\n\nDaily self-update digests (newest first). Generated by `automation/superskill_daily.py`.\n\n"
    old = index.read_text(encoding="utf-8") if index.is_file() else ""
    body = old[len(head):] if old.startswith(head) else ""
    entry = f"- [{ctx.date}]({name}) {version} — {str(result.get('summary', ''))[:140]}\n"
    index.write_text(head + entry + body, encoding="utf-8")
    return f"references/radar/{name}"


def bump_version(ctx: Ctx, version: str, digest_rel: str, summary: str) -> None:
    sk = ctx.skill / "SKILL.md"
    text = sk.read_text(encoding="utf-8")
    matches = list(FOOTNOTE.finditer(text))
    if matches:
        m = matches[-1]
        text = text[:m.start(2)] + version + text[m.end(2):]
    block = (f"<!-- daily-self-update -->\n**Latest daily self-update:** {version} — {ctx.date} — "
             f"{summary[:180]} — [digest]({digest_rel}) · [all](references/radar/README.md)\n"
             f"<!-- /daily-self-update -->")
    if DAILY_MARK.search(text):
        text = DAILY_MARK.sub(lambda _m: block, text)
    sk.write_text(text, encoding="utf-8")
    pj = ctx.repo / ".claude-plugin" / "plugin.json"
    if pj.is_file():
        data = json.loads(pj.read_text(encoding="utf-8"))
        data["version"] = version.lstrip("V")
        pj.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cl = ctx.skill / "CHANGELOG.md"
    entry = (f"## [{version.lstrip('V')}] - {ctx.date}\n\n### Daily self-update (radar)\n- {summary}\n"
             f"- Digest: [{digest_rel}]({digest_rel})\n\n")
    if cl.is_file():
        old = cl.read_text(encoding="utf-8")
        idx = old.find("\n## [")
        new = old[:idx + 1] + entry + old[idx + 1:] if idx >= 0 else old + "\n" + entry
        cl.write_text(new, encoding="utf-8")


# ---------------------------------------------------------------- D5 gates

def gates(ctx: Ctx) -> bool:
    custom = os.environ.get("SUPERSKILL_GATE_CMD")
    argv = custom.split("|") if custom else [sys.executable, str(ctx.skill / "scripts" / "run_all_tests.py")]
    rc, out = sh(argv, cwd=ctx.skill, timeout=3600)
    (ctx.logs / f"daily_{ctx.date}_gates.log").write_text(out, encoding="utf-8")
    tail = " | ".join([l for l in out.strip().splitlines() if l.strip()][-2:])
    if rc != 0:
        return ctx.stage("D5", False, f"check suite failed: {tail[:200]}")
    claude = find_claude()
    if not custom and (shutil.which(claude[0]) or Path(claude[0]).exists()):
        rc, out = sh(claude + ["plugin", "validate", str(ctx.skill)], cwd=ctx.repo, timeout=300)
        if rc != 0 and "Validation failed" in out:
            return ctx.stage("D5", False, f"plugin validate failed: {out.strip().splitlines()[-1:]}")
    return ctx.stage("D5", True, tail[:200])


# ---------------------------------------------------------------- D6–D8

def commit(ctx: Ctx, version: str, summary: str, applied: list[dict]) -> bool:
    dirty = recovery.scoped_dirty(_git_fn(ctx))
    foreign = None if dirty is None else [
        p for p in dirty if ctx.ours.get(p) is None or recovery.file_hash(ctx.repo / p) != ctx.ours[p]]
    if foreign is None or foreign:
        return ctx.stage("D6", False, f"files changed by someone else during the run, not committing: "
                                      f"{(foreign or ['git status failed'])[:3]}")
    paths = sorted(ctx.ours)
    if not paths:
        return ctx.stage("D6", True, "nothing to commit")
    git(ctx, "add", "--", *paths)
    rc, _ = git(ctx, "diff", "--cached", "--quiet")
    if rc == 0:
        return ctx.stage("D6", True, "nothing to commit")
    msg = (f"chore(self-update): {version} 每日自更新 {ctx.date} — {summary[:72]}\n\n"
           + "".join(f"- {a['path']}: {str(a.get('summary', ''))[:100]}\n" for a in applied)
           + "\nAutomated by automation/superskill_daily.py (radar → distill → gates → push).\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n")
    rc, out = sh(["git", "commit", "-q", "-F", "-", "--", *paths], cwd=ctx.repo, input_text=msg,
                 env={"GIT_LITERAL_PATHSPECS": "1"})
    return ctx.stage("D6", rc == 0, out.strip()[-160:] or "committed")


def install(ctx: Ctx) -> bool:
    if ctx.args.no_install:
        return ctx.stage("D7", True, "skipped (--no-install)")
    rc, out = sh([sys.executable, str(ctx.skill / "install.py"), "--global"], cwd=ctx.repo, timeout=900)
    ok = rc == 0 and "doctor: all good" in out
    return ctx.stage("D7", ok, "global install refreshed, doctor all good" if ok else out.strip()[-200:])


def push(ctx: Ctx) -> bool:
    if ctx.args.no_push:
        return ctx.stage("D8", True, "skipped (--no-push)")
    layers = os.environ.get("SUPERSKILL_PUSH_LAYERS", "gh,git,api").split(",")
    for layer in layers:
        if layer == "gh":
            rc, out = gh_git(ctx, "push", "origin", ctx.args.branch, timeout=300)
        elif layer == "git":
            rc, out = git(ctx, "push", "origin", ctx.args.branch, timeout=300)
        elif layer == "api" and (ctx.auto / "api_push.py").is_file():
            rc, out = sh([sys.executable, str(ctx.auto / "api_push.py")], cwd=ctx.repo, timeout=600)
        else:
            continue
        if rc == 0:
            return ctx.stage("D8", True, f"pushed via {layer}")
        ctx.log(f"[D8] {layer} failed: {out.strip()[-160:]}")
    return ctx.stage("D8", False, "all push layers failed — commit kept locally")


def notify(ctx: Ctx) -> None:
    lines = [f"# Super-Skill daily self-update — {ctx.date}", ""]
    for name, s in ctx.report["stages"].items():
        lines.append(f"- {'✅' if s['ok'] else '❌'} {name}: {s['note']}")
    text = "\n".join(lines) + "\n"
    (ctx.logs / f"daily_{ctx.date}.md").write_text(text, encoding="utf-8")
    url = os.environ.get("SUPERSKILL_NOTIFY_WEBHOOK")
    if not url:
        return
    body = ({"msgtype": "markdown", "markdown": {"content": text}} if "qyapi.weixin" in url
            else {"text": text})
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15).read()  # noqa: S310 - user-configured webhook
    except Exception as exc:  # noqa: BLE001 - notification is best-effort
        ctx.log(f"[D9] webhook failed: {exc}")


# ---------------------------------------------------------------- main

def run(args) -> int:
    repo = Path(args.repo).resolve() if args.repo else AUTO_DEFAULT.parent
    ctx = Ctx(repo, args)
    if not acquire_lock(ctx):
        return 0
    try:
        if not preflight(ctx):
            notify(ctx)
            return 0 if ctx.report["stages"]["D0"].get("skipped") else 1
        items, new_state = scan(ctx)
        state_file = ctx.auto / "radar_state.json"
        if not items or args.scan_only:
            if not args.dry_run:
                radar.save_json(state_file, new_state)
            notify(ctx)
            return 0
        if not _mark_in_progress(ctx):  # from here on the tree may be dirty until commit/revert
            notify(ctx)
            return 1
        result = distill(ctx, items)
        if result is None:
            revert(ctx, "distill failed")
            notify(ctx)
            return 1
        if args.dry_run:
            ctx.log("[dry-run] stopping before apply; staged output left in automation/daily_out/")
            notify(ctx)
            return 0
        applied = apply(ctx)
        _record_ours(ctx)                       # D3 output is ours from the start (refreshed after D4)
        radar.save_json(state_file, new_state)  # candidates were reviewed, whatever the outcome
        if not applied and not result.get("adopted"):
            ctx.stage("D4", True, "nothing worth adopting today — no commit")
            notify(ctx)
            return 0
        version = next_version(current_version(ctx.skill))
        summary = str(result.get("summary") or "daily radar").strip().replace("\n", " ")
        digest = write_digest(ctx, items, result, applied, version)
        bump_version(ctx, version, digest, summary)
        _record_ours(ctx)
        ctx.stage("D4", True, f"{version}, digest {digest}")
        if not gates(ctx):
            revert(ctx, "gates failed")
            ctx.log("[D5] reverted the whole run")
            notify(ctx)
            return 1
        if not commit(ctx, version, summary, applied):
            if ctx.ours:
                git(ctx, "reset", "-q", "--", *ctx.ours)   # unstage before reverting
            revert(ctx, "commit failed")
            notify(ctx)
            return 1
        install(ctx)
        ok = push(ctx)
        notify(ctx)
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001 - last resort: never leave a half-applied tree
        ctx.log(f"[fatal] {exc.__class__.__name__}: {exc}")
        revert(ctx, f"{exc.__class__.__name__}")
        notify(ctx)
        return 1
    finally:
        try:
            _clear_marker_if_clean(ctx)
        finally:
            release_lock(ctx)


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Super-Skill daily self-update")
    ap.add_argument("--repo", help="repository root (default: parent of automation/)")
    ap.add_argument("--branch", default="master")
    ap.add_argument("--dry-run", action="store_true", help="scan + distill only; no apply/commit/push/state")
    ap.add_argument("--scan-only", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--budget-usd", type=float, default=float(os.environ.get("SUPERSKILL_DAILY_BUDGET", "3")))
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--wait-minutes", type=float,
                    default=float(os.environ.get("SUPERSKILL_LOCK_WAIT_MIN", "150")),
                    help="how long to wait for a running weekly/daily pipeline before skipping")
    args = ap.parse_args(argv)
    pipeline_lock.tie_children_to_this_process()   # a killed run must not leave claude/git running
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
