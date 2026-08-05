"""Tests for clash_proxy. Run: python -m pytest test_clash_proxy.py -q

Only exercises the deterministic, side-effect-free logic. The GUI-dependent
paths (start/stop/_dismiss_firewall_dialog) launch or focus the real Clash UI
and are intentionally NOT exercised here — they're marked `# pragma: no cover`.
"""
import os
import subprocess
import sys
import traceback
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import clash_proxy as cp  # noqa: E402


# ---- status() ------------------------------------------------------------- #

def test_status_false_on_dead_port(monkeypatch=None):
    # A port nothing is listening on refuses fast → status False.
    assert cp.status(port=1, timeout=2.0) is False


def test_status_true_when_opener_succeeds(monkeypatch=None):
    """status() returns True iff the opener's request completes."""
    class _FakeResp:
        def read(self, n=-1):
            return b"x" * max(1, n if isinstance(n, int) and n > 0 else 1)
    class _FakeOpener:
        last_handler = None
        def __init__(self, handler):
            type(self).last_handler = handler
        def open(self, url, timeout=None):
            return _FakeResp()
    real_build = cp.urllib.request.build_opener
    cp.urllib.request.build_opener = _FakeOpener
    try:
        assert cp.status(port=7890, timeout=1.0) is True
    finally:
        cp.urllib.request.build_opener = real_build


# ---- config resolution ---------------------------------------------------- #

def test_port_env_override(monkeypatch=None):
    os.environ["CLASH_PORT"] = "9999"
    try:
        assert cp._port() == 9999
    finally:
        os.environ.pop("CLASH_PORT", None)
    assert cp._port() == cp.DEFAULT_PORT


def test_port_invalid_env_falls_back(monkeypatch=None):
    os.environ["CLASH_PORT"] = "not-an-int"
    try:
        assert cp._port() == cp.DEFAULT_PORT
    finally:
        os.environ.pop("CLASH_PORT", None)


def test_exe_env_override(monkeypatch=None):
    os.environ["CLASH_EXE"] = "/some/where/clash.exe"
    try:
        assert cp._exe_path() == "/some/where/clash.exe"
    finally:
        os.environ.pop("CLASH_EXE", None)
    assert cp._exe_path() == cp.DEFAULT_EXE


# ---- run_with_proxy() ----------------------------------------------------- #

def test_run_with_proxy_injects_env():
    # Run a python one-liner that prints HTTPS_PROXY; it must see the proxy URL.
    r = cp.run_with_proxy([sys.executable, "-c",
                           "import os; print(os.environ.get('HTTPS_PROXY',''))"],
                          port=7890)
    assert r.returncode == 0
    assert "http://127.0.0.1:7890" in r.stdout


def test_run_with_proxy_port_override():
    r = cp.run_with_proxy([sys.executable, "-c",
                           "import os; print(os.environ.get('HTTP_PROXY',''))"],
                          port=8421)
    assert r.returncode == 0
    assert "http://127.0.0.1:8421" in r.stdout


# ---- main() / argparse ---------------------------------------------------- #

def test_main_status_exits_nonzero_when_down(monkeypatch=None):
    # Force status() to report down regardless of real network.
    real = cp.status
    cp.status = lambda *a, **k: False
    try:
        rc = cp.main(["status"])
    finally:
        cp.status = real
    assert rc == 1


def test_main_status_exits_zero_when_up(monkeypatch=None):
    real = cp.status
    cp.status = lambda *a, **k: True
    try:
        rc = cp.main(["status"])
    finally:
        cp.status = real
    assert rc == 0


def test_main_run_executes_command_through_proxy():
    rc = cp.main(["run", "--", sys.executable, "-c",
                  "import os; assert os.environ['HTTPS_PROXY'].startswith('http'), os.environ['HTTPS_PROXY']"])
    assert rc == 0


def test_main_run_requires_command():
    rc = cp.main(["run", "--"])
    assert rc == 2


# ---- cross-platform guards ----------------------------------------------- #

def test_is_running_returns_bool_without_raising():
    # Must not raise regardless of platform; on non-Windows returns False.
    assert isinstance(cp.is_running(), bool)


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
