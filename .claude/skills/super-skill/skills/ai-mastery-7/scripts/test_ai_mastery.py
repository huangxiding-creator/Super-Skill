"""Tests for weekly_retrospective + rationale_mining (ai-mastery-7).

Run: python -m pytest test_ai_mastery.py -q
Or:   python test_ai_mastery.py            # standalone, no pytest needed

Builds a throwaway git repo in a temp dir with a known commit graph, then asserts
both scripts read it back correctly. Fully offline and deterministic.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from weekly_retrospective import (  # noqa: E402
    collect as wr_collect, summarize as wr_summarize, Commit, SCOPE_FILE_THRESHOLD,
    main as wr_main,
)
from rationale_mining import (  # noqa: E402
    history as rm_history, build_report as rm_build_report,
    blame_segments as rm_blame_segments, main as rm_main,
)


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=60, check=True,
    )
    return r.stdout


def _commit(repo: Path, msg: str, paths: list[str], content: str | None = None) -> None:
    for p in paths:
        full = repo / p
        full.parent.mkdir(parents=True, exist_ok=True)
        if content is not None:
            full.write_text(content, encoding="utf-8")
        else:
            full.write_text((full.read_text(encoding="utf-8") if full.exists() else "") + "x\n",
                            encoding="utf-8")
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "--allow-empty", "-m", msg, "--quiet")


def _make_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="aim7_"))
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test Bot")
    _git(repo, "config", "commit.gpgsign", "false")
    return repo


# ---- weekly_retrospective ------------------------------------------------- #

def test_weekly_categorizes_delivered_and_wip():
    repo = _make_repo()
    try:
        _commit(repo, "feat: add login", ["src/login.py"], content="def login():\n    pass\n")
        _commit(repo, "fix: null in token", ["src/login.py"])
        _commit(repo, "wip: drafting cache", ["src/cache.py"], content="# draft\n")

        commits = wr_collect(str(repo), 7, ())
        subjects = {c.subject for c in commits}
        assert "feat: add login" in subjects
        by_cat = {"delivered": [], "in_progress": []}
        for c in commits:
            by_cat.setdefault(c.category, []).append(c)
        assert any("login" in c.subject for c in by_cat["delivered"])
        assert any(c.category == "in_progress" for c in commits)  # the wip commit
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_weekly_scope_signal_flags_large_commit():
    repo = _make_repo()
    try:
        # One commit touching many files → scope signal.
        paths = [f"mod_{i}.py" for i in range(SCOPE_FILE_THRESHOLD + 2)]
        _commit(repo, "feat: big scaffolding", paths,
                content="print('hi')\n")
        commits = wr_collect(str(repo), 7, ())
        big = [c for c in commits if "scaffolding" in c.subject]
        assert big and big[0].is_scope_signal
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_weekly_area_filter_limits_paths():
    repo = _make_repo()
    try:
        _commit(repo, "feat: a", ["src/a.py"], content="a\n")
        _commit(repo, "feat: b", ["tests/b.py"], content="b\n")
        only_src = wr_collect(str(repo), 7, ("src",))
        assert all(c.files == ["src/a.py"] or all(f.startswith("src") for f in c.files)
                   for c in only_src)
        assert any("a" in c.subject for c in only_src)
        assert all("b" in c.subject is False for c in only_src) or \
               not any(c.subject == "feat: b" for c in only_src)
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_weekly_main_emits_json_and_exits_zero():
    repo = _make_repo()
    try:
        _commit(repo, "feat: seed", ["src/app.py"], content="app\n")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = wr_main(["--repo", str(repo), "--since", "7", "--json"])
        assert rc == 0
        import json
        data = json.loads(buf.getvalue())
        assert data["totals"]["commits"] >= 1
        assert "delivered" in data
        assert "by_day" in data
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_weekly_handles_non_ascii_commit_message():
    """Regression: UTF-8 commit messages must not crash the GBK-default subprocess decode."""
    repo = _make_repo()
    try:
        _commit(repo, "feat: 添加中文登录模块 — with em-dash", ["src/auth.py"],
                content="def auth():\n    pass\n")
        commits = wr_collect(str(repo), 7, ())
        assert any("中文登录" in c.subject for c in commits)
        # and the markdown path renders without crashing
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert wr_main(["--repo", str(repo), "--since", "7"]) == 0
        assert "中文登录" in buf.getvalue()
    finally:
        shutil.rmtree(repo, ignore_errors=True)


# ---- rationale_mining ----------------------------------------------------- #

def test_rationale_history_returns_oldest_first():
    repo = _make_repo()
    try:
        _commit(repo, "feat: introduce module", ["src/x.py"], content="v1\n")
        _commit(repo, "refactor: clean module", ["src/x.py"])
        _commit(repo, "fix: edge case", ["src/x.py"])
        changes = rm_history(str(repo), "src/x.py")
        assert len(changes) == 3
        assert changes[0].subject == "feat: introduce module"   # origin first
        assert changes[-1].subject == "fix: edge case"          # most recent last
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_rationale_report_has_origin_and_formative():
    repo = _make_repo()
    try:
        _commit(repo, "feat: seed file", ["auth.py"], content="line\n")
        _commit(repo, "feat: expand a lot", ["auth.py"], content="line\n" * 50)
        report = rm_build_report(str(repo), "auth.py", max_formative=5)
        assert report["total_commits"] == 2
        assert report["origin"]["subject"] == "feat: seed file"
        assert report["formative"][0]["subject"] == "feat: expand a lot"  # biggest churn first
        assert report["recent_drift"][0]["subject"] == "feat: expand a lot"
        assert "segments" in report  # single file → blame ran
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_rationale_segments_cover_whole_file():
    repo = _make_repo()
    try:
        _commit(repo, "feat: three lines", ["f.py"], content="a\nb\nc\n")
        segs = rm_blame_segments(str(repo), "f.py")
        # 3 source lines → one run attributed to the seed commit
        assert segs, "expected at least one blame segment"
        assert segs[0]["start"] == 1
        assert segs[-1]["end"] == 3  # covers all 3 lines
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_rationale_no_history_returns_error_report():
    repo = _make_repo()
    try:
        report = rm_build_report(str(repo), "never_committed.py", 5)
        assert report.get("error")
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_rationale_main_markdown_exits_zero():
    repo = _make_repo()
    try:
        _commit(repo, "feat: a thing", ["thing.py"], content="thing\n")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rm_main(["thing.py", "--repo", str(repo)])
        assert rc == 0
        assert "Rationale timeline" in buf.getvalue()
        assert "Origin" in buf.getvalue()
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_subprocess_stdout_is_valid_utf8_with_chinese():
    """Regression: as a real CLI, stdout bytes must be UTF-8 even on GBK Windows."""
    repo = _make_repo()
    try:
        _commit(repo, "feat: 中文模块 — em-dash here", ["src/z.py"], content="z\n")
        script = str(Path(__file__).parent / "weekly_retrospective.py")
        r = subprocess.run(
            [sys.executable, script, "--repo", str(repo), "--since", "7", "--json"],
            capture_output=True, timeout=60,
        )
        assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
        # The whole point: bytes must decode cleanly as UTF-8 and contain the Chinese.
        text = r.stdout.decode("utf-8")
        assert "中文模块" in text
    finally:
        shutil.rmtree(repo, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
