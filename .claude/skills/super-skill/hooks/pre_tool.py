#!/usr/bin/env python3
"""PreToolUse guard (W1): the rules that must hold no matter what the model
decides live here, not in prose.

deny  — destructive shell (rm -rf / ~ *, Remove-Item -Recurse -Force on roots,
        disk formatting), force-push, reading/writing secrets (.env, SSH keys,
        *.pem, *.secret.*), direct writes to engine state (state.json,
        ledger.jsonl) and — when a hard budget is exhausted — any new work;
        playbook do-not-repeat rules marked ``block``.
ask   — human decisions (`ss.py approve|reject`), pushes to main/master,
        `curl … | sh` style remote execution.

Pattern sources: trailofbits/claude-code-config deny baseline and
disler/hooks-mastery guard scripts (patterns only, no license); decision JSON
per the official hooks docs.
"""
from __future__ import annotations

import re
import shlex

import _hooklib as H

_SECRET_PATH = re.compile(
    r"(?i)(^|[\\/])(\.env(\.[\w-]+)?|id_(rsa|ed25519|ecdsa|dsa)(\.pub)?|\.netrc|\.pgpass|"
    r"credentials(\.json)?|[\w.-]*\.secret(\.[\w]+)?|[\w.-]*\.pem|[\w.-]*\.p12|[\w.-]*\.pfx)$|"
    r"(^|[\\/])\.ssh([\\/]|$)|(^|[\\/])\.aws[\\/]credentials$")
_SECRET_OK = re.compile(r"(?i)\.env\.(example|sample|template|dist|defaults?)$|\.pub$")
_STATE_FILES = re.compile(r"(?i)[\\/]?\.super-skill[\\/](state\.json|ledger\.jsonl)$")
# compared against lower-cased tokens, so keep every entry lower-case
_DANGER_TARGETS = {"/", "/*", "~", "~/", "~/*", "$home", "${home}", "$home/", "*", ".", "./",
                   "..", "../", "c:\\", "c:/", "c:", "%userprofile%", "$env:userprofile"}
_READ_CMDS = re.compile(r"(?i)\b(cat|type|less|more|head|tail|get-content|gc|bat|strings|xxd|od)\b")
_REMOTE_EXEC = re.compile(r"(?i)\b(curl|wget|iwr|invoke-webrequest)\b[^|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b|"
                          r"\biex\b.*\b(iwr|invoke-webrequest|downloadstring)\b")
_FORMAT = re.compile(r"(?i)\bmkfs(\.\w+)?\b|\bformat(-volume)?\s+[a-z]:|\bdd\b[^|;]*\bof=/dev/(sd|nvme|disk)")
_APPROVE = re.compile(r"ss\.py[\"']?\s+(?:--root\s+\S+\s+)?(approve|reject)\b")
_PUSH = re.compile(r"\bgit\b[^;&|]*\bpush\b(?P<rest>[^;&|]*)")


def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": f"Super-Skill guard: {reason}"}}


def _ask(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                   "permissionDecisionReason": f"Super-Skill guard: {reason}"}}


def _is_secret(path: str) -> bool:
    p = path.strip().strip("\"'")
    return bool(p) and bool(_SECRET_PATH.search(p)) and not _SECRET_OK.search(p)


def _tokens(cmd: str) -> list[str]:
    try:
        return shlex.split(cmd, posix=True)
    except ValueError:
        return cmd.split()


def check_shell(cmd: str) -> dict | None:
    low = cmd.lower()
    if _APPROVE.search(cmd):
        return _ask("approve/reject is a human decision — confirm only if YOU (the user) approve")
    toks = _tokens(cmd)
    for i, tok in enumerate(toks):
        t = tok.lower()
        if t == "rm":
            flags = "".join(x.lstrip("-") for x in toks[i + 1:i + 4] if x.startswith("-"))
            targets = [x.lower().rstrip() for x in toks[i + 1:] if not x.startswith("-")]
            if "r" in flags.lower() and any(x in _DANGER_TARGETS for x in targets):
                return _deny(f"refusing recursive delete of a root/home/wildcard target: {cmd[:120]}")
        if t in ("remove-item", "rd", "rmdir", "del") and ("-recurse" in low or "/s" in low):
            targets = [x.lower() for x in toks[i + 1:] if not x.startswith(("-", "/"))]
            if any(x in _DANGER_TARGETS for x in targets):
                return _deny(f"refusing recursive delete of a root/home target: {cmd[:120]}")
    if _FORMAT.search(cmd):
        return _deny("disk formatting / raw device writes are blocked")
    for m in _PUSH.finditer(cmd):
        rest = m.group("rest")
        if re.search(r"(^|\s)(-f|--force)(\s|$)", rest) and "--force-with-lease" not in rest:
            return _deny("force-push is blocked (use --force-with-lease on a feature branch)")
        if re.search(r"(^|[\s:+])(main|master)(\s|$)", rest):
            return _ask("push to main/master — confirm this is intended")
    if _READ_CMDS.search(cmd) and any(_is_secret(t) for t in toks):
        return _deny("reading secret files (.env / keys / credentials) is blocked")
    if _STATE_FILES.search(cmd.replace("'", "").replace('"', "")) and re.search(r">|\bsed\b.*-i|set-content|out-file|\btee\b", low):
        return _deny("engine state is written only via ss.py (state.json / ledger.jsonl)")
    if _REMOTE_EXEC.search(cmd):
        return _ask("piping a download into a shell — confirm the source is trusted")
    return None


def check_file(tool: str, ti: dict, root) -> dict | None:
    path = str(ti.get("file_path") or ti.get("notebook_path") or "")
    if _is_secret(path):
        return _deny(f"{tool} of secret file {path} is blocked (keep secrets out of the agent's context)")
    if tool in H.EDIT_TOOLS and _STATE_FILES.search(path.replace("\\", "/")):
        return _deny("state.json / ledger.jsonl are written only via ss.py (use `ss.py advance|goto|config`)")
    if tool in H.EDIT_TOOLS:
        new_text = ti.get("content") or ti.get("new_string") or ti.get("new_source") or ""
        if not new_text and isinstance(ti.get("edits"), list):
            new_text = "\n".join(str(e.get("new_string", "")) for e in ti["edits"] if isinstance(e, dict))
        if new_text:
            try:
                import playbook
                hits = [h for h in playbook.check_text(root, new_text) if h.get("block")]
            except Exception:
                hits = []
            if hits:
                h = hits[0]
                return _deny(f"do-not-repeat rule {h.get('id')}: {h.get('text')}")
    return None


def check_budget(payload: dict, root) -> dict | None:
    st = H.load_state(root)
    budget = st.get("budget") or {}
    if not (budget.get("usd_limit") or budget.get("token_limit")) or not budget.get("hard_stop", True):
        return None
    tp = payload.get("transcript_path")
    if not tp:
        return None
    try:
        import cost_meter
        b = cost_meter.budget_status(root, tp)
    except Exception:
        return None
    if b.get("level") == "exceeded":
        return _deny(f"budget exhausted ({b.get('ratio', 0):.0%} of limit). Stop new work, write a "
                     "hand-off (`ss.py handoff`) and ask the user to raise `budget.usd_limit`.")
    return None


def handle(payload: dict, root):
    tool = payload.get("tool_name") or ""
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return None
    if tool in H.SHELL_TOOLS:
        verdict = check_shell(str(ti.get("command", "")))
    elif tool in H.EDIT_TOOLS or tool == "Read":
        verdict = check_file(tool, ti, root)
    else:
        verdict = None
    if verdict is None and tool in (H.EDIT_TOOLS | H.SHELL_TOOLS):
        verdict = check_budget(payload, root)
    if verdict:
        rec = H.event_record(payload, root, ok=None)
        rec["ev"] = "GuardDecision"
        rec["decision"] = verdict["hookSpecificOutput"]["permissionDecision"]
        rec["reason"] = verdict["hookSpecificOutput"]["permissionDecisionReason"][:200]
        H.log_event(root, rec)
    return verdict


if __name__ == "__main__":
    H.run(handle)
