"""W9 budget & observability for Super-Skill V5.

Stdlib only. Three concerns live here:

1. **Session usage** -- parse Claude Code transcript JSONL (the ccusage
   approach): every ``type == "assistant"`` line carries ``message.id``,
   ``message.model``, ``message.usage`` and a top-level ``requestId``. Claude
   Code writes one line per content block, so the same API response appears
   several times with identical usage; entries are deduplicated by
   ``(message.id, requestId)``. Subagent transcripts stored next to the main
   one (``<session-id>/subagents/*.jsonl``) are included.
2. **Budget** -- compare spend against ``state["budget"]``.
3. **Phase report** -- join ledger.jsonl and events.jsonl per phase.

Honesty rule: every USD figure is an *estimate* (list prices, no discounts,
no plan subscriptions) and is labelled as such in all outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import (  # noqa: E402
    force_utf8_stdio,
    ledger,
    load_state,
    now_iso,
    read_json,
    read_jsonl,
    sdir,
    write_json_atomic,
)

CACHE_FILE = "cost_cache.json"
PRICING_FILE = "pricing.json"
REPORT_FILE = "REPORT.md"
CACHE_VERSION = 1

# USD per million tokens, matched by substring of the model id (longest key
# wins). cache_write / cache_read default to 1.25x / 0.1x the input rate.
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "opus": {"input": 5.0, "output": 25.0},
    "sonnet": {"input": 3.0, "output": 15.0},
    "haiku": {"input": 1.0, "output": 5.0},
}
FALLBACK_FAMILY = "sonnet"
CACHE_WRITE_MULT = 1.25
CACHE_READ_MULT = 0.1
DEFAULT_WARN_RATIO = 0.7

TOKEN_KEYS = ("input", "output", "cache_write", "cache_read")


# ---------------------------------------------------------------- pricing

def load_pricing(root: Optional[Path] = None) -> dict[str, dict[str, float]]:
    """Default table, overlaid per family by ``.super-skill/pricing.json``."""
    table = {k: dict(v) for k, v in DEFAULT_PRICING.items()}
    if root is not None:
        override = read_json(sdir(root) / PRICING_FILE, default=None)
        if isinstance(override, dict):
            for family, rates in override.items():
                if isinstance(rates, dict):
                    fam = str(family).lower()
                    merged = dict(table.get(fam, {}))
                    merged.update({k: float(v) for k, v in rates.items()
                                   if isinstance(v, (int, float)) and not isinstance(v, bool)})
                    table[fam] = merged
    return table


def rates_for(model: str, pricing: dict[str, dict[str, float]]) -> dict[str, float]:
    """Resolve per-token-kind rates (USD / MTok) for a model id."""
    name = (model or "").lower()
    base: Optional[dict[str, float]] = None
    # longest family key first so e.g. "sonnet-4" beats "sonnet"
    for family in sorted(pricing, key=len, reverse=True):
        if family and family in name:
            base = pricing[family]
            break
    if base is None:
        base = pricing.get(FALLBACK_FAMILY) or DEFAULT_PRICING[FALLBACK_FAMILY]
    inp = float(base.get("input", DEFAULT_PRICING[FALLBACK_FAMILY]["input"]))
    return {
        "input": inp,
        "output": float(base.get("output", inp * 5)),
        "cache_write": float(base.get("cache_write", inp * CACHE_WRITE_MULT)),
        "cache_read": float(base.get("cache_read", inp * CACHE_READ_MULT)),
    }


def price_tokens(tokens: dict[str, int], rates: dict[str, float]) -> float:
    return sum(tokens.get(k, 0) * rates[k] for k in TOKEN_KEYS) / 1_000_000


# ---------------------------------------------------------------- transcripts

def transcript_files(transcript_path: str | Path) -> list[Path]:
    """Main transcript plus subagent transcripts stored beside it.

    Observed layout (Claude Code, 2026)::

        projects/<slug>/<session-id>.jsonl
        projects/<slug>/<session-id>/subagents/agent-<id>.jsonl (+ .meta.json)
    """
    main = Path(transcript_path)
    files = [main] if main.is_file() else []
    sub_dir = main.with_suffix("") / "subagents"
    if sub_dir.is_dir():
        files.extend(sorted(p for p in sub_dir.glob("*.jsonl") if p.is_file()))
    return files


def _num(v: Any) -> int:
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def _usage_tokens(usage: dict) -> dict[str, int]:
    cache_write = _num(usage.get("cache_creation_input_tokens"))
    if not cache_write and isinstance(usage.get("cache_creation"), dict):
        # newer transcripts also split cache writes by TTL (ephemeral_5m / _1h)
        cache_write = sum(_num(v) for v in usage["cache_creation"].values())
    return {
        "input": _num(usage.get("input_tokens")),
        "output": _num(usage.get("output_tokens")),
        "cache_write": cache_write,
        "cache_read": _num(usage.get("cache_read_input_tokens")),
    }


def _entries(files: list[Path]) -> list[dict]:
    """Deduplicated usage entries across all files.

    On a duplicate key the entry with the larger token total wins (same rule
    as ccusage: streaming can log a partial usage before the final one).
    Lines without ``message.id`` cannot be deduplicated and are kept as-is.
    """
    keyed: dict[tuple, dict] = {}
    loose: list[dict] = []
    for f in files:
        for rec in read_jsonl(f):
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message")
            if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                continue
            tokens = _usage_tokens(msg["usage"])
            cost = rec.get("costUSD")
            entry = {
                "model": str(msg.get("model") or "unknown"),
                "tokens": tokens,
                "total": sum(tokens.values()),
                "cost_usd": float(cost) if isinstance(cost, (int, float))
                and not isinstance(cost, bool) else None,
                "ts": rec.get("timestamp"),
            }
            mid = msg.get("id")
            if not mid:
                loose.append(entry)
                continue
            key = (mid, rec.get("requestId"))
            prev = keyed.get(key)
            if prev is None or entry["total"] > prev["total"]:
                keyed[key] = entry
    return list(keyed.values()) + loose


def _aggregate(entries: list[dict], pricing: dict[str, dict[str, float]]) -> dict:
    totals = {k: 0 for k in TOKEN_KEYS}
    by_model: dict[str, dict] = {}
    usd = 0.0
    reported = 0
    stamps = sorted(str(e["ts"]) for e in entries if e.get("ts"))
    for e in entries:
        model = e["model"]
        if e["cost_usd"] is not None:
            cost = e["cost_usd"]  # transcript-supplied figure preferred
            reported += 1
        else:
            cost = price_tokens(e["tokens"], rates_for(model, pricing))
        usd += cost
        slot = by_model.setdefault(
            model, {**{k: 0 for k in TOKEN_KEYS}, "messages": 0, "usd_estimate": 0.0})
        for k in TOKEN_KEYS:
            totals[k] += e["tokens"][k]
            slot[k] += e["tokens"][k]
        slot["messages"] += 1
        slot["usd_estimate"] += cost
    for slot in by_model.values():
        slot["total"] = sum(slot[k] for k in TOKEN_KEYS)
        slot["usd_estimate"] = round(slot["usd_estimate"], 6)
    return {
        "tokens": {**totals, "total": sum(totals.values())},
        "usd_estimate": round(usd, 6),
        "by_model": by_model,
        "messages": len(entries),
        "cost_usd_reported_messages": reported,
        "first_ts": stamps[0] if stamps else None,
        "last_ts": stamps[-1] if stamps else None,
        "estimate": True,
    }


def _signature(files: list[Path], pricing: dict) -> dict:
    sig: dict[str, Any] = {"v": CACHE_VERSION, "files": []}
    for f in files:
        try:
            st = f.stat()
        except OSError:
            continue
        sig["files"].append([str(f), st.st_mtime_ns, st.st_size])
    sig["pricing"] = hashlib.sha1(
        json.dumps(pricing, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return sig


def session_usage(transcript_path: str | Path, root: Optional[Path] = None,
                  pricing: Optional[dict] = None) -> dict:
    """Token / USD-estimate summary for one session (main + subagents).

    With ``root`` the project's pricing override applies and the result is
    cached in ``.super-skill/cost_cache.json`` keyed by transcript path and
    the (mtime, size) of every contributing file, so repeated hook calls on
    an unchanged transcript cost only a few ``stat`` calls.
    """
    path = Path(transcript_path)
    if pricing is None:
        pricing = load_pricing(root)
    files = transcript_files(path)
    sig = _signature(files, pricing)
    key = str(path.resolve()) if path.exists() else str(path)
    cache_path = sdir(root) / CACHE_FILE if root is not None else None
    cache: dict = {}
    if cache_path is not None:
        cache = read_json(cache_path, default={}) or {}
        hit = cache.get(key)
        if isinstance(hit, dict) and hit.get("sig") == sig:
            return {**hit["result"], "cached": True}
    result = _aggregate(_entries(files), pricing)
    result["files"] = len(files)
    if cache_path is not None and root is not None and sdir(root).is_dir():
        cache[key] = {"sig": sig, "result": result}
        try:
            write_json_atomic(cache_path, cache)
        except OSError:
            pass  # cache is an optimisation only
    return {**result, "cached": False}


# ---------------------------------------------------------------- budget

def budget_status(root: Path, transcript_path: str | Path) -> dict:
    """Spend vs ``state["budget"]``; ``ratio`` is the worse of USD / tokens."""
    budget = load_state(root).get("budget") or {}
    if not isinstance(budget, dict):
        budget = {}
    usd_limit = budget.get("usd_limit")
    tok_limit = budget.get("token_limit")
    warn = budget.get("warn_ratio")
    warn = float(warn) if isinstance(warn, (int, float)) else DEFAULT_WARN_RATIO
    usd_limit = float(usd_limit) if isinstance(usd_limit, (int, float)) and usd_limit > 0 else None
    tok_limit = int(tok_limit) if isinstance(tok_limit, (int, float)) and tok_limit > 0 else None

    usage = session_usage(transcript_path, root=root)
    spent_usd = usage["usd_estimate"]
    spent_tok = usage["tokens"]["total"]
    ratios = []
    if usd_limit:
        ratios.append(spent_usd / usd_limit)
    if tok_limit:
        ratios.append(spent_tok / tok_limit)
    if not ratios:
        level, ratio = "off", None
    else:
        ratio = round(max(ratios), 4)
        level = "exceeded" if ratio >= 1.0 else "warn" if ratio >= warn else "ok"
    return {
        "level": level,
        "ratio": ratio,
        "spent_usd": spent_usd,
        "spent_tokens": spent_tok,
        "limit_usd": usd_limit,
        "limit_tokens": tok_limit,
        "warn_ratio": warn,
        "estimate": True,
    }


# ---------------------------------------------------------------- phase report

def _parse_ts(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    # naive stamps are taken as local time so they compare with aware ones
    return dt if dt.tzinfo else dt.astimezone()


def _new_phase(pid: str) -> dict:
    return {"phase": pid, "start": None, "end": None, "duration_s": 0.0,
            "runs": 0, "gate_failures": 0, "breaker_trips": 0,
            "tool_calls": 0, "tool_failures": 0, "cost_snapshots": [],
            "cost_usd_estimate": None}


def phase_report(root: Path) -> dict:
    """Per-phase timing, gate/breaker counts, tool calls and cost snapshots.

    Events are attributed to the phase whose ``phase_start`` most recently
    preceded them, until that phase's ``phase_done`` (or the next
    ``phase_start``); events outside any phase go to ``unattributed``.
    """
    base = sdir(root)
    records = read_jsonl(base / "ledger.jsonl")
    phases: dict[str, dict] = {}
    intervals: list[tuple[datetime, Optional[datetime], str]] = []
    active: Optional[str] = None
    active_since: Optional[datetime] = None

    def get(pid: str) -> dict:
        return phases.setdefault(pid, _new_phase(pid))

    for rec in records:
        kind = rec.get("kind")
        ts = _parse_ts(rec.get("ts"))
        pid = rec.get("phase")
        if kind == "phase_start" and pid:
            if active and active_since and ts:  # implicit close of previous
                intervals.append((active_since, ts, active))
                get(active)["duration_s"] += (ts - active_since).total_seconds()
            p = get(pid)
            p["runs"] += 1
            p["start"] = p["start"] or rec.get("ts")
            active, active_since = pid, ts
        elif kind == "phase_done" and pid:
            p = get(pid)
            p["end"] = rec.get("ts")
            if active == pid and active_since and ts:
                intervals.append((active_since, ts, pid))
                p["duration_s"] += (ts - active_since).total_seconds()
                active, active_since = None, None
        elif kind == "gate" and pid and rec.get("passed") is False:
            get(pid)["gate_failures"] += 1
        elif kind == "breaker" and str(rec.get("state", "")).upper() == "OPEN":
            target = pid or active
            if target:
                get(target)["breaker_trips"] += 1
        elif kind == "cost":
            target = pid or active
            if target:
                p = get(target)
                p["cost_snapshots"].append(
                    {"ts": rec.get("ts"), "usd": rec.get("usd"), "tokens": rec.get("tokens")})
                p["cost_usd_estimate"] = rec.get("usd")
    if active and active_since:
        intervals.append((active_since, None, active))  # still running

    unattributed = {"tool_calls": 0, "tool_failures": 0}
    for ev in read_jsonl(base / "events.jsonl"):
        name = str(ev.get("ev") or "")
        # count each tool call once, at its Post* event (Pre* has no outcome)
        if not name.startswith("PostToolUse"):
            continue
        failed = ev.get("ok") is False or name == "PostToolUseFailure"
        ts = _parse_ts(ev.get("ts"))
        owner = None
        if ts:
            for start, end, pid in intervals:
                if start <= ts and (end is None or ts < end):
                    owner = pid
        slot = phases[owner] if owner else unattributed
        slot["tool_calls"] += 1
        slot["tool_failures"] += int(failed)

    rows = list(phases.values())
    for p in rows:
        p["duration_s"] = round(p["duration_s"], 1)
    snaps = [s for p in rows for s in p["cost_snapshots"]
             if isinstance(s.get("usd"), (int, float))]
    latest_cost = max(snaps, key=lambda s: str(s["ts"]))["usd"] if snaps else None
    totals = {
        "phases": len(rows),
        "duration_s": round(sum(p["duration_s"] for p in rows), 1),
        "gate_failures": sum(p["gate_failures"] for p in rows),
        "breaker_trips": sum(p["breaker_trips"] for p in rows),
        "tool_calls": sum(p["tool_calls"] for p in rows) + unattributed["tool_calls"],
        "tool_failures": sum(p["tool_failures"] for p in rows) + unattributed["tool_failures"],
        "latest_cost_usd_estimate": latest_cost,
    }
    return {"generated": now_iso(), "phases": rows, "unattributed": unattributed,
            "totals": totals, "estimate": True}


def _fmt_dur(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{sec:02d}s"


def _fmt_usd(v: Any) -> str:
    return f"~${v:.2f}" if isinstance(v, (int, float)) and not isinstance(v, bool) else "-"


def render_report_md(report: dict) -> str:
    lines = [
        "# Super-Skill run report",
        "",
        f"_Generated {report.get('generated', '')}. USD figures are estimates "
        "(list prices applied to token counts), not billing data._",
        "",
        "| Phase | Start | End | Duration | Runs | Gate fails | Breaker trips "
        "| Tool calls | Tool fails | Cost (est.) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for p in report.get("phases", []):
        lines.append(
            f"| {p['phase']} | {p['start'] or '-'} | {p['end'] or '-'} "
            f"| {_fmt_dur(p['duration_s'])} | {p['runs']} | {p['gate_failures']} "
            f"| {p['breaker_trips']} | {p['tool_calls']} | {p['tool_failures']} "
            f"| {_fmt_usd(p['cost_usd_estimate'])} |")
    un = report.get("unattributed", {})
    if un.get("tool_calls"):
        lines.append(f"| _(outside phases)_ | - | - | - | - | - | - "
                     f"| {un['tool_calls']} | {un['tool_failures']} | - |")
    t = report.get("totals", {})
    lines += [
        "",
        "## Totals",
        "",
        f"- Phases: {t.get('phases', 0)}",
        f"- Active duration: {_fmt_dur(t.get('duration_s', 0))}",
        f"- Gate failures: {t.get('gate_failures', 0)}",
        f"- Breaker trips: {t.get('breaker_trips', 0)}",
        f"- Tool calls: {t.get('tool_calls', 0)} ({t.get('tool_failures', 0)} failed)",
        f"- Latest cost snapshot: {_fmt_usd(t.get('latest_cost_usd_estimate'))} (estimate)",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- snapshot

def snapshot(root: Path, transcript_path: str | Path, phase: Optional[str] = None) -> dict:
    """Append a ledger ``cost`` record with the current session estimate."""
    usage = session_usage(transcript_path, root=root)
    if phase is None:
        state = load_state(root)
        phase = state.get("active_phase") or state.get("phase") or state.get("current_phase")
    return ledger(root, "cost", usd=usage["usd_estimate"],
                  tokens=usage["tokens"]["total"], phase=phase, estimate=True)


# ---------------------------------------------------------------- CLI

def _print(obj: Any, as_json: bool, text: str) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2) if as_json else text)


def main(argv: Optional[list[str]] = None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="cost_meter",
                                 description="Super-Skill budget & observability (estimates).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("session", help="token/USD estimate for a transcript")
    s.add_argument("transcript")
    s.add_argument("--root", default=None, help="project root (pricing override + cache)")
    s.add_argument("--json", action="store_true")
    b = sub.add_parser("budget", help="budget level for the project")
    b.add_argument("--root", required=True)
    b.add_argument("--transcript", required=True)
    b.add_argument("--json", action="store_true")
    r = sub.add_parser("report", help="per-phase report (also writes REPORT.md)")
    r.add_argument("--root", required=True)
    r.add_argument("--json", action="store_true")
    n = sub.add_parser("snapshot", help="append a ledger cost record")
    n.add_argument("--root", required=True)
    n.add_argument("--transcript", required=True)
    n.add_argument("--phase", default=None)
    args = ap.parse_args(argv)

    if args.cmd == "session":
        u = session_usage(args.transcript, root=Path(args.root) if args.root else None)
        t = u["tokens"]
        _print(u, args.json,
               f"messages={u['messages']} tokens={t['total']} (in={t['input']} "
               f"out={t['output']} cache_w={t['cache_write']} cache_r={t['cache_read']}) "
               f"usd_estimate={_fmt_usd(u['usd_estimate'])}")
    elif args.cmd == "budget":
        st = budget_status(Path(args.root), args.transcript)
        ratio = "-" if st["ratio"] is None else f"{st['ratio']:.0%}"
        _print(st, args.json,
               f"budget={st['level']} ratio={ratio} spent={_fmt_usd(st['spent_usd'])} "
               f"/ {_fmt_usd(st['limit_usd'])}, tokens={st['spent_tokens']} "
               f"/ {st['limit_tokens'] or '-'} (estimate)")
    elif args.cmd == "report":
        root = Path(args.root)
        rep = phase_report(root)
        md = render_report_md(rep)
        if sdir(root).is_dir():
            (sdir(root) / REPORT_FILE).write_text(md, encoding="utf-8")
        _print(rep, args.json, md)
    elif args.cmd == "snapshot":
        rec = snapshot(Path(args.root), args.transcript, args.phase)
        print(json.dumps(rec, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
