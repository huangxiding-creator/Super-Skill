---
name: clash-proxy
description: Manage the Clash proxy needed to reach GFW-blocked sites (GitHub/HuggingFace/PyPI) from this machine. Start before a network op, stop after (用完即关). Invoke when git push/pull to GitHub times out, when downloading foreign resources, or on "代理/网络失败".
---

# clash-proxy — Clash for Windows proxy manager

> **Why this exists:** from this machine, direct connections to `github.com:443` (and
> HuggingFace / raw PyPI) time out — a Clash proxy on `127.0.0.1:7890` is required.
> This sub-skill brings the proxy up on demand, routes a command through it, and tears
> it down afterwards, so network ops succeed without leaving the proxy running.

This is the operational tool behind the **We-AIPO "用完即关" (close-after-use)** pattern
documented in [../../references/audit-loop-case-study.md](../../references/audit-loop-case-study.md).

## When to invoke

- `git push` / `git pull` / `git fetch` to GitHub fails with "Failed to connect … port 443" or "Connection was reset"
- Downloading from HuggingFace / raw GitHub / a foreign CDN
- User says "代理 / 网络失败 / push 失败 / 连不上 GitHub"
- Before Phase 2 (GitHub Discovery) or Phase 11 (deploy/push) on this machine

## Usage

```bash
# 1. Bring the proxy up (launches Clash, polls port 7890 until ready, ≤120s)
python scripts/clash_proxy.py start

# 2. Run any command through the proxy
python scripts/clash_proxy.py run -- git push origin master
python scripts/clash_proxy.py run -- git -c http.proxy=http://127.0.0.1:7890 push origin master

# 3. One-shot: run + close the proxy right after (用完即关)
python scripts/clash_proxy.py run --close-after -- git push origin master

# Status check (exit 0 = up, 1 = down) — no side effects
python scripts/clash_proxy.py status

# Clean GUI exit (Ctrl+Q) — NEVER use taskkill (triggers UAC)
python scripts/clash_proxy.py stop
```

**Direct git one-liner** (no Python wrapper, if you only need the proxy for one push):
```bash
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 push origin master
```

## Python API

```python
from clash_proxy import start, stop, status, run_with_proxy
start()                         # launch + poll until ready
run_with_proxy(["git", "push"]) # HTTPS_PROXY injected into the subprocess
stop()                          # clean GUI exit
```

## How it works

| Function | Behaviour |
|----------|-----------|
| `status()` | Ground truth — opens a real request through `127.0.0.1:7890` to `https://github.com`. A live Clash process whose port is closed still returns False. |
| `start()` | If `status()` is up → return. Else launch Clash via `explorer.exe` (so the Electron GUI initializes its singleton + tray), then poll every 2s up to 120s. Best-effort auto-clicks the Windows firewall `允许访问` button once. |
| `stop()` | Focus the Clash window and send `Ctrl+Q` (Electron standard quit). **Never `taskkill`** — that triggers a UAC prompt. If `stop()` can't find the window, exit via the tray. |
| `run_with_proxy(cmd)` | Spawns `cmd` with `HTTP_PROXY`/`HTTPS_PROXY` (and lowercase variants) set to the proxy. `close_after=True` stops the proxy when the command finishes. |

## Configuration (no code edits)

| Env var | Default | Purpose |
|---------|---------|---------|
| `CLASH_EXE` | `C:\Program Files\Clash for Windows\Clash for Windows.exe` | Clash executable path |
| `CLASH_PORT` | `7890` | mixed-port to poll |
| `CLASH_TEST` | `https://github.com` | URL probed to confirm real internet reachability |

## Platform notes

- **Windows-focused** — the GUI launch, firewall dismissal, and `Ctrl+Q` exit are Windows/Clash-for-Windows specific.
- On other platforms `start`/`stop` are graceful no-ops (with a warning); `status` and `run` work anywhere a proxy is already up.
- The script is pure stdlib (`urllib`, `subprocess`, `ctypes`) — no dependencies.

## Tests

`scripts/test_clash_proxy.py` — 12 cases covering the deterministic logic (status on
dead/live port, env config resolution, `run_with_proxy` env injection, argparse).
GUI paths (`start`/`stop`/firewall) are intentionally not live-tested. Auto-discovered
by `scripts/health_check.py`.
