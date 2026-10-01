#!/usr/bin/env python3
"""Super-Skill daily self-update (default 23:00 Beijing time, see schedule_daily.py).

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
import time
import urllib.request
from pathlib import Path

AUTO_DEFAULT = Path(__file__).resolve().parent
sys.path.insert(0, str(AUTO_DEFAULT))
import radar  # noqa: E402

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
    return sh(["git", *args], cwd=ctx.repo, timeout=timeout)


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

def acquire_lock(ctx: Ctx) -> bool:
    for name in ("selfupdate.lock", "weekly.lock"):
        f = ctx.logs / name
        if f.exists() and (time.time() - f.stat().st_mtime) < 6 * 3600:
            ctx.log(f"[lock] {name} held ({(time.time() - f.stat().st_mtime) / 60:.0f} min old) — skip")
            return False
    (ctx.logs / "selfupdate.lock").write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock(ctx: Ctx) -> None:
    try:
        (ctx.logs / "selfupdate.lock").unlink()
    except OSError:
        pass


def preflight(ctx: Ctx) -> bool:
    if (ctx.auto / "PAUSE").exists():
        return ctx.stage("D0", False, "PAUSE file present — skipped", skipped=True)
    rc, out = git(ctx, "rev-parse", "--abbrev-ref", "HEAD")
    branch = out.strip().splitlines()[0] if rc == 0 and out.strip() else "?"
    if branch != ctx.args.branch:
        return ctx.stage("D0", False, f"on branch {branch}, expected {ctx.args.branch}")
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


def revert(ctx: Ctx) -> None:
    git(ctx, "checkout", "--", ".")
    git(ctx, "clean", "-fdq", "--", ".claude/skills/super-skill", ".claude-plugin")


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
    tools = ("Read,Grep,Glob,WebFetch,WebSearch,Write,Edit,"
             "Bash(gh api:*),Bash(gh search:*),Bash(gh repo view:*)")
    argv = find_claude() + ["-p", "--permission-mode", "acceptEdits", "--output-format", "json",
                            "--max-turns", str(ctx.args.max_turns),
                            "--max-budget-usd", str(ctx.args.budget_usd), "--allowedTools", tools]
    ctx.log(f"[D2] headless distill (budget ${ctx.args.budget_usd}, ≤{ctx.args.max_turns} turns)")
    rc, raw = sh(argv, cwd=ctx.repo, timeout=ctx.args.timeout, input_text=prompt)
    out, meta = parse_claude_output(raw)
    (ctx.logs / f"daily_{ctx.date}_output.md").write_text(out or raw or "", encoding="utf-8")
    cost = meta.get("total_cost_usd")
    ctx.report["cost_usd"] = cost
    if cost is not None:
        ctx.log(f"[D2] model cost ${cost:.2f}, {meta.get('num_turns')} turns")
    # anything the model wrote outside the staging dir is discarded
    rc2, dirty = git(ctx, "status", "--porcelain", "--", ".claude", ".claude-plugin")
    if dirty.strip():
        ctx.log(f"[D2] model touched the repo directly — reverting: {dirty.strip().splitlines()[:3]}")
        revert(ctx)
    result = parse_result(out)
    if rc != 0 or result is None:
        ctx.stage("D2", False, f"claude rc={rc}, result JSON {'missing' if result is None else 'ok'}")
        return None
    spent = f" (${cost:.2f}, {meta.get('num_turns')} turns)" if cost is not None else ""
    ctx.stage("D2", True, str(result.get("summary", ""))[:160] + spent,
              adopted=len(result.get("adopted") or []), rejected=len(result.get("rejected") or []))
    return result


# ---------------------------------------------------------------- D3 apply

def validate_entry(skill: Path, out: Path, entry: dict) -> tuple[bool, str]:
    rel = str(entry.get("path", "")).replace("\\", "/").lstrip("/")
    parts = rel.split("/")
    if not rel or ".." in parts or ":" in rel:
        return False, f"bad path {rel!r}"
    if rel in DENY_FILES or rel.startswith(DENY_PREFIXES):
        return False, f"protected path {rel} (verifier / blast radius)"
    if not (rel in ALLOW_FILES or rel.startswith(ALLOW_PREFIXES)):
        return False, f"outside whitelist {rel}"
    src = out / rel
    if not src.is_file():
        return False, f"staged file missing {rel}"
    if src.stat().st_size > MAX_BYTES:
        return False, f"too large {rel}"
    dst = skill / rel
    if "/tests/" in f"/{rel}" and dst.exists():
        return False, f"existing test {rel} may not be modified (add new tests instead)"
    if rel == "SKILL.md":
        text = src.read_text(encoding="utf-8", errors="replace")
        if text.count("\n") + 1 >= 500:
            return False, "SKILL.md would reach 500 lines"
        if not FOOTNOTE.search(text):
            return False, "SKILL.md lost its version footnote"
    return True, rel


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
        dst.parent.mkdir(parents=True, exist_ok=True)
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
    rdir.mkdir(parents=True, exist_ok=True)
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
    name = f"{ctx.date}.md"
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
    git(ctx, "add", "--", ".claude/skills/super-skill", ".claude-plugin/plugin.json")
    rc, _ = git(ctx, "diff", "--cached", "--quiet")
    if rc == 0:
        return ctx.stage("D6", True, "nothing to commit")
    msg = (f"chore(self-update): {version} 每日自更新 {ctx.date} — {summary[:72]}\n\n"
           + "".join(f"- {a['path']}: {str(a.get('summary', ''))[:100]}\n" for a in applied)
           + "\nAutomated by automation/superskill_daily.py (radar → distill → gates → push).\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n")
    rc, out = sh(["git", "commit", "-q", "-F", "-"], cwd=ctx.repo, input_text=msg)
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
        result = distill(ctx, items)
        if result is None:
            revert(ctx)
            notify(ctx)
            return 1
        if args.dry_run:
            ctx.log("[dry-run] stopping before apply; staged output left in automation/daily_out/")
            notify(ctx)
            return 0
        applied = apply(ctx)
        radar.save_json(state_file, new_state)  # candidates were reviewed, whatever the outcome
        if not applied and not result.get("adopted"):
            ctx.stage("D4", True, "nothing worth adopting today — no commit")
            notify(ctx)
            return 0
        version = next_version(current_version(ctx.skill))
        summary = str(result.get("summary") or "daily radar").strip().replace("\n", " ")
        digest = write_digest(ctx, items, result, applied, version)
        bump_version(ctx, version, digest, summary)
        ctx.stage("D4", True, f"{version}, digest {digest}")
        if not gates(ctx):
            revert(ctx)
            ctx.log("[D5] reverted the whole run")
            notify(ctx)
            return 1
        if not commit(ctx, version, summary, applied):
            revert(ctx)
            notify(ctx)
            return 1
        install(ctx)
        ok = push(ctx)
        notify(ctx)
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001 - last resort: never leave a half-applied tree
        ctx.log(f"[fatal] {exc.__class__.__name__}: {exc}")
        revert(ctx)
        notify(ctx)
        return 1
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
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
