"""Tests for clash_proxy. Run: python -m pytest test_clash_proxy.py -q
(or standalone: python test_clash_proxy.py)

Only exercises the deterministic, side-effect-free logic. The GUI-dependent
paths (start/stop/_dismiss_firewall_dialog/_gui_quit) launch or focus the real
Clash UI and are intentionally NOT exercised here — they're marked
`# pragma: no cover`.

V4.1.6 adds the Clash API layer (We-AIPO provenance): config.yaml discovery,
mode-switch payloads, node pinning, and the `push` git recipe.
"""
import os
import subprocess
import sys
import traceback
import pathlib
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import clash_proxy as cp  # noqa: E402


# ---- status() ------------------------------------------------------------- #

def test_status_false_on_dead_port(monkeypatch=None):
    # A port nothing is listening on refuses fast -> status False.
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


# ---- Clash API: config.yaml discovery -------------------------------------- #

def test_config_yaml_settings_parsed():
    """external-controller port + secret are read from the Clash config."""
    fake_secret = "00000000-test-0000-not-0000-a-real-secret"
    with tempfile.TemporaryDirectory() as tmp:
        cfg = pathlib.Path(tmp) / "config.yaml"
        cfg.write_text(
            "mixed-port: 7890\n"
            "external-controller: 127.0.0.1:25148\n"
            f'secret: "{fake_secret}"\n',
            encoding="utf-8")
        real_cfg = cp.CONFIG_YAML
        cp.CONFIG_YAML = cfg
        try:
            ports, secret = cp._config_yaml_settings()
            assert ports == [25148]
            assert secret == fake_secret
        finally:
            cp.CONFIG_YAML = real_cfg


def test_config_yaml_missing_is_safe():
    real_cfg = cp.CONFIG_YAML
    cp.CONFIG_YAML = pathlib.Path(tempfile.gettempdir()) / "no-such-clash-cfg.yaml"
    try:
        assert cp._config_yaml_settings() == ([], "")
    finally:
        cp.CONFIG_YAML = real_cfg


def test_api_secret_env_override():
    os.environ["CLASH_SECRET"] = "tok-123"
    try:
        assert cp.api_secret() == "tok-123"
    finally:
        os.environ.pop("CLASH_SECRET", None)


def test_api_base_env_override_skips_discovery():
    os.environ["CLASH_API"] = "http://10.0.0.5:9090/"
    try:
        assert cp.api_base() == "http://10.0.0.5:9090"  # trailing slash stripped
    finally:
        os.environ.pop("CLASH_API", None)


def test_api_base_probes_config_port_then_table_with_cache():
    """Discovery order: config.yaml port first, then the fixed table; first live
    port wins and is cached."""
    calls = []
    def fake_probe(base, secret, timeout=2.0):
        calls.append(base)
        return base.endswith(":25148")          # only the config port is alive
    real_probe, real_settings, cache = cp._probe_version, cp._config_yaml_settings, dict(cp._api_cache)
    cp._probe_version = fake_probe
    cp._config_yaml_settings = lambda: ([25148], "s")
    cp._api_cache.clear()
    try:
        assert cp.api_base() == "http://127.0.0.1:25148"
        assert cp.api_base() == "http://127.0.0.1:25148"   # cached, no re-probe
        assert len(calls) == 1
    finally:
        cp._probe_version, cp._config_yaml_settings = real_probe, real_settings
        cp._api_cache.clear(); cp._api_cache.update(cache)


def test_api_base_falls_back_to_default_when_all_down():
    real_probe, real_settings, cache = cp._probe_version, cp._config_yaml_settings, dict(cp._api_cache)
    cp._probe_version = lambda base, secret, timeout=2.0: False
    cp._config_yaml_settings = lambda: ([], "")
    cp._api_cache.clear()
    try:
        assert cp.api_base() == f"http://127.0.0.1:{cp.CLASH_API_PORTS[0]}"
    finally:
        cp._probe_version, cp._config_yaml_settings = real_probe, real_settings
        cp._api_cache.clear(); cp._api_cache.update(cache)


# ---- Clash API: mode switching --------------------------------------------- #

class _ApiRecorder:
    """Replace cp._api with a recorder returning scripted results."""
    def __init__(self, default=(204, "")):
        self.calls = []
        self.default = default
    def __call__(self, method, path, payload=None, timeout=5.0):
        self.calls.append((method, path, payload))
        return self.default


def test_set_mode_direct_disables_tun_and_dns():
    rec = _ApiRecorder()
    real = cp._api
    cp._api = rec
    try:
        assert cp.set_mode("direct") is True
    finally:
        cp._api = real
    assert rec.calls == [("PATCH", "/configs",
                          {"mode": "direct", "tun": {"enable": False},
                           "dns": {"enable": False}})]


def test_set_mode_global_defaults_to_no_tun():
    """Explicit-proxy mode by default — TUN must be opt-in (no DNS hijack)."""
    rec = _ApiRecorder()
    real = cp._api
    cp._api = rec
    try:
        assert cp.set_mode("global") is True
    finally:
        cp._api = real
    assert rec.calls == [("PATCH", "/configs", {"mode": "global"})]


def test_set_mode_global_tun_opt_in():
    rec = _ApiRecorder()
    real = cp._api
    cp._api = rec
    try:
        assert cp.set_mode("global", tun=True) is True
    finally:
        cp._api = real
    assert rec.calls == [("PATCH", "/configs",
                          {"mode": "global", "tun": {"enable": True}})]


def test_set_mode_false_on_http_error_and_network_error():
    real = cp._api
    try:
        cp._api = lambda *a, **k: (500, "nope")
        assert cp.set_mode("global") is False
        def _boom(*a, **k):
            raise OSError("refused")
        cp._api = _boom
        assert cp.set_mode("direct") is False
    finally:
        cp._api = real


def test_get_mode_parses_configs_and_none_when_unreachable():
    real = cp._api
    try:
        cp._api = lambda *a, **k: (200, '{"mode": "rule"}')
        assert cp.get_mode() == "rule"
        cp._api = lambda *a, **k: (500, "err")
        assert cp.get_mode() is None
        def _boom(*a, **k):
            raise OSError("down")
        cp._api = _boom
        assert cp.get_mode() is None
    finally:
        cp._api = real


def test_pin_node_noop_without_config():
    rec = _ApiRecorder()
    real_api, has_node = cp._api, os.environ.pop("CLASH_NODE", None)
    cp._api = rec
    try:
        assert cp.pin_node() is False
    finally:
        cp._api = real_api
        if has_node is not None:
            os.environ["CLASH_NODE"] = has_node
    assert rec.calls == []          # no API call when nothing to pin


def test_pin_node_puts_global_selector():
    rec = _ApiRecorder()
    real_api, has_node = cp._api, os.environ.pop("CLASH_NODE", None)
    cp._api = rec
    os.environ["CLASH_NODE"] = "\U0001f1ef\U0001f1f5 JP 01"
    try:
        assert cp.pin_node() is True
    finally:
        cp._api = real_api
        if has_node is None:
            os.environ.pop("CLASH_NODE", None)
        else:
            os.environ["CLASH_NODE"] = has_node
    assert rec.calls == [("PUT", "/proxies/GLOBAL", {"name": "\U0001f1ef\U0001f1f5 JP 01"})]


# ---- Clash API: diagnostics ------------------------------------------------- #

def test_dns_hijacked_detects_fake_ip():
    class _R:
        returncode = 0
        stdout = "Name: github.com\nAddresses: 198.18.0.5\n"
        stderr = ""
    real_run = cp.subprocess.run
    cp.subprocess.run = lambda *a, **k: _R()
    try:
        assert cp.dns_hijacked() is True
    finally:
        cp.subprocess.run = real_run


def test_dns_hijacked_clean_when_real_ip():
    class _R:
        returncode = 0
        stdout = "Addresses: 20.205.243.166\n"
        stderr = ""
    real_run = cp.subprocess.run
    cp.subprocess.run = lambda *a, **k: _R()
    try:
        assert cp.dns_hijacked() is False
    finally:
        cp.subprocess.run = real_run


def test_release_switches_direct_without_killing():
    """W18 pattern: release() only switches mode — Clash process stays alive."""
    seen = []
    real = (cp.set_mode, cp._system_proxy_off, cp.flush_dns)
    cp.set_mode = lambda m, tun=False: seen.append(("mode", m)) or True
    cp._system_proxy_off = lambda: seen.append(("sysproxy",))
    cp.flush_dns = lambda: seen.append(("dns",)) or True
    try:
        assert cp.release() is True
    finally:
        cp.set_mode, cp._system_proxy_off, cp.flush_dns = real
    assert ("mode", "direct") in seen and ("dns",) in seen


# ---- push (We-AIPO recipe) -------------------------------------------------- #

class _GitRecorder:
    """Stub cp._git. Behaviour per subcommand:
    - log @{u}..HEAD  -> `log_out` (rc 0)
    - commit          -> rc 0
    - push (no -c)    -> `push_rc` for the proxied attempt
    - push (with -c)  -> `direct_rc` for the empty-proxy fallback
    """
    def __init__(self, log_out="", push_rc=0, direct_rc=0):
        self.calls = []
        self.log_out, self.push_rc, self.direct_rc = log_out, push_rc, direct_rc

    def __call__(self, repo, *args, timeout=60.0, env=None):
        self.calls.append((args, env))
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        r = _R()
        if args[:1] == ("log",):
            r.stdout = self.log_out
        elif "push" in args:
            if "-c" in args:                       # direct fallback attempt
                r.returncode = self.direct_rc
                r.stderr = "" if self.direct_rc == 0 else "direct fail"
            else:                                  # proxied attempt
                r.returncode = self.push_rc
                r.stderr = "" if self.push_rc == 0 else "Recv failure"
        elif args[:1] == ("commit",):
            r.stdout = "[master abc123] msg"
        return r


def _patch_push_env(rec_git, status=True, api_ok=True):
    """Monkeypatch everything push() touches besides _git; restore dict."""
    real = {"_git": cp._git, "status": cp.status, "start": cp.start,
            "api_reachable": cp.api_reachable, "set_mode": cp.set_mode,
            "pin_node": cp.pin_node, "stop": cp.stop, "release": cp.release}
    cp._git = rec_git
    cp.status = lambda *a, **k: status
    cp.start = lambda *a, **k: True
    cp.api_reachable = lambda: api_ok
    cp.set_mode = lambda m, tun=False: True
    cp.pin_node = lambda node=None: False
    cp.stop = lambda: True
    cp.release = lambda: True
    return real


def _restore_push_env(real):
    for k, v in real.items():
        setattr(cp, k, v)


def test_push_requires_git_repo():
    with tempfile.TemporaryDirectory() as tmp:
        assert cp.push(repo_root=tmp) == 2


def test_push_nothing_to_push_returns_zero():
    rec = _GitRecorder(log_out="")                 # no unpushed commits
    real = _patch_push_env(rec)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / ".git").mkdir()
            assert cp.push(repo_root=tmp) == 0
    finally:
        _restore_push_env(real)
    assert not any("push" in args for args, _ in rec.calls)   # never pushed


def test_push_commits_pushes_and_closes():
    rec = _GitRecorder(log_out="abc123 fix\nabc124 feat\n", push_rc=0)
    real = _patch_push_env(rec)
    stopped = []
    cp.stop = lambda: stopped.append(True) or True
    try:
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / ".git").mkdir()
            rc = cp.push(message="ship it", repo_root=tmp)
    finally:
        _restore_push_env(real)
    assert rc == 0
    subcommands = [args[0] for args, _ in rec.calls]
    assert "add" in subcommands and "commit" in subcommands
    proxied = [env for args, env in rec.calls if "push" in args and "-c" not in args]
    assert proxied and proxied[0]["HTTPS_PROXY"].startswith("http://127.0.0.1:")
    assert stopped == [True]                       # close-after-use (stop, not release)


def test_push_direct_fallback_when_proxied_push_fails():
    rec = _GitRecorder(log_out="abc123 fix\n", push_rc=1, direct_rc=0)
    real = _patch_push_env(rec)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / ".git").mkdir()
            assert cp.push(repo_root=tmp) == 0
    finally:
        _restore_push_env(real)
    proxied = [args for args, _ in rec.calls if "push" in args and "-c" not in args]
    direct = [args for args, _ in rec.calls if "push" in args and "-c" in args]
    assert len(proxied) == 1 and len(direct) == 1
    # The fallback must override the proxy to empty, before the subcommand.
    d = direct[0]
    assert d[d.index("-c") + 1] == "http.proxy="


def test_push_keep_releases_instead_of_stop():
    rec = _GitRecorder(log_out="abc123 fix\n", push_rc=0)
    real = _patch_push_env(rec)
    released, stopped = [], []
    cp.release = lambda: released.append(True) or True
    cp.stop = lambda: stopped.append(True) or True
    try:
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / ".git").mkdir()
            assert cp.push(repo_root=tmp, keep=True) == 0
    finally:
        _restore_push_env(real)
    assert released == [True] and stopped == []


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


def test_main_mode_reports_diagnostics(monkeypatch=None):
    real = (cp.api_reachable, cp.get_mode, cp.status,
            cp.dns_hijacked, cp.is_running)
    cp.api_reachable = lambda: True
    cp.get_mode = lambda: "rule"
    cp.status = lambda *a, **k: True
    cp.dns_hijacked = lambda domain="github.com": False
    cp.is_running = lambda: True
    try:
        rc = cp.main(["mode", "--json"])
    finally:
        (cp.api_reachable, cp.get_mode, cp.status,
         cp.dns_hijacked, cp.is_running) = real
    assert rc == 0


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
