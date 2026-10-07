#!/usr/bin/env python3
"""Daily research radar for Super-Skill self-update (deterministic, no LLM).

Scans three free sources and ranks what is *new* since the last run:

1. GitHub repository search (configured queries + topics, recently pushed,
   minimum stars) — new projects in the Claude Code / agent-skill space;
2. a watchlist of known best-in-class repos — new releases / fresh activity;
3. Hacker News (Algolia API) — recent high-signal stories.

Auth: ``GITHUB_TOKEN`` / ``GH_TOKEN`` or ``gh auth token`` when available
(5 000 req/h); otherwise unauthenticated (60 req/h, enough for one run).
State (``radar_state.json``, machine-local) de-duplicates across days; it is
only saved when the caller says the run succeeded.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

AUTO = Path(__file__).resolve().parent
CONFIG_FILE = AUTO / "radar_config.json"
STATE_FILE = AUTO / "radar_state.json"
UA = "super-skill-radar/1.0"

Fetch = Callable[[str], object]


# ---------------------------------------------------------------- io

def load_json(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def github_token() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    gh = shutil.which("gh")
    if not gh:
        return None
    try:
        out = subprocess.run([gh, "auth", "token"], capture_output=True, text=True, timeout=20)
        tok = (out.stdout or "").strip()
        return tok or None
    except (OSError, subprocess.SubprocessError):
        return None


def make_fetch(token: str | None, timeout: int = 30) -> Fetch:
    def fetch(url: str):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
        if token and "api.github.com" in url:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https hosts
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    return fetch


# ---------------------------------------------------------------- scoring

def relevance(text: str, keywords: list[str]) -> int:
    low = text.lower()
    return sum(1 for k in keywords if k.lower() in low)


def score_repo(repo: dict, prev: dict | None, keywords: list[str], today: dt.date) -> tuple[float, str]:
    stars = int(repo.get("stargazers_count") or 0)
    text = " ".join([repo.get("full_name") or "", repo.get("description") or "",
                     " ".join(repo.get("topics") or [])])
    rel = relevance(text, keywords)
    s = 1.5 * rel + math.log10(stars + 1)
    reasons = [f"relevance {rel}", f"{stars}★"]
    if prev is None:
        s += 2.0
        reasons.append("new to radar")
    else:
        delta = stars - int(prev.get("stars") or 0)
        if delta > 0:
            s += min(3.0, math.log10(delta + 1) * 1.5)
            reasons.append(f"+{delta}★ since last seen")
    created = (repo.get("created_at") or "")[:10]
    if created:
        try:
            age = (today - dt.date.fromisoformat(created)).days
            if age <= 30:
                s += 1.0
                reasons.append(f"created {age}d ago")
        except ValueError:
            pass
    return round(s, 3), ", ".join(reasons)


def _repo_item(repo: dict, kind: str, score: float, reason: str, extra: dict | None = None) -> dict:
    lic = (repo.get("license") or {}) or {}
    item = {"kind": kind, "name": repo.get("full_name"), "url": repo.get("html_url"),
            "stars": int(repo.get("stargazers_count") or 0), "description": (repo.get("description") or "")[:300],
            "license": lic.get("spdx_id") or "NONE", "pushed_at": repo.get("pushed_at"),
            "topics": (repo.get("topics") or [])[:8], "score": score, "reason": reason}
    item.update(extra or {})
    return item


# ---------------------------------------------------------------- sources

def scan_github(fetch: Fetch, cfg: dict, state: dict, today: dt.date, log) -> list[dict]:
    since = (today - dt.timedelta(days=cfg.get("lookback_days", 7))).isoformat()
    min_stars = cfg.get("min_stars", 50)
    seen = state.setdefault("seen", {})
    qs = [f"{q} pushed:>={since} stars:>={min_stars}" for q in cfg.get("queries", [])]
    qs += [f"topic:{t} pushed:>={since} stars:>={min_stars}" for t in cfg.get("topics", [])]
    found: dict[str, dict] = {}
    for q in qs:
        url = ("https://api.github.com/search/repositories?" +
               urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": 20}))
        try:
            data = fetch(url)
        except Exception as exc:  # noqa: BLE001 - one bad query must not kill the scan
            log(f"[radar] query failed ({exc.__class__.__name__}): {q}")
            continue
        for repo in (data or {}).get("items", []) if isinstance(data, dict) else []:
            if repo.get("fork") or repo.get("archived"):
                continue
            found.setdefault(repo["full_name"], repo)
    items = []
    for name, repo in found.items():
        prev = seen.get(name)
        if prev is not None and prev.get("stars") is None:
            prev["stars"] = int(repo.get("stargazers_count") or 0)  # seeded/known repo: baseline only
            continue
        if prev and int(repo.get("stargazers_count") or 0) - int(prev.get("stars") or 0) < cfg.get("min_delta", 25):
            continue  # already reviewed and not accelerating
        if relevance(" ".join([name, repo.get("description") or "", " ".join(repo.get("topics") or [])]),
                     cfg.get("keywords", [])) == 0:
            continue
        score, reason = score_repo(repo, prev, cfg.get("keywords", []), today)
        items.append(_repo_item(repo, "new_repo" if prev is None else "rising_repo", score, reason))
    return items


def scan_watchlist(fetch: Fetch, cfg: dict, state: dict, log) -> list[dict]:
    seen = state.setdefault("seen", {})
    items = []
    for name in cfg.get("watchlist", []):
        try:
            repo = fetch(f"https://api.github.com/repos/{name}")
        except Exception as exc:  # noqa: BLE001
            log(f"[radar] watchlist {name}: {exc.__class__.__name__}")
            continue
        if not isinstance(repo, dict) or not repo.get("full_name"):
            continue
        full = repo["full_name"]
        try:
            rel = fetch(f"https://api.github.com/repos/{full}/releases/latest")
            if rel is None:
                continue  # time budget used up: no answer is not "no release" — record nothing
            tag = rel.get("tag_name") if isinstance(rel, dict) else None
            notes = (rel.get("body") or "")[:600] if isinstance(rel, dict) else ""
        except Exception:  # noqa: BLE001 - many repos have no releases
            tag, notes = None, ""
        prev = seen.get(full) or seen.get(name)
        if prev is None or "release" not in prev:
            # first watch (incl. dossier-seeded repos): record a baseline, it is not news
            entry = dict(prev or {})
            entry.update(stars=repo.get("stargazers_count"), pushed_at=repo.get("pushed_at"), release=tag)
            entry.setdefault("first_seen", dt.date.today().isoformat())
            seen[full] = entry
            if name != full:
                seen[name] = dict(entry, renamed_to=full)  # renamed repo: both names are known
            continue
        if tag and tag != prev.get("release"):
            items.append(_repo_item(repo, "release", 6.0, f"new release {tag} (was {prev.get('release')})",
                                    {"release": tag, "release_notes": notes}))
    return items


def scan_hn(fetch: Fetch, cfg: dict, state: dict, now_ts: int, log) -> list[dict]:
    seen = set(state.get("hn_seen", []))
    since = now_ts - 86400 * cfg.get("hn_lookback_days", 2)
    items = []
    for q in cfg.get("hn_queries", []):
        url = ("https://hn.algolia.com/api/v1/search_by_date?" +
               urllib.parse.urlencode({"query": q, "tags": "story",
                                       "numericFilters": f"created_at_i>{since},points>{cfg.get('hn_min_points', 20)}"}))
        try:
            data = fetch(url)
        except Exception as exc:  # noqa: BLE001
            log(f"[radar] HN query failed ({exc.__class__.__name__}): {q}")
            continue
        for hit in (data or {}).get("hits", []) if isinstance(data, dict) else []:
            oid = str(hit.get("objectID"))
            if oid in seen:
                continue
            seen.add(oid)
            pts = int(hit.get("points") or 0)
            items.append({"kind": "hn", "name": hit.get("title"), "id": oid,
                          "url": hit.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                          "points": pts, "score": round(1.0 + math.log10(pts + 1), 3),
                          "reason": f"HN {pts} points"})
    state["hn_seen"] = sorted(seen)[-500:]
    return items


# ---------------------------------------------------------------- seeding

def seed_from_dossier(state: dict, dossier_dir: Path) -> int:
    """Mark every repo already studied in the research dossier as known.

    Known repos get ``stars: None``: the first sighting stores a baseline and
    only later star surges (``min_delta``) or new releases surface them.
    """
    import re
    seen = state.setdefault("seen", {})
    n = 0
    for md in sorted(Path(dossier_dir).glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="ignore")
        for owner, repo in re.findall(r"github\.com/([\w.-]+)/([\w.-]+)", text):
            name = f"{owner}/{repo.rstrip('.')}"
            if name not in seen:
                seen[name] = {"stars": None, "seed": "dossier", "first_seen": dt.date.today().isoformat()}
                n += 1
    return n


# ---------------------------------------------------------------- entry

BUDGET_S = 900   # whole scan ≤ 15 min even when every request hangs until its 30 s timeout


def _with_budget(fetch: Fetch, budget_s: float, log) -> Fetch:
    """After ``budget_s`` seconds every further request returns None (logged once)."""
    deadline = time.monotonic() + budget_s
    told = []

    def limited(url: str):
        if time.monotonic() >= deadline:
            if not told:
                told.append(True)
                log(f"[radar] time budget ({budget_s / 60:.0f} min) used up — skipping the remaining requests")
            return None
        return fetch(url)
    return limited

def run(cfg: dict | None = None, state: dict | None = None, fetch: Fetch | None = None,
        today: dt.date | None = None, log=print) -> tuple[list[dict], dict]:
    """Return (ranked candidates, updated state). The caller persists state."""
    cfg = cfg if cfg is not None else load_json(CONFIG_FILE, {})
    state = json.loads(json.dumps(state if state is not None else load_json(STATE_FILE, {})))
    fetch = _with_budget(fetch or make_fetch(github_token()), float(cfg.get("budget_s", BUDGET_S)), log)
    today = today or dt.date.today()
    now_ts = int(dt.datetime.now().timestamp())
    # watchlist first: it registers canonical names of renamed repos before search sees them
    items = scan_watchlist(fetch, cfg, state, log)
    items += scan_github(fetch, cfg, state, today, log)
    items += scan_hn(fetch, cfg, state, now_ts, log)
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    top = items[: cfg.get("top_n", 10)]
    for it in top:
        if it["kind"] in ("new_repo", "rising_repo", "release") and it.get("name"):
            entry = state.setdefault("seen", {}).setdefault(it["name"], {"first_seen": today.isoformat()})
            entry.update(stars=it.get("stars"), pushed_at=it.get("pushed_at"))
            if it.get("release"):
                entry["release"] = it["release"]
    state["last_run"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    return top, state


def to_markdown(items: list[dict], date: str) -> str:
    lines = [f"# Radar candidates — {date}", ""]
    if not items:
        return "\n".join(lines + ["(nothing new above the thresholds)"]) + "\n"
    lines += ["| # | Kind | Project | Stars/Points | License | Why |", "|---|---|---|---|---|---|"]
    for i, it in enumerate(items, 1):
        metric = it.get("stars", it.get("points", ""))
        lines.append(f"| {i} | {it['kind']} | [{it.get('name')}]({it.get('url')}) | {metric} | "
                     f"{it.get('license', '—')} | {it.get('reason', '')} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Super-Skill daily research radar")
    ap.add_argument("--out", default=str(AUTO / "daily_out" / "candidates.json"))
    ap.add_argument("--save-state", action="store_true", help="persist de-dup state (default: dry run)")
    args = ap.parse_args(argv)
    items, state = run()
    save_json(Path(args.out), items)
    print(to_markdown(items, dt.date.today().isoformat()))
    if args.save_state:
        save_json(STATE_FILE, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
