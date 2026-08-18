"""Clash for Windows proxy manager (Super-Skill `clash-proxy` sub-skill).

Manages the Clash proxy required to reach GFW-blocked sites from this machine
(GitHub / HuggingFace / PyPI). Brings the proxy up before a network op and takes
it down after — the We-AIPO "用完即关" (close-after-use) pattern that ships with
this skill.

V4.1.6 adds the **Clash API layer** (from We-AIPO's proxy_mgr/sched_guard, battle-
tested over 290+ commits): instead of only GUI automation, mode switching goes
through the Clash RESTful API — which is faster, silent (no window focus), and
leaves no TUN/DNS residue:

    GET  /version          probe API reachability
    GET  /configs          read current mode (global / rule / direct)
    PATCH /configs         switch mode; `direct` also disables TUN + fake-IP DNS
    PUT  /proxies/GLOBAL   pin the exit node (stable geo — risk-control friendlier)

Contract (documented in ../SKILL.md):
    python clash_proxy.py start             # launch Clash + poll port until ready (<=120s)
    python clash_proxy.py status            # exit 0 if proxy up, 1 if down
    python clash_proxy.py mode              # API diagnostic: base, mode, DNS-hijack check
    python clash_proxy.py global            # API: switch to global (proxy) mode
    python clash_proxy.py direct            # API: switch to direct + TUN/DNS off + flushdns
    python clash_proxy.py stop              # API direct first, then full exit (Ctrl+Q/taskkill)
    python clash_proxy.py push [-m MSG]     # We-AIPO git-push recipe (commit -> proxy -> push
                                            #   -> direct-fallback -> close-after-use)
    python clash_proxy.py run -- <cmd...>   # run a command with HTTP(S)_PROXY set

Windows-focused (Clash for Windows GUI + explorer launch + firewall dialog).
On non-Windows, start/stop are graceful no-ops with a warning; status/run work anywhere.

Config (override without code edits):
    CLASH_EXE    path to Clash for Windows exe
    CLASH_PORT   mixed-port to poll (default 7890)
    CLASH_TEST   URL probed to confirm the proxy actually reaches the open internet
    CLASH_API    explicit Clash API base URL (skips discovery)
    CLASH_SECRET API bearer secret (skips ~/.config/clash/config.yaml discovery)
    CLASH_NODE   default exit node pinned on every `global`/`push` (geo stability)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

DEFAULT_EXE = r"C:\Program Files\Clash for Windows\Clash for Windows.exe"
DEFAULT_PORT = 7890
DEFAULT_TEST_URL = "https://github.com"
START_TIMEOUT = 120          # seconds, matches SKILL.md
POLL_INTERVAL = 2

# --- Clash API (We-AIPO provenance) ---------------------------------------- #
# Port drift is the #1 silent killer: We-AIPO hardcoded 18886 once and every API
# call failed silently (proxy never switched). Discovery order mirrors
# sched_guard.py FIX-0817b/0818n: config.yaml first (it drifts — 11845 -> 25148
# observed), then fixed probe table (CFW GUI 20225, headless core 11845, upstream
# default 9090). Each candidate is probed with a real GET /version.
CLASH_API_PORTS = (20225, 11845, 9090)
CONFIG_YAML = Path.home() / ".config" / "clash" / "config.yaml"
FAKE_IP_PREFIX = "198.18."          # Clash fake-IP range 198.18.0.0/16
CLASH_PROCESS_NAMES = ("clash-win64", "clash-verge", "mihomo",
                       "clash-core-service", "clash for windows")

_api_cache: dict = {}


def _force_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def _exe_path() -> str:
    return os.environ.get("CLASH_EXE") or DEFAULT_EXE


def _port() -> int:
    try:
        return int(os.environ.get("CLASH_PORT") or DEFAULT_PORT)
    except ValueError:
        return DEFAULT_PORT


def _proxy_env(port: Optional[int] = None) -> dict:
    """Env dict with HTTP(S)_PROXY pointed at the local Clash mixed-port."""
    port = _port() if port is None else port
    proxy = f"http://127.0.0.1:{port}"
    return {
        **os.environ,
        "HTTP_PROXY": proxy, "HTTPS_PROXY": proxy,
        "http_proxy": proxy, "https_proxy": proxy,
    }


def status(port: Optional[int] = None, test_url: str = DEFAULT_TEST_URL, timeout: float = 5.0) -> bool:
    """True if the proxy is up AND can reach `test_url` through it.

    This is the ground truth — a live Clash process whose port is closed still
    returns False, which is exactly what callers need to decide. We-AIPO lesson:
    never trust port-open alone; only a real request through 127.0.0.1:7890 counts.
    """
    port = _port() if port is None else port
    handler = urllib.request.ProxyHandler({
        "http": f"http://127.0.0.1:{port}",
        "https": f"http://127.0.0.1:{port}",
    })
    opener = urllib.request.build_opener(handler)
    try:
        resp = opener.open(test_url, timeout=timeout)
        resp.read(64)  # touch the body so a 200 with empty read still counts
        return True
    except Exception:
        return False


def is_running() -> bool:
    """True if any known Clash core/GUI process is running (Windows only)."""
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        ).lower()
        return any(name in out for name in CLASH_PROCESS_NAMES)
    except Exception:
        return False


# --- Clash REST API layer (We-AIPO proxy_mgr / sched_guard) ------------------ #

def _config_yaml_settings() -> Tuple[List[int], str]:
    """Parse (api_ports, secret) from ~/.config/clash/config.yaml.

    Returns ([], "") when the file is missing or unreadable — callers fall back
    to the fixed probe table / empty secret. Ports drift between Clash runs, so
    the config file is the most current source (We-AIPO FIX-0818n).
    """
    ports: List[int] = []
    secret = ""
    try:
        text = CONFIG_YAML.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"external-controller:\s*127\.0\.0\.1:(\d+)", text)
        if m:
            ports.append(int(m.group(1)))
        m = re.search(r"^secret:\s*[\"']?(\S+?)[\"']?\s*$", text, re.MULTILINE)
        if m:
            secret = m.group(1)
    except Exception:
        pass
    return ports, secret


def _probe_version(base: str, secret: str, timeout: float = 2.0) -> bool:
    """GET <base>/version == 200 -> the Clash API is alive there."""
    req = urllib.request.Request(f"{base}/version")
    if secret:
        req.add_header("Authorization", f"Bearer {secret}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def api_base() -> str:
    """Discover the Clash API base URL. Order: CLASH_API env > config.yaml port >
    fixed probe table (20225, 11845, 9090). Success is cached; failure falls back
    to the first probe-table port so callers can treat it as unreachable."""
    explicit = os.environ.get("CLASH_API")
    if explicit:
        return explicit.rstrip("/")
    if _api_cache.get("base"):
        return _api_cache["base"]
    secret = api_secret()
    for port in _config_yaml_settings()[0] + list(CLASH_API_PORTS):
        base = f"http://127.0.0.1:{port}"
        if _probe_version(base, secret):
            _api_cache["base"] = base
            return base
    return f"http://127.0.0.1:{CLASH_API_PORTS[0]}"


def api_secret() -> str:
    """API bearer secret: CLASH_SECRET env > config.yaml > "" (no auth)."""
    explicit = os.environ.get("CLASH_SECRET")
    if explicit:
        return explicit
    if _api_cache.get("secret") is None:
        _api_cache["secret"] = _config_yaml_settings()[1]
    return _api_cache["secret"]


def _api(method: str, path: str, payload: Optional[dict] = None,
         timeout: float = 5.0) -> Tuple[int, str]:
    """Call the Clash REST API. Returns (status, body). HTTP errors map to their
    status code; network errors raise (callers catch)."""
    req = urllib.request.Request(api_base() + path, method=method)
    secret = api_secret()
    if secret:
        req.add_header("Authorization", f"Bearer {secret}")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]


def api_reachable() -> bool:
    try:
        code, _ = _api("GET", "/version", timeout=2.0)
        return code == 200
    except Exception:
        return False


def get_mode() -> Optional[str]:
    """Current Clash mode ("global" / "rule" / "direct"), or None if the API is
    unreachable (We-AIPO sched_guard semantics: None = don't guess)."""
    try:
        code, body = _api("GET", "/configs")
        if code == 200:
            return json.loads(body).get("mode")
    except Exception:
        pass
    return None


def set_mode(mode: str, tun: bool = False) -> bool:
    """Switch Clash mode via PATCH /configs.

    - "global": proxy mode. TUN is OFF by default — traffic must opt in via
      explicit proxy env (safer: no DNS hijack of domestic traffic). Pass
      tun=True for whole-system capture (We-AIPO sched_guard behaviour).
    - "direct": everything direct; also disables TUN and fake-IP DNS so no
      residue survives the switch (We-AIPO 2026-08-07 lesson: killing/leaving
      Clash in TUN mode poisons DNS with 198.18.x.x fake-IPs).
    """
    payload: dict = {"mode": mode}
    if mode == "global" and tun:
        payload["tun"] = {"enable": True}
    if mode == "direct":
        payload["tun"] = {"enable": False}
        payload["dns"] = {"enable": False}
    try:
        code, _ = _api("PATCH", "/configs", payload)
        return code in (200, 204)
    except Exception:
        return False


def pin_node(node: Optional[str] = None) -> bool:
    """Pin the GLOBAL exit node via PUT /proxies/GLOBAL.

    We-AIPO FIX-0818p: exit-country drift across runs is a risk-control trigger
    for Google-class services; re-pin on every switch. Node comes from `node` or
    CLASH_NODE; when neither is set this is a no-op (returns False, no API call).
    """
    node = node or os.environ.get("CLASH_NODE")
    if not node:
        return False
    try:
        code, _ = _api("PUT", "/proxies/GLOBAL", {"name": node})
        return code in (200, 204)
    except Exception:
        return False


def flush_dns() -> bool:
    """ipconfig /flushdns — clear fake-IP records left by Clash TUN DNS."""
    if sys.platform != "win32":
        return False
    try:
        r = subprocess.run(["ipconfig", "/flushdns"],
                           capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def dns_hijacked(domain: str = "github.com") -> bool:
    """True if `domain` resolves into the Clash fake-IP range (198.18.0.0/16) —
    i.e. Clash TUN DNS is still capturing traffic it shouldn't."""
    if sys.platform != "win32":
        return False
    try:
        r = subprocess.run(["nslookup", domain], capture_output=True, text=True,
                           timeout=3, encoding="utf-8", errors="replace")
        return FAKE_IP_PREFIX in (r.stdout or "")
    except Exception:
        return False


def _system_proxy_off() -> None:
    """Best-effort: clear the WinINET system proxy (ProxyEnable=0). Belt and
    braces beside mode switching — We-AIPO proxy_off does the same."""
    if sys.platform != "win32":
        return
    try:  # pragma: no cover - registry-dependent
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
    except Exception:
        return


def release() -> bool:
    """Restore direct connectivity but LEAVE Clash running (We-AIPO W18
    NetworkOrchestrator pattern): direct mode + TUN/DNS off + system proxy off +
    flushdns. Cheaper than a full stop and avoids TUN/DNS churn between repeated
    proxy sessions; use `stop()` when the proxy won't be needed again."""
    ok = set_mode("direct")
    _system_proxy_off()
    flush_dns()
    return ok


def start(exe_path: Optional[str] = None, port: Optional[int] = None,
          timeout: float = START_TIMEOUT, handle_firewall: bool = True) -> bool:
    """Launch Clash (if down) and poll until the proxy is ready. Returns True if up."""
    port = _port() if port is None else port
    if status(port):
        return True
    exe = exe_path or _exe_path()
    if sys.platform != "win32":
        print("clash_proxy: start is Windows-only (Clash for Windows GUI); "
              "start Clash manually on this platform.", file=sys.stderr)
        # still poll — the user may bring it up themselves
    else:
        if not os.path.isfile(exe):
            print(f"clash_proxy: Clash exe not found: {exe} (set CLASH_EXE)", file=sys.stderr)
            return False
        try:
            # explorer.exe launch so the Electron GUI initializes its singleton + tray
            subprocess.Popen(["explorer.exe", exe], close_fds=True)
        except Exception as e:  # pragma: no cover - environment-dependent
            print(f"clash_proxy: launch failed: {e}", file=sys.stderr)
            return False

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        if status(port):
            if handle_firewall:
                _dismiss_firewall_dialog()
            return True
    return False


def _dismiss_firewall_dialog() -> None:
    """Best-effort: if the Windows firewall '#32770' dialog is up, click its
    允许访问 / Allow access button once. Never raises — this is a convenience,
    not a guarantee. Matches the SKILL.md "精确点击一次，不乱点" rule.
    """
    if sys.platform != "win32":
        return
    try:  # pragma: no cover - GUI-dependent, no live assertion
        import ctypes
        user32 = ctypes.windll.user32

        # Walk top-level windows; find a #32770 dialog owned by this session.
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        found = []

        def _enum(hwnd, _lparam):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value == "#32770" and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
            return True

        user32.EnumWindows(EnumWindowsProc(_enum), 0)
        if not found:
            return

        targets = ["允许访问", "allow access", "允许", "allow"]
        for hwnd in found:
            # Enumerate child buttons; click the first whose text matches.
            btns = []

            def _enum_child(h, _l):
                cls = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(h, cls, 64)
                if cls.value == "Button":
                    txt = ctypes.create_unicode_buffer(256)
                    user32.GetWindowTextW(h, txt, 256)
                    btns.append((h, txt.value.lower()))
                return True

            user32.EnumChildWindows(hwnd, EnumWindowsProc(_enum_child), 0)
            for h, txt in btns:
                if any(t in txt for t in targets):
                    user32.SendMessageW(h, 0x00F5, 0, 0)  # BM_CLICK
                    return
    except Exception:
        return  # never let firewall dismissal affect the proxy flow


def _gui_quit() -> bool:
    """Graceful GUI exit: focus the Clash window and send Ctrl+Q (Electron quit)."""
    if sys.platform != "win32":
        return False
    try:  # pragma: no cover - GUI-dependent
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Clash for Windows")
        if not hwnd:
            return False
        user32.ShowWindow(hwnd, 9)            # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        VK_CONTROL, VK_Q, KEYUP = 0x11, 0x51, 0x0002
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_Q, 0, 0, 0)
        user32.keybd_event(VK_Q, 0, KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYUP, 0)
        return True
    except Exception:
        return False


def stop() -> bool:
    """Full exit (We-AIPO exit_clash recipe). Order matters:

    1. API switch to direct FIRST — even if the kill later fails, no TUN/DNS
       residue survives (2026-08-07 lesson: killing Clash mid-TUN poisons DNS).
    2. Clear system proxy; graceful Ctrl+Q GUI quit.
    3. taskkill fallback: WM_CLOSE first, then /F only for residue. Clash runs
       as the current user at normal integrity, so no UAC prompt (the old
       "never taskkill" rule targeted elevated targets; API-direct-first makes
       even a forced kill safe).
    4. Best-effort `sc stop "Clash Core Service"`; flushdns; verify.

    Returns True when no Clash process remains.
    """
    if sys.platform != "win32":
        return False
    set_mode("direct")
    _system_proxy_off()
    _gui_quit()
    time.sleep(2)
    if is_running():
        subprocess.run(["taskkill", "/IM", "clash-win64.exe"],
                       capture_output=True, timeout=10)
        time.sleep(1)
        if is_running():
            subprocess.run(["taskkill", "/F", "/IM", "clash-win64.exe"],
                           capture_output=True, timeout=10)
            time.sleep(1)
    try:  # best-effort; the service may not exist or need elevation
        subprocess.run(["sc", "stop", "Clash Core Service"],
                       capture_output=True, timeout=10)
    except Exception:
        pass
    flush_dns()
    return not is_running()


def run_with_proxy(cmd: Iterable[str], port: Optional[int] = None,
                   close_after: bool = False) -> subprocess.CompletedProcess:
    """Run `cmd` with HTTP_PROXY/HTTPS_PROXY pointed at Clash.

    If `close_after` is True (the We-AIPO 用完即关 pattern), the proxy is stopped
    after the command finishes — useful for one-shot pushes like git push.
    """
    port = _port() if port is None else port
    try:
        result = subprocess.run(list(cmd), env=_proxy_env(port),
                                capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
    finally:
        if close_after:
            stop()
    # Re-emit so the caller sees normal output when run from a shell
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result


# --- push (We-AIPO scripts/push_github.py recipe) ---------------------------- #

def _git(repo: str, *args: str, timeout: float = 60.0,
         env: Optional[dict] = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, env=env)


def push(message: Optional[str] = None, repo_root: Optional[str] = None,
         branch: Optional[str] = None, keep: bool = False,
         timeout: float = 120.0) -> int:
    """Safe GitHub push through Clash, closing it after (用完即关).

    We-AIPO-proven sequence (scripts/push_github.py):
      1. optional `git add -A && git commit -m <message>`
      2. show unpushed commits (`git log @{u}..HEAD`); bail out if none
      3. bring the proxy up (start if needed), API-switch to global + pin node
      4. `git push` with proxy env (120s timeout)
      5. on failure: one direct push retry with proxy overridden to empty
      6. close: `stop()` (full exit) or `release()` with --keep (direct mode,
         Clash stays running — W18 pattern for repeated sessions)

    Returns the final git exit code (0 = pushed), or 1/2 for our own failures.
    """
    repo = repo_root or os.getcwd()
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"clash_proxy push: not a git repository: {repo}", file=sys.stderr)
        return 2

    if message:
        _git(repo, "add", "-A")
        r = _git(repo, "commit", "-m", message)
        if r.returncode == 0:
            print(f"  committed: {message[:60]}")
        else:
            print(f"  commit: {(r.stdout or r.stderr).strip()[:80]}")

    r = _git(repo, "log", "@{u}..HEAD", "--oneline")
    if r.returncode == 0:
        lines = [l for l in (r.stdout or "").splitlines() if l.strip()]
        if not lines:
            print("clash_proxy push: nothing to push")
            return 0
        print(f"=== {len(lines)} commit(s) to push ===")
        for line in lines:
            print(f"  {line[:70]}")

    if not status():
        if not start():
            print("clash_proxy push: proxy unavailable (start failed)", file=sys.stderr)
            return 1

    api_ok = api_reachable()
    if api_ok:
        if set_mode("global"):
            print("  Clash API: global mode on")
        pin_node()
    else:
        print("  Clash API unreachable — pushing through port 7890 anyway")

    push_args: List[str] = ["push"] + (["origin", branch] if branch else [])
    rc = 1
    try:
        r = _git(repo, *push_args, timeout=timeout, env=_proxy_env())
        rc = r.returncode
        if rc == 0:
            print("  PUSH OK")
        else:
            print(f"  push failed: {(r.stderr or '').strip()[:120]}")
            print("  trying direct...")
            try:
                r2 = _git(repo, "-c", "http.proxy=", "-c", "https.proxy=",
                          *push_args, timeout=60.0)
                if r2.returncode == 0:
                    print("  DIRECT PUSH OK")
                    rc = 0
                else:
                    print(f"  direct also failed: {(r2.stderr or '').strip()[:120]}")
            except subprocess.TimeoutExpired:
                print("  direct push timed out", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("  push timed out", file=sys.stderr)
    finally:
        if keep:
            release()
            print("=== Clash left running in direct mode (release) ===")
        else:
            stop()
            print("=== Clash closed (用完即关) ===")
    return rc


def main(argv: Optional[List[str]] = None) -> int:
    _force_utf8_stdout()
    p = argparse.ArgumentParser(description="Clash for Windows proxy manager.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_start = sub.add_parser("start", help="launch Clash and poll until the proxy is ready")
    sp_start.add_argument("--timeout", type=float, default=START_TIMEOUT)

    sub.add_parser("status", help="exit 0 if proxy is up, 1 otherwise")

    sp_mode = sub.add_parser("mode", help="Clash API diagnostic (base, mode, DNS check)")
    sp_mode.add_argument("--json", action="store_true", help="emit JSON")

    sub.add_parser("global", help="API: switch to global (proxy) mode")
    sub.add_parser("direct", help="API: direct mode + TUN/DNS off + flushdns (Clash keeps running)")
    sub.add_parser("stop", help="full exit: API direct first, then Ctrl+Q / taskkill")

    sp_push = sub.add_parser("push", help="We-AIPO git-push recipe: commit -> proxy -> push -> close")
    sp_push.add_argument("-m", "--message", help="commit this message first (git add -A)")
    sp_push.add_argument("--repo-root", default=None, help="repo directory (default: cwd)")
    sp_push.add_argument("--branch", default=None, help="push origin <branch> instead of the upstream default")
    sp_push.add_argument("--keep", action="store_true",
                         help="leave Clash running in direct mode after (W18 pattern)")
    sp_push.add_argument("--timeout", type=float, default=120.0)

    sp_run = sub.add_parser("run", help="run a command through the proxy")
    sp_run.add_argument("--close-after", action="store_true",
                        help="stop the proxy after the command finishes (用完即关)")
    sp_run.add_argument("command", nargs=argparse.REMAINDER, help="command to run (use -- first)")

    args = p.parse_args(argv)

    if args.cmd == "status":
        return 0 if status() else 1
    if args.cmd == "start":
        return 0 if start(timeout=args.timeout) else 1
    if args.cmd == "mode":
        info = {
            "api_base": api_base(),
            "api_reachable": api_reachable(),
            "mode": get_mode(),
            "proxy_port_up": status(),
            "dns_hijacked": dns_hijacked(),
            "clash_running": is_running(),
        }
        if args.json:
            print(json.dumps(info, ensure_ascii=False))
        else:
            for k, v in info.items():
                print(f"  {k}: {v}")
        return 0
    if args.cmd == "global":
        ok = set_mode("global")
        pin_node()
        print(f"clash_proxy: global mode {'on' if ok else 'FAILED (API unreachable?)'}")
        return 0 if ok else 1
    if args.cmd == "direct":
        ok = release()
        print(f"clash_proxy: direct mode {'restored' if ok else 'FAILED (API unreachable?)'}")
        return 0 if ok else 1
    if args.cmd == "stop":
        return 0 if stop() else 1
    if args.cmd == "push":
        return push(message=args.message, repo_root=args.repo_root,
                    branch=args.branch, keep=args.keep, timeout=args.timeout)
    if args.cmd == "run":
        cmd = args.command or []
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            print("clash_proxy: `run` needs a command", file=sys.stderr)
            return 2
        r = run_with_proxy(cmd, close_after=args.close_after)
        return r.returncode
    return 2  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())
