"""Clash for Windows proxy manager (Super-Skill `clash-proxy` sub-skill).

Manages the Clash proxy required to reach GFW-blocked sites from this machine
(GitHub / HuggingFace / PyPI). Brings the proxy up before a network op and takes
it down after — the We-AIPO "用完即关" (close-after-use) pattern that ships with
this skill.

Contract (documented in ../SKILL.md):
    python clash_proxy.py start             # launch Clash + poll port until ready (<=120s)
    python clash_proxy.py status            # exit 0 if proxy up, 1 if down
    python clash_proxy.py stop              # clean GUI exit (Ctrl+Q); NEVER taskkill (UAC)
    python clash_proxy.py run -- <cmd...>   # run a command with HTTP(S)_PROXY set

Windows-focused (Clash for Windows GUI + explorer launch + firewall dialog).
On non-Windows, start/stop are graceful no-ops with a warning; status/run work anywhere.

Config (override without code edits):
    CLASH_EXE   path to Clash for Windows exe
    CLASH_PORT  mixed-port to poll (default 7890)
    CLASH_TEST  URL probed to confirm the proxy actually reaches the open internet
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from typing import Iterable, List, Optional

DEFAULT_EXE = r"C:\Program Files\Clash for Windows\Clash for Windows.exe"
DEFAULT_PORT = 7890
DEFAULT_TEST_URL = "https://github.com"
START_TIMEOUT = 120          # seconds, matches SKILL.md
POLL_INTERVAL = 2


def _exe_path() -> str:
    return os.environ.get("CLASH_EXE") or DEFAULT_EXE


def _port() -> int:
    try:
        return int(os.environ.get("CLASH_PORT") or DEFAULT_PORT)
    except ValueError:
        return DEFAULT_PORT


def status(port: Optional[int] = None, test_url: str = DEFAULT_TEST_URL, timeout: float = 5.0) -> bool:
    """True if the proxy is up AND can reach `test_url` through it.

    This is the ground truth — a live Clash process whose port is closed still
    returns False, which is exactly what callers need to decide.
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
    """True if a Clash for Windows process is currently running (Windows only)."""
    if sys.platform != "win32":
        return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq clash-win64.exe", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, timeout=10,
        )
        return "clash-win64.exe" in out.lower()
    except Exception:
        return False


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


def stop() -> bool:
    """Clean GUI exit: focus the Clash window and send Ctrl+Q (Electron quit).

    Returns True if a window was found and keys were sent. NEVER uses taskkill
    (that triggers UAC, per SKILL.md). If this returns False, exit via the tray.
    """
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


def run_with_proxy(cmd: Iterable[str], port: Optional[int] = None,
                   close_after: bool = False) -> subprocess.CompletedProcess:
    """Run `cmd` with HTTP_PROXY/HTTPS_PROXY pointed at Clash.

    If `close_after` is True (the We-AIPO 用完即关 pattern), the proxy is stopped
    after the command finishes — useful for one-shot pushes like git push.
    """
    port = _port() if port is None else port
    env = {
        **os.environ,
        "HTTP_PROXY": f"http://127.0.0.1:{port}",
        "HTTPS_PROXY": f"http://127.0.0.1:{port}",
        "http_proxy": f"http://127.0.0.1:{port}",
        "https_proxy": f"http://127.0.0.1:{port}",
    }
    try:
        result = subprocess.run(list(cmd), env=env, capture_output=True, text=True)
    finally:
        if close_after:
            stop()
    # Re-emit so the caller sees normal output when run from a shell
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Clash for Windows proxy manager.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_start = sub.add_parser("start", help="launch Clash and poll until the proxy is ready")
    sp_start.add_argument("--timeout", type=float, default=START_TIMEOUT)

    sub.add_parser("status", help="exit 0 if proxy is up, 1 otherwise")
    sub.add_parser("stop", help="clean GUI exit (Ctrl+Q)")

    sp_run = sub.add_parser("run", help="run a command through the proxy")
    sp_run.add_argument("--close-after", action="store_true",
                        help="stop the proxy after the command finishes (用完即关)")
    sp_run.add_argument("command", nargs=argparse.REMAINDER, help="command to run (use -- first)")

    args = p.parse_args(argv)

    if args.cmd == "status":
        return 0 if status() else 1
    if args.cmd == "start":
        return 0 if start(timeout=args.timeout) else 1
    if args.cmd == "stop":
        return 0 if stop() else 1
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
