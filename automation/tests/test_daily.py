"""Tests for the daily self-update: radar, whitelist, versioning, scheduling and a
full end-to-end run against a throwaway repo with a local bare "origin", a fake
`claude`, a fake network and a configurable gate command."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AUTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUTO))
import radar  # noqa: E402
import schedule_daily  # noqa: E402
import superskill_daily as sd  # noqa: E402

TODAY = dt.date(2026, 10, 1)
CFG = {"queries": ["claude code skill"], "topics": [], "keywords": ["claude", "skill", "agent"],
       "watchlist": ["acme/watched"], "hn_queries": ["claude code"], "min_stars": 10, "min_delta": 25,
       "top_n": 10, "lookback_days": 7}


def repo_json(name, stars, desc="a claude code skill", created="2026-09-28", **kw):
    return {"full_name": name, "html_url": f"https://github.com/{name}", "stargazers_count": stars,
            "description": desc, "topics": ["claude-code"], "license": {"spdx_id": "MIT"},
            "pushed_at": "2026-09-30T00:00:00Z", "created_at": f"{created}T00:00:00Z", **kw}


def fake_fetch(search=(), watched=None, release=None, hn=()):
    def fetch(url):
        if "search/repositories" in url:
            return {"items": list(search)}
        if url.endswith("/releases/latest"):
            if release is None:
                raise OSError("404")
            return {"tag_name": release, "body": "notes"}
        if "api.github.com/repos/" in url:
            return watched or repo_json("acme/watched", 500)
        if "hn.algolia.com" in url:
            return {"hits": list(hn)}
        raise AssertionError(url)
    return fetch


# ---------------------------------------------------------------- radar

def test_radar_ranks_new_relevant_repos_and_skips_noise():
    items, state = radar.run(CFG, {}, fake_fetch(search=[
        repo_json("a/hot", 5000), repo_json("b/niche", 40),
        {**repo_json("c/offtopic", 9000, desc="kubernetes operator"), "topics": ["k8s"]},
        repo_json("d/fork", 999, fork=True)]), TODAY, log=lambda m: None)
    names = [i["name"] for i in items]
    assert names[:2] == ["a/hot", "b/niche"] and "c/offtopic" not in names and "d/fork" not in names
    assert state["seen"]["a/hot"]["stars"] == 5000


def test_radar_dedup_and_rising_detection():
    state = {"seen": {"a/hot": {"stars": 5000}}}
    items, _ = radar.run(CFG, state, fake_fetch(search=[repo_json("a/hot", 5010)]), TODAY, log=lambda m: None)
    assert not [i for i in items if i["name"] == "a/hot"], "small delta must not resurface"
    items, _ = radar.run(CFG, state, fake_fetch(search=[repo_json("a/hot", 5600)]), TODAY, log=lambda m: None)
    assert items[0]["kind"] == "rising_repo" and "+600" in items[0]["reason"]


def test_radar_seeded_repo_only_records_baseline(tmp_path):
    (tmp_path / "r.md").write_text("see https://github.com/a/hot and github.com/x/y.", encoding="utf-8")
    state = {}
    assert radar.seed_from_dossier(state, tmp_path) == 2
    items, state = radar.run(CFG, state, fake_fetch(search=[repo_json("a/hot", 5000)]), TODAY, log=lambda m: None)
    assert not items and state["seen"]["a/hot"]["stars"] == 5000


def test_radar_watchlist_release_and_hn_dedup():
    _, state = radar.run(CFG, {}, fake_fetch(release="v1.0"), TODAY, log=lambda m: None)
    assert state["seen"]["acme/watched"]["release"] == "v1.0"
    hn = [{"objectID": "42", "title": "Show HN: skill", "points": 80, "url": "https://x"}]
    items, state = radar.run(CFG, state, fake_fetch(release="v2.0", hn=hn), TODAY, log=lambda m: None)
    kinds = {i["kind"] for i in items}
    assert kinds == {"release", "hn"} and state["seen"]["acme/watched"]["release"] == "v2.0"
    items, _ = radar.run(CFG, state, fake_fetch(release="v2.0", hn=hn), TODAY, log=lambda m: None)
    assert not items, "same release and same HN story must not resurface"


def test_radar_dossier_seeded_watchlist_records_release_baseline():
    # regression (2026-10-01 live run): dossier-seeded watch repos never got a release baseline,
    # so every existing release would have been re-reported as "new" every day
    state = {"seen": {"acme/watched": {"stars": None, "seed": "dossier"}}}
    items, state = radar.run(CFG, state, fake_fetch(release="v1.0"), TODAY, log=lambda m: None)
    assert not items and state["seen"]["acme/watched"]["release"] == "v1.0"
    items, state = radar.run(CFG, state, fake_fetch(release="v1.0"), TODAY, log=lambda m: None)
    assert not items
    items, _ = radar.run(CFG, state, fake_fetch(release="v1.1"), TODAY, log=lambda m: None)
    assert [i["kind"] for i in items] == ["release"]


def test_radar_renamed_watch_repo_is_not_new():
    # regression: ruvnet/claude-flow → ruvnet/ruflo surfaced as a "new" repo
    cfg = dict(CFG, watchlist=["old/name"])
    renamed = repo_json("new/name", 7000)
    state = {"seen": {"old/name": {"stars": None, "seed": "dossier"}}}
    items, state = radar.run(cfg, state, fake_fetch(search=[renamed], watched=renamed), TODAY, log=lambda m: None)
    assert not items, items
    assert state["seen"]["new/name"]["stars"] == 7000 and state["seen"]["old/name"]["renamed_to"] == "new/name"


def test_parse_claude_output_json_and_text_fallback():
    wrapped = json.dumps({"type": "result", "result": "hi\n```json\n{\"a\": 1}\n```", "total_cost_usd": 1.25,
                          "num_turns": 7, "is_error": False, "subtype": "success"})
    text, meta = sd.parse_claude_output(wrapped + "\n[stderr] warning")
    assert text.startswith("hi") and meta["total_cost_usd"] == 1.25 and meta["num_turns"] == 7
    assert sd.parse_result(text) == {"a": 1}
    text, meta = sd.parse_claude_output("plain output\n```json\n{\"b\": 2}\n```")
    assert meta == {} and sd.parse_result(text) == {"b": 2}


def test_radar_survives_failing_source():
    def broken(url):
        raise OSError("network down")
    items, _ = radar.run(CFG, {}, broken, TODAY, log=lambda m: None)
    assert items == []


# ---------------------------------------------------------------- whitelist / versioning / schedule

@pytest.mark.parametrize("path,ok", [
    ("references/patterns/x.md", True), ("SKILL.md", True), ("engine/new_mod.py", True),
    ("engine/tests/test_new.py", True), ("engine/tests/test_core.py", False),
    ("hooks/pre_tool.py", False), ("install.py", False), ("phases.json", False),
    ("evals/bench_offline.py", False), ("scripts/run_all_tests.py", False), ("CHANGELOG.md", False),
    ("references/radar/2026-10-01.md", False), ("engine/ss_common.py", False),
    ("../evil.py", False), ("C:/x.py", False), ("README_ROOT.md", False)])
def test_whitelist(tmp_path, path, ok):
    skill, out = tmp_path / "skill", tmp_path / "out"
    (skill / "engine" / "tests").mkdir(parents=True)
    (skill / "engine" / "tests" / "test_core.py").write_text("x", encoding="utf-8")
    target = out / path.replace("../", "").replace("C:/", "")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("*Super-Skill V5.0.0: x*\n", encoding="utf-8")
    assert sd.validate_entry(skill, out, {"path": path})[0] is ok


def test_skill_md_line_gate(tmp_path):
    skill, out = tmp_path / "s", tmp_path / "o"
    out.mkdir(parents=True)
    (out / "SKILL.md").write_text("x\n" * 600 + "*Super-Skill V5.0.0: y*", encoding="utf-8")
    assert not sd.validate_entry(skill, out, {"path": "SKILL.md"})[0]
    (out / "SKILL.md").write_text("short, no footnote", encoding="utf-8")
    assert not sd.validate_entry(skill, out, {"path": "SKILL.md"})[0]


def test_versions():
    assert sd.next_version("V5.0.0") == "V5.0.1"
    assert sd.next_version("V5.0.9") == "V5.0.10"
    assert sd.next_version("V5") == "V5.0.1"


BJ = dt.timezone(dt.timedelta(hours=8))


def test_schedule_default_is_22_beijing():
    assert schedule_daily.DEFAULT_AT == "22:00" and schedule_daily.DEFAULT_TZ_OFFSET == 8.0
    args = schedule_daily.build_parser().parse_args([])
    assert args.at == "22:00" and args.tz_offset == 8.0


@pytest.mark.parametrize("now,expected", [
    (dt.datetime(2026, 10, 1, 21, 59, 42, tzinfo=BJ), dt.datetime(2026, 10, 1, 22, 0, tzinfo=BJ)),
    (dt.datetime(2026, 10, 1, 22, 0, 0, tzinfo=BJ), dt.datetime(2026, 10, 2, 22, 0, tzinfo=BJ)),
    (dt.datetime(2026, 10, 1, 22, 30, tzinfo=BJ), dt.datetime(2026, 10, 2, 22, 0, tzinfo=BJ)),
    (dt.datetime(2026, 10, 1, 13, 59, tzinfo=dt.timezone.utc), dt.datetime(2026, 10, 1, 22, 0, tzinfo=BJ)),
    # a machine in Europe at 16:30 CEST (= 22:30 Beijing) → next is tomorrow 22:00 Beijing
    (dt.datetime(2026, 10, 1, 16, 30, tzinfo=dt.timezone(dt.timedelta(hours=2))),
     dt.datetime(2026, 10, 2, 22, 0, tzinfo=BJ)),
])
def test_next_run_is_next_beijing_occurrence(now, expected):
    got = schedule_daily.next_run("22:00", 8, now=now)
    assert got == expected and got.utcoffset() == dt.timedelta(hours=8)


def test_windows_script_pins_utc8_boundary_and_settings():
    start = dt.datetime(2026, 10, 2, 22, 0, tzinfo=BJ)
    ps = schedule_daily.windows_register_script(r"C:\Py's\pythonw.exe", r"E:\a\b.py", r"E:\a", start)
    assert "$t.StartBoundary = '2026-10-02T22:00:00+08:00'" in ps
    assert "-StartWhenAvailable" in ps and "-MultipleInstances IgnoreNew" in ps
    assert f"New-TimeSpan -Hours {schedule_daily.EXEC_LIMIT_HOURS}" in ps
    assert "C:\\Py''s\\pythonw.exe" in ps, "single quotes must be escaped for PowerShell"


def test_cron_line_and_bad_time():
    line = schedule_daily.cron_line("22:00")
    assert line.startswith("0 22 * * * ") and line.endswith(schedule_daily.TAG)
    with pytest.raises(ValueError):
        schedule_daily.next_run("24:00", 8)


def test_schedule_time_conversion():
    local_offset = dt.datetime.now().astimezone().utcoffset().total_seconds() / 3600
    assert schedule_daily.local_time_for("23:00", local_offset) == "23:00"
    assert schedule_daily.local_time_for("23:30", local_offset - 1) == "00:30"


# ---------------------------------------------------------------- end to end

FAKE_CLAUDE = r'''
import json, os, pathlib, sys
prompt = sys.stdin.read()
assert "Today's candidates" in prompt
mode = pathlib.Path(os.environ["SS_FAKE_MODE_FILE"]).read_text().strip()
pathlib.Path(os.environ["SS_FAKE_MODE_FILE"] + ".cwd").write_text(os.getcwd())
out = pathlib.Path("automation/daily_out")
if mode == "nothing":
    print('```json\n{"changed": false, "summary": "nothing new", "adopted": [], "rejected": [{"source": "a/hot", "reason": "dup"}]}\n```')
    sys.exit(0)
if mode == "glob":
    (out / "references").mkdir(parents=True, exist_ok=True)
    (out / "references/x[a].md").write_text("model update", encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps([{"action": "update", "path": "references/x[a].md", "summary": "s"}]))
    print('```json' + chr(10) + '{"changed": true, "summary": "glob", "adopted": [{"source": "a/hot", "idea": "x", "files": []}], "rejected": []}' + chr(10) + '```')
    sys.exit(0)
(out / "references/patterns").mkdir(parents=True, exist_ok=True)
(out / "references/patterns/demo.md").write_text("# Demo pattern\n", encoding="utf-8")
(out / "hooks").mkdir(exist_ok=True)
(out / "hooks/pre_tool.py").write_text("evil = True\n", encoding="utf-8")
if mode == "tamper":   # a prompt-injected model writing outside the staging dir
    pathlib.Path(".claude/skills/super-skill/SKILL.md").write_text("tampered", encoding="utf-8")
    pathlib.Path("automation/superskill_daily.py").write_text("backdoor = True\n", encoding="utf-8")
    pathlib.Path("automation/new_evil.py").write_text("x = 1\n", encoding="utf-8")
(out / "manifest.json").write_text(json.dumps([
    {"action": "add", "path": "references/patterns/demo.md", "summary": "demo card", "source": "a/hot"},
    {"action": "update", "path": "hooks/pre_tool.py", "summary": "try to weaken the guard", "source": "a/hot"}]))
print('done\n```json\n{"changed": true, "summary": "adds a demo pattern card", "adopted": [{"source": "a/hot", "idea": "demo", "files": ["references/patterns/demo.md"], "license": "MIT", "mode": "pattern"}], "rejected": []}\n```')
'''


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8")


@pytest.fixture
def world(tmp_path, monkeypatch):
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "master", str(remote))
    repo = tmp_path / "repo"
    skill = repo / ".claude" / "skills" / "super-skill"
    (skill / "references" / "radar").mkdir(parents=True)
    (skill / "hooks").mkdir()
    (skill / "hooks" / "pre_tool.py").write_text("guard = True\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: super-skill\n---\n# S\n<!-- daily-self-update -->\nnone\n<!-- /daily-self-update -->\n"
        "*Super-Skill V5.0.0: test*\n", encoding="utf-8")
    (skill / "CHANGELOG.md").write_text("# Changelog\n\n## [5.0.0] - 2026-09-30\n- base\n", encoding="utf-8")
    (skill / "references" / "radar" / "README.md").write_text(
        "# Radar log\n\nDaily self-update digests (newest first). Generated by `automation/superskill_daily.py`.\n\n",
        encoding="utf-8")
    (repo / ".claude-plugin").mkdir()
    (repo / ".claude-plugin" / "plugin.json").write_text('{"name": "super-skill", "version": "5.0.0"}', encoding="utf-8")
    auto = repo / "automation"
    auto.mkdir()
    for f in ("radar.py", "superskill_daily.py", "daily_research_prompt.md"):
        shutil.copy2(AUTO / f, auto / f)
    (auto / "radar_config.json").write_text(json.dumps(CFG), encoding="utf-8")
    (repo / ".gitignore").write_text("automation/logs/\nautomation/daily_out/\nautomation/radar_state.json\n"
                                     "automation/fake_mode.txt\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "master")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-q", "origin", "master")
    fake = tmp_path / "fake_claude.py"
    fake.write_text(FAKE_CLAUDE, encoding="utf-8")
    monkeypatch.setenv("SUPERSKILL_CLAUDE", f"{sys.executable}|{fake}")
    monkeypatch.setenv("SS_FAKE_MODE_FILE", str(auto / "fake_mode.txt"))
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|pass")
    monkeypatch.setenv("SUPERSKILL_PUSH_LAYERS", "git")
    locks = tmp_path / "locks"
    monkeypatch.setenv("SUPERSKILL_LOCK_DIR", str(locks))   # never touch the real ~/.claude lock
    monkeypatch.setenv("GIT_AUTHOR_NAME", "t")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "t@t")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "t")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "t@t")
    return {"repo": repo, "remote": remote, "skill": skill, "auto": auto, "locks": locks}


def _args(repo, **kw):
    ns = argparse.Namespace(repo=str(repo), branch="master", dry_run=False, scan_only=False, no_push=False,
                            no_install=True, budget_usd=1.0, max_turns=5, timeout=120, wait_minutes=0)
    ns._fetch = fake_fetch(search=[repo_json("a/hot", 5000)])
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def test_end_to_end_adopts_commits_and_pushes(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 0
    skill = world["skill"]
    assert (skill / "references" / "patterns" / "demo.md").is_file()
    assert (skill / "hooks" / "pre_tool.py").read_text(encoding="utf-8") == "guard = True\n", "verifier untouched"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert "tampered" not in text and "*Super-Skill V5.0.1:" in text and "Latest daily self-update:** V5.0.1" in text
    assert "## [5.0.1]" in (skill / "CHANGELOG.md").read_text(encoding="utf-8")
    assert json.loads((world["repo"] / ".claude-plugin" / "plugin.json").read_text())["version"] == "5.0.1"
    digest = next((skill / "references" / "radar").glob("20*.md"))
    assert "a/hot" in digest.read_text(encoding="utf-8")
    log = _git(world["remote"], "log", "--oneline", "-1", "master").stdout
    assert "V5.0.1" in log, "commit must reach origin"
    assert json.loads((world["auto"] / "radar_state.json").read_text())["seen"]["a/hot"]["stars"] == 5000
    assert not _git(world["repo"], "status", "--porcelain", "--untracked-files=no").stdout.strip()


def test_two_runs_same_day_keep_both_digests(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 0
    second = _args(world["repo"])
    second._fetch = fake_fetch(search=[repo_json("b/fresh", 3000)])
    assert sd.run(second) == 0
    digests = sorted(p.name for p in (world["skill"] / "references" / "radar").glob("20*.md"))
    assert len(digests) == 2 and any(d.endswith("-2.md") for d in digests), digests
    assert "V5.0.2" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout


def test_end_to_end_gate_failure_reverts_everything(world, monkeypatch):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|raise SystemExit(1)")
    assert sd.run(_args(world["repo"])) == 1
    assert not (world["skill"] / "references" / "patterns").exists()
    assert "*Super-Skill V5.0.0:" in (world["skill"] / "SKILL.md").read_text(encoding="utf-8")
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout
    assert not _git(world["repo"], "status", "--porcelain", "--", ".claude").stdout.strip()
    assert not _git(world["repo"], "stash", "list").stdout.strip(), "only pipeline output: nothing to keep"


def test_end_to_end_nothing_to_adopt_makes_no_commit(world):
    (world["auto"] / "fake_mode.txt").write_text("nothing", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 0
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout


def test_preflight_refuses_dirty_tree_and_honours_pause(world):
    (world["skill"] / "SKILL.md").write_text("local edit", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 1
    _git(world["repo"], "checkout", "--", ".")
    (world["auto"] / "PAUSE").write_text("", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 0
    report = (world["auto"] / "logs" / f"daily_{dt.date.today().isoformat()}.md").read_text(encoding="utf-8")
    assert "PAUSE" in report


# ---------------------------------------------------------------- pipeline lock (daily ⟂ weekly)

import os  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

import pipeline_lock  # noqa: E402


HOLDER = r'''
import sys, time
sys.path.insert(0, sys.argv[1])
import pipeline_lock
assert pipeline_lock.acquire(sys.argv[2], sys.argv[3], log=lambda m: None)
print("locked", flush=True)
time.sleep(float(sys.argv[4]))
'''  # exits WITHOUT release(): the operating system must drop the lock


def _hold_in_subprocess(lock_dir, owner, seconds):
    p = subprocess.Popen([sys.executable, "-c", HOLDER, str(AUTO), str(lock_dir), owner, str(seconds)],
                         stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "locked"
    return p


def test_pipeline_lock_is_os_level_and_released_when_holder_is_killed(tmp_path):
    p = _hold_in_subprocess(tmp_path, "weekly", 60)
    try:
        assert pipeline_lock.is_held(tmp_path)
        assert not pipeline_lock.acquire(tmp_path, "daily", wait_s=0, log=lambda m: None)
        assert pipeline_lock.holder(tmp_path)["owner"] == "weekly"
    finally:
        p.kill()
        p.wait()
    assert pipeline_lock.acquire(tmp_path, "daily", log=lambda m: None), "a killed holder leaves nothing stale"
    pipeline_lock.release(tmp_path, "daily")
    assert not pipeline_lock.is_held(tmp_path)


def test_pipeline_lock_waits_for_holder_to_exit(tmp_path):
    p = _hold_in_subprocess(tmp_path, "weekly", 0.6)
    t0 = time.monotonic()
    assert pipeline_lock.acquire(tmp_path, "daily", wait_s=20, poll_s=0.05, log=lambda m: None)
    assert time.monotonic() - t0 > 0.3
    pipeline_lock.release(tmp_path, "daily")
    p.wait()


def test_pipeline_lock_owner_checked_release_in_process(tmp_path):
    assert pipeline_lock.acquire(tmp_path, "daily", log=lambda m: None)
    assert not pipeline_lock.acquire(tmp_path, "weekly", wait_s=0, log=lambda m: None)
    pipeline_lock.release(tmp_path, "weekly")          # not the owner: no-op
    assert pipeline_lock.is_held(tmp_path)
    pipeline_lock.release(tmp_path, "daily")
    assert not pipeline_lock.is_held(tmp_path)
    assert pipeline_lock.acquire(tmp_path, "weekly", log=lambda m: None)
    pipeline_lock.release(tmp_path, "weekly")


def test_daily_waits_for_legacy_weekly_lock(world, monkeypatch):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    logs = world["auto"] / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "weekly.lock").write_text("123", encoding="utf-8")
    assert sd.run(_args(world["repo"], wait_minutes=0)) == 0
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout, "must not run"
    monkeypatch.setattr(sd, "LOCK_POLL_S", 0.05)
    threading.Timer(0.4, (logs / "weekly.lock").unlink).start()
    t0 = time.monotonic()
    assert sd.run(_args(world["repo"], wait_minutes=0.5)) == 0
    assert time.monotonic() - t0 > 0.3, "it must have waited for the weekly run"
    assert "V5.0.1" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout
    assert not pipeline_lock.is_held(world["locks"]), "lock released after the run"


def test_daily_ignores_dead_legacy_weekly_lock(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    logs = world["auto"] / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "weekly.lock").write_text("123", encoding="utf-8")
    old = time.time() - sd.LEGACY_STALE_S - 60
    os.utime(logs / "weekly.lock", (old, old))
    assert sd.run(_args(world["repo"], wait_minutes=0)) == 0
    assert "V5.0.1" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout


def test_daily_skips_while_other_pipeline_holds_lock(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    p = _hold_in_subprocess(world["locks"], "weekly", 60)
    try:
        assert sd.run(_args(world["repo"], wait_minutes=0)) == 0
        assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout
        assert pipeline_lock.holder(world["locks"])["owner"] == "weekly", "foreign lock untouched"
    finally:
        p.kill()
        p.wait()


def test_weekly_yields_to_running_daily_and_records_skip(tmp_path, monkeypatch):
    import superskill_weekly as wk
    monkeypatch.setattr(wk, "LOGS", tmp_path)
    monkeypatch.setattr(wk, "LOCK_FILE", tmp_path / "weekly.lock")
    monkeypatch.setattr(wk, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(wk, "PAUSE_FLAG", tmp_path / "PAUSE")
    monkeypatch.setenv("SUPERSKILL_LOCK_DIR", str(tmp_path / "locks"))
    monkeypatch.setenv("SUPERSKILL_WEEKLY_LOCK_WAIT_MIN", "0")
    p = _hold_in_subprocess(tmp_path / "locks", "daily", 60)
    try:
        assert wk.main([]) == 0
        state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
        assert state["last_result"] == "skipped" and "giving up" in " ".join(state["lock_messages"])
        assert "giving up" in (tmp_path / "weekly_lock_skips.log").read_text(encoding="utf-8")
        assert not (tmp_path / "weekly.lock").exists()
    finally:
        p.kill()
        p.wait()
    assert wk.acquire_lock(lambda m: None) is True
    assert pipeline_lock.holder()["owner"] == "weekly" and (tmp_path / "weekly.lock").exists()
    wk.release_lock()
    assert not pipeline_lock.is_held() and not (tmp_path / "weekly.lock").exists()


# ---------------------------------------------------------------- interrupted-run recovery

def _write_marker(world, head=None, since=None, owner="daily"):
    logs = world["auto"] / "logs"
    logs.mkdir(exist_ok=True)
    head = head if head is not None else _git(world["repo"], "rev-parse", "HEAD").stdout.strip()
    since = since or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    (logs / sd.IN_PROGRESS).write_text(json.dumps(
        {"owner": owner, "date": "2026-09-30", "pid": 1, "head": head, "since": since}), encoding="utf-8")
    return logs


def test_preflight_recovers_interrupted_run_by_stashing(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    logs = _write_marker(world)
    (world["skill"] / "SKILL.md").write_text("half-applied by a killed run", encoding="utf-8")
    (world["skill"] / "references" / "orphan.md").write_text("left behind", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 0
    stashes = _git(world["repo"], "stash", "list").stdout
    assert "super-skill interrupted daily run of 2026-09-30" in stashes, "changes kept, not discarded"
    assert "V5.0.1" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout
    assert not (logs / sd.IN_PROGRESS).exists()


def test_stale_marker_never_stashes_work_made_after_new_commits(world):
    # review E1: a marker outliving its run turned "refuse a dirty tree" into "stash the human's WIP"
    _write_marker(world, head="deadbeef" * 5)
    (world["skill"] / "SKILL.md").write_text("HUMAN WIP", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 1
    assert (world["skill"] / "SKILL.md").read_text(encoding="utf-8") == "HUMAN WIP"
    assert not _git(world["repo"], "stash", "list").stdout.strip()
    assert (world["auto"] / "logs" / sd.IN_PROGRESS).exists(), "kept for a human"


def test_marker_does_not_claim_files_edited_long_after_the_run(world):
    yesterday = (dt.datetime.now().astimezone() - dt.timedelta(hours=20)).isoformat(timespec="seconds")
    _write_marker(world, since=yesterday)
    (world["skill"] / "SKILL.md").write_text("edited this morning", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 1
    assert (world["skill"] / "SKILL.md").read_text(encoding="utf-8") == "edited this morning"
    assert not _git(world["repo"], "stash", "list").stdout.strip()


def test_failed_run_never_deletes_untracked_human_files_in_plugin_dir(world, monkeypatch):
    # review E2: revert used `git clean -f` on .claude-plugin/
    draft = world["repo"] / ".claude-plugin" / "draft-hooks.json"
    draft.write_text("{}", encoding="utf-8")
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|raise SystemExit(1)")
    assert sd.run(_args(world["repo"])) == 1
    assert draft.read_text(encoding="utf-8") == "{}"
    assert not (world["auto"] / "logs" / sd.IN_PROGRESS).exists()


def test_revert_stashes_a_human_edit_made_during_the_run(world, monkeypatch):
    # review E3: `git checkout -- .` silently discarded edits typed while the run was going
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    gate = "open('SKILL.md','a',encoding='utf-8').write('HUMAN LINE');raise SystemExit(1)"
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|{gate}")
    assert sd.run(_args(world["repo"])) == 1
    assert not (world["skill"] / "references" / "patterns").exists(), "pipeline-only files restored"
    stash = _git(world["repo"], "stash", "list").stdout
    assert "gates failed" in stash
    assert "HUMAN LINE" in _git(world["repo"], "stash", "show", "-p", "stash@{0}").stdout
    assert "*Super-Skill V5.0.0:" in (world["skill"] / "SKILL.md").read_text(encoding="utf-8")


def test_preflight_refuses_interrupted_run_mixed_with_human_edits(world):
    logs = world["auto"] / "logs"
    logs.mkdir(exist_ok=True)
    (logs / sd.IN_PROGRESS).write_text('{"date": "2026-09-30", "pid": 1}', encoding="utf-8")
    (world["repo"] / ".gitignore").write_text("edited by a human\n", encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 1
    assert (logs / sd.IN_PROGRESS).exists(), "marker kept for a human to resolve"
    assert not _git(world["repo"], "stash", "list").stdout.strip()
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout


def test_marker_cleared_after_successful_and_reverted_runs(world, monkeypatch):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|raise SystemExit(1)")
    assert sd.run(_args(world["repo"])) == 1
    assert not (world["auto"] / "logs" / sd.IN_PROGRESS).exists(), "reverted run leaves a clean tree"


# ---------------------------------------------------------------- schedule status

def test_boundary_mismatch_detects_old_registrations():
    assert schedule_daily.boundary_mismatch("2026-10-02T22:00:00+08:00") is None
    assert "re-run" in schedule_daily.boundary_mismatch("2026-10-01T23:00:00+08:00")
    assert "no UTC offset" in schedule_daily.boundary_mismatch("2026-10-02T22:00:00")
    assert schedule_daily.boundary_mismatch("2026-10-02T14:00:00+00:00") is None   # same instant
    assert schedule_daily.EXEC_LIMIT_HOURS == 7


def test_dry_run_changes_nothing(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    assert sd.run(_args(world["repo"], dry_run=True)) == 0
    assert not (world["skill"] / "references" / "patterns").exists()
    assert not (world["auto"] / "radar_state.json").exists()
    assert (world["auto"] / "daily_out" / "manifest.json").is_file()


# ---------------------------------------------------------------- second-review regressions

import pipeline_recovery as recovery  # noqa: E402


def test_porcelain_fails_closed_and_parses_renames():
    assert recovery.porcelain_paths(lambda *a: (128, "fatal: dubious ownership")) is None
    raw = (" R automation/ren dst.md\0.claude/skills/super-skill/ren.md\0"
           "R  .claude/skills/super-skill/moved in.md\0automation/old name.md\0 M 中文 路径.md\0")
    paths = recovery.porcelain_paths(lambda *a: (0, raw))
    assert paths == ["automation/ren dst.md", ".claude/skills/super-skill/ren.md",
                     ".claude/skills/super-skill/moved in.md", "automation/old name.md", "中文 路径.md"]


def test_marker_kept_when_git_status_fails(tmp_path):
    (tmp_path / recovery.MARKER).write_text("{}", encoding="utf-8")
    assert not recovery.clear_if_clean(tmp_path, lambda *a: (128, "fatal"))
    assert (tmp_path / recovery.MARKER).exists()
    ok, msg = recovery.recover(tmp_path, tmp_path, lambda *a: (128, "fatal"))
    assert not ok and "git status failed" in msg and (tmp_path / recovery.MARKER).exists()


def test_holder_ignores_non_object_info(tmp_path):
    p = _hold_in_subprocess(tmp_path, "weekly", 60)
    try:
        for junk in ("[1]", '"x"', "5"):
            (tmp_path / (pipeline_lock.LOCK_NAME + pipeline_lock.INFO_SUFFIX)).write_text(junk, encoding="utf-8")
            assert pipeline_lock.holder(tmp_path) is None
            assert not pipeline_lock.acquire(tmp_path, "daily", wait_s=0, log=lambda m: None)
    finally:
        p.kill()
        p.wait()


def test_daily_ignores_weekly_lock_left_by_a_killed_new_weekly(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    logs = world["auto"] / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "weekly.lock").write_text('{"pid": 1, "os_lock": true}', encoding="utf-8")
    assert sd.run(_args(world["repo"], wait_minutes=0)) == 0
    assert "V5.0.1" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout


def _weekly_env(tmp_path, monkeypatch, repo=None):
    import superskill_weekly as wk
    monkeypatch.setattr(wk, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(wk, "LOCK_FILE", tmp_path / "logs" / "weekly.lock")
    monkeypatch.setattr(wk, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(wk, "PAUSE_FLAG", tmp_path / "PAUSE")
    if repo is not None:
        monkeypatch.setattr(wk, "REPO", repo)
    monkeypatch.setenv("SUPERSKILL_LOCK_DIR", str(tmp_path / "locks"))
    monkeypatch.setenv("SUPERSKILL_WEEKLY_LOCK_WAIT_MIN", "0")
    return wk


def test_weekly_takes_over_its_own_tagged_lock(tmp_path, monkeypatch):
    wk = _weekly_env(tmp_path, monkeypatch)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "weekly.lock").write_text('{"pid": 1, "os_lock": true}', encoding="utf-8")
    msgs = []
    assert wk.acquire_lock(msgs.append) is True and "接管" in " ".join(msgs)
    wk.release_lock()
    (tmp_path / "logs" / "weekly.lock").write_text("123", encoding="utf-8")   # untagged = old clone
    assert wk.acquire_lock(lambda m: None) is False


def test_weekly_honours_interrupted_daily_marker(world, monkeypatch):
    # review: the weekly committed and pushed an interrupted daily run's ungated leftovers
    wk = _weekly_env(world["repo"].parent, monkeypatch, repo=world["repo"])
    monkeypatch.setattr(wk, "LOGS", world["auto"] / "logs")
    _write_marker(world, head="deadbeef" * 5)
    (world["skill"] / "SKILL.md").write_text("half-applied", encoding="utf-8")
    called = []
    monkeypatch.setattr(wk, "stage_s5", lambda log, state: called.append(1))
    wk.main(["--stages", "s5"])
    state = json.loads((world["repo"].parent / "state.json").read_text(encoding="utf-8"))
    assert not called and state["s5"]["ok"] is False and "人工" in state["s5"]["note"]
    assert (world["skill"] / "SKILL.md").read_text(encoding="utf-8") == "half-applied"


def test_api_push_refuses_to_overwrite_unknown_remote_content(world, monkeypatch, capsys):
    import api_push
    monkeypatch.setattr(api_push, "REPO_ROOT", world["repo"])
    calls = []

    def fake_gh(method, path, payload=None):
        calls.append((method, path))
        if "/git/ref/" in path:
            return {"object": {"sha": "f" * 40}}
        if "/git/commits/" in path:
            return {"tree": {"sha": "e" * 40}}      # a tree the local history never had
        raise AssertionError(path)
    monkeypatch.setattr(api_push, "gh_api", fake_gh)
    monkeypatch.setattr(sys, "argv", ["api_push", "--repo", "o/r", "--branch", "master"])
    assert api_push.main() == 1
    assert all(m == "GET" for m, _ in calls), "nothing may be written"
    assert "拒绝推送" in capsys.readouterr().err


def test_radar_time_budget_stops_requests():
    seen, logs = [], []

    def fetch(url):
        seen.append(url)
        return {}
    items, _ = radar.run(dict(CFG, budget_s=0), {}, fetch, TODAY, log=logs.append)
    assert items == [] and not seen and any("time budget" in m for m in logs)


@pytest.mark.skipif(os.name != "nt", reason="Job Objects are Windows-only")
def test_children_die_with_a_killed_pipeline():
    parent = (f"import sys, subprocess, time; sys.path.insert(0, {str(AUTO)!r}); import pipeline_lock;"
              "assert pipeline_lock.tie_children_to_this_process();"
              f"c = subprocess.Popen([{sys.executable!r}, '-c', 'import time; time.sleep(60)']);"
              "print(c.pid, flush=True); time.sleep(60)")
    p = subprocess.Popen([sys.executable, "-c", parent], stdout=subprocess.PIPE, text=True)
    child = int(p.stdout.readline())
    p.kill()
    p.wait()
    for _ in range(50):
        out = subprocess.run(["tasklist", "/FI", f"PID eq {child}", "/NH"], capture_output=True,
                             encoding="mbcs", errors="replace").stdout
        if str(child) not in out:
            break
        time.sleep(0.1)
    assert str(child) not in out, "orphaned child survived its killed pipeline"


def test_model_runs_in_a_sandbox_and_cannot_touch_the_live_tree(world):
    # review: path-set snapshots missed ignored files (a planted test the gate runs nightly)
    (world["auto"] / "fake_mode.txt").write_text("tamper", encoding="utf-8")
    original = (world["auto"] / "superskill_daily.py").read_text(encoding="utf-8")
    assert sd.run(_args(world["repo"])) == 0
    cwd = Path((world["auto"] / "fake_mode.txt.cwd").read_text())
    assert cwd.resolve() != world["repo"].resolve() and not cwd.exists(), "throwaway worktree, removed"
    assert (world["auto"] / "superskill_daily.py").read_text(encoding="utf-8") == original
    assert not (world["auto"] / "new_evil.py").exists()
    assert "tampered" not in (world["skill"] / "SKILL.md").read_text(encoding="utf-8")
    assert (world["skill"] / "references" / "patterns" / "demo.md").is_file(), "staged output still used"
    assert "ss-distill-" not in _git(world["repo"], "worktree", "list").stdout


def test_edit_during_the_radar_scan_stops_the_run(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    args = _args(world["repo"])
    inner = args._fetch

    def fetch(url):
        with open(world["skill"] / "SKILL.md", "a", encoding="utf-8") as fh:
            fh.write("HUMAN")
        return inner(url)
    args._fetch = fetch
    assert sd.run(args) == 1
    assert (world["skill"] / "SKILL.md").read_text(encoding="utf-8").endswith("HUMAN")
    assert not _git(world["repo"], "stash", "list").stdout.strip()
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout


def test_human_edit_during_passing_gates_is_never_committed(world, monkeypatch):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    gate = "open('SKILL.md','a',encoding='utf-8').write('HUMAN LINE')"
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|{gate}")
    assert sd.run(_args(world["repo"])) == 1
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout
    assert "HUMAN LINE" in _git(world["repo"], "stash", "show", "-p", "stash@{0}").stdout


def test_revert_uses_literal_pathspecs(world, monkeypatch):
    # review: `git checkout HEAD -- x[a].md` also matched xa.md and wiped a human edit
    refs = world["skill"] / "references"
    (refs / "x[a].md").write_text("orig bracket", encoding="utf-8")
    (refs / "xa.md").write_text("orig plain", encoding="utf-8")
    _git(world["repo"], "add", "-A")
    _git(world["repo"], "commit", "-qm", "two files")
    _git(world["repo"], "push", "-q", "origin", "master")
    (world["auto"] / "fake_mode.txt").write_text("glob", encoding="utf-8")
    gate = "open('references/xa.md','w',encoding='utf-8').write('HUMAN WORK');raise SystemExit(1)"
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|{gate}")
    assert sd.run(_args(world["repo"])) == 1
    assert (refs / "x[a].md").read_text(encoding="utf-8") == "orig bracket"
    kept = (refs / "xa.md").read_text(encoding="utf-8") == "HUMAN WORK" or \
        "HUMAN WORK" in _git(world["repo"], "stash", "show", "-p", "stash@{0}").stdout
    assert kept, "the human edit must survive (in place or in a stash)"


def test_weekly_s5_never_commits_work_it_did_not_apply(world, monkeypatch):
    # review: S5 committed a human's uncommitted SKILL.md edit after S3 skipped
    wk = _weekly_env(world["repo"].parent, monkeypatch, repo=world["repo"])
    (world["skill"] / "SKILL.md").write_text("HALF-WRITTEN HUMAN DRAFT", encoding="utf-8")
    state = {"s3": {"ok": True, "note": "无新增材料，跳过蒸馏"}}
    assert wk.stage_s5(lambda m: None, state) is False
    assert "base" in _git(world["remote"], "log", "--oneline", "-1", "master").stdout
    assert (world["skill"] / "SKILL.md").read_text(encoding="utf-8") == "HALF-WRITTEN HUMAN DRAFT"


def test_weekly_s3_crash_after_distill_is_reverted(world, monkeypatch):
    # review: an exception in _apply_staged skipped the rollback and S4/S5 shipped the output
    wk = _weekly_env(world["repo"].parent, monkeypatch, repo=world["repo"])
    out = world["repo"].parent / "distill_out"
    monkeypatch.setattr(wk, "DISTILL_OUT", out)
    monkeypatch.setattr(wk, "SKILL_SRC", world["skill"])
    (world["repo"].parent / "logs").mkdir(exist_ok=True)
    real_sh = wk.sh

    def fake_sh(args, *a, **kw):
        if "-p" in [str(x) for x in args]:
            (out / "references").mkdir(parents=True, exist_ok=True)
            (out / "references" / "new.md").write_text("ungated", encoding="utf-8")
            (out / "manifest.json").write_text('[{"path": "references/new.md"}]', encoding="utf-8")
            return 0, '```json\n{"changed": true, "summary": "x"}\n```'
        return real_sh(args, *a, **kw)
    monkeypatch.setattr(wk, "sh", fake_sh)

    def boom(log, entries):
        raise RuntimeError("crash after the files were applied")
    monkeypatch.setattr(wk, "_jev_verify_applied", boom)
    state = {"s2": {"new_materials": [{"source": "s", "title": "t", "path": "p"}]}}
    assert wk.stage_s3(lambda m: None, state) is False
    assert "异常" in state["s3"]["note"]
    assert not (world["skill"] / "references" / "new.md").exists()
    assert "weekly revert" in _git(world["repo"], "stash", "list").stdout


def test_api_push_accepts_only_its_own_history(world, monkeypatch, tmp_path):
    import api_push
    monkeypatch.setattr(api_push, "REPO_ROOT", world["repo"])
    monkeypatch.setattr(api_push, "STATE", tmp_path / "api_push_state.json")
    head = _git(world["repo"], "rev-parse", "HEAD").stdout.strip()
    assert api_push._remote_is_ours(head), "remote == an ancestor of HEAD: fast-forward"
    assert not api_push._remote_is_ours("f" * 40), "unknown remote commit (another machine, a revert)"
    (tmp_path / "api_push_state.json").write_text(json.dumps({"remote_sha": "f" * 40, "local_head": head}))
    assert api_push._remote_is_ours("f" * 40), "same tree, different SHA from our own last api push"


def test_radar_budget_never_records_a_false_release_baseline():
    def fetch(url):
        if url.endswith("/releases/latest"):
            return None                     # what the budget wrapper returns once time is up
        return repo_json("acme/watched", 100)
    _, state = radar.run(dict(CFG, budget_s=900), {}, fetch, TODAY, log=lambda m: None)
    assert "acme/watched" not in state.get("seen", {}), "no answer must not become a 'no release' baseline"


@pytest.mark.parametrize("path", ["engine/SS_COMMON.py", "engine/ss_common.py.", "engine/ss_common.py ",
                                  "references/Radar/README.md", "engine/./ss_common.py", "skill.md",
                                  "engine/Tests/test_core.py"])
def test_whitelist_is_case_and_dot_insensitive(tmp_path, path):
    # review: on NTFS these name the protected file itself
    skill, out = tmp_path / "skill", tmp_path / "out"
    (skill / "engine" / "tests").mkdir(parents=True)
    (skill / "engine" / "ss_common.py").write_text("x", encoding="utf-8")
    (skill / "engine" / "tests" / "test_core.py").write_text("x", encoding="utf-8")
    (skill / "SKILL.md").write_text("x", encoding="utf-8")
    target = out / path.rstrip(". ")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("*Super-Skill V5.0.0: x*\n", encoding="utf-8")
    assert sd.validate_entry(skill, out, {"path": path})[0] is False


def test_api_push_publishes_mode_only_changes(world, monkeypatch, tmp_path):
    import api_push
    repo = world["repo"]
    (repo / "run.sh").write_text("echo hi\n", encoding="utf-8")
    _git(repo, "add", "run.sh")
    _git(repo, "commit", "-qm", "script")
    blob = _git(repo, "rev-parse", "HEAD:run.sh").stdout.strip()
    tree_before = _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "update-index", "--chmod=+x", "run.sh")
    _git(repo, "commit", "-qm", "exec bit")
    entries = [{"path": l.split("\t")[1], "mode": l.split()[0], "type": l.split()[1], "sha": l.split()[2]}
               for l in _git(repo, "ls-tree", "-r", base).stdout.splitlines()]
    monkeypatch.setattr(api_push, "REPO_ROOT", repo)
    monkeypatch.setattr(api_push, "STATE", tmp_path / "state.json")
    posted = []

    def fake_gh(method, path, payload=None):
        if "/git/ref/" in path and method == "GET":
            return {"object": {"sha": base}}
        if "/git/commits/" in path and method == "GET":
            return {"tree": {"sha": tree_before}}
        if "/git/trees/" in path:
            return {"tree": entries}
        if path.endswith("/git/trees"):
            posted.append(payload)
            return {"sha": "t" * 40}
        if path.endswith("/git/commits"):
            return {"sha": "c" * 40}
        if method == "PATCH":
            return {}
        if path.endswith("/git/blobs"):
            raise AssertionError("mode-only change must not re-upload the blob")
        raise AssertionError(path)
    monkeypatch.setattr(api_push, "gh_api", fake_gh)
    monkeypatch.setattr(sys, "argv", ["api_push", "--repo", "o/r", "--branch", "master"])
    api_push.main()   # the fake cannot pass the final tree check; what matters is what was sent
    assert posted and {"path": "run.sh", "mode": "100755", "type": "blob", "sha": blob} in posted[0]["tree"]


def test_children_never_run_under_pythonw(monkeypatch, tmp_path):
    # live regression (2026-10-02..04): the scheduled task runs pythonw.exe; pytest started from it
    # with inherited handles exits 1, so every nightly gate reported 2/14 and reverted good work
    (tmp_path / "pythonw.exe").write_text("", encoding="utf-8")
    (tmp_path / "python.exe").write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "pythonw.exe"))
    assert sd._console_python() == str(tmp_path / "python.exe")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))
    assert sd._console_python() == str(tmp_path / "python.exe")
