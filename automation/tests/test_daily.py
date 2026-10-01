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


def test_schedule_time_conversion():
    local_offset = dt.datetime.now().astimezone().utcoffset().total_seconds() / 3600
    assert schedule_daily.local_time_for("23:00", local_offset) == "23:00"
    assert schedule_daily.local_time_for("23:30", local_offset - 1) == "00:30"


# ---------------------------------------------------------------- end to end

FAKE_CLAUDE = r'''
import json, pathlib, sys
prompt = sys.stdin.read()
assert "Today's candidates" in prompt
mode = pathlib.Path("automation/fake_mode.txt").read_text().strip()
out = pathlib.Path("automation/daily_out")
if mode == "nothing":
    print('```json\n{"changed": false, "summary": "nothing new", "adopted": [], "rejected": [{"source": "a/hot", "reason": "dup"}]}\n```')
    sys.exit(0)
(out / "references/patterns").mkdir(parents=True, exist_ok=True)
(out / "references/patterns/demo.md").write_text("# Demo pattern\n", encoding="utf-8")
(out / "hooks").mkdir(exist_ok=True)
(out / "hooks/pre_tool.py").write_text("evil = True\n", encoding="utf-8")
pathlib.Path(".claude/skills/super-skill/SKILL.md").write_text("tampered", encoding="utf-8")
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
    monkeypatch.setenv("SUPERSKILL_GATE_CMD", f"{sys.executable}|-c|pass")
    monkeypatch.setenv("SUPERSKILL_PUSH_LAYERS", "git")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "t")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "t@t")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "t")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "t@t")
    return {"repo": repo, "remote": remote, "skill": skill, "auto": auto}


def _args(repo, **kw):
    ns = argparse.Namespace(repo=str(repo), branch="master", dry_run=False, scan_only=False, no_push=False,
                            no_install=True, budget_usd=1.0, max_turns=5, timeout=120)
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


def test_dry_run_changes_nothing(world):
    (world["auto"] / "fake_mode.txt").write_text("adopt", encoding="utf-8")
    assert sd.run(_args(world["repo"], dry_run=True)) == 0
    assert not (world["skill"] / "references" / "patterns").exists()
    assert not (world["auto"] / "radar_state.json").exists()
    assert (world["auto"] / "daily_out" / "manifest.json").is_file()
