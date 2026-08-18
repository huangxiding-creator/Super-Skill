---
name: clash-proxy
description: Manage the Clash proxy needed to reach GFW-blocked sites (GitHub/HuggingFace/PyPI) from this machine. Start before a network op, stop after (用完即关). V4.1.6 adds the We-AIPO Clash REST API layer (mode switching, node pinning, DNS-residue cleanup) and a one-command `push` recipe. Invoke when git push/pull to GitHub times out, when downloading foreign resources, or on "代理/网络失败".
---

# clash-proxy — Clash for Windows proxy manager

> **Why this exists:** from this machine, direct connections to `github.com:443` (and
> HuggingFace / raw PyPI) time out — a Clash proxy on `127.0.0.1:7890` is required.
> This sub-skill brings the proxy up on demand, routes a command through it, and tears
> it down afterwards, so network ops succeed without leaving the proxy running.

This is the operational tool behind the **We-AIPO "用完即关" (close-after-use)** pattern
documented in [../../references/audit-loop-case-study.md](../../references/audit-loop-case-study.md).
V4.1.6 ports We-AIPO's **Clash API approach** (its `proxy_mgr.py` / `sched_guard.py` /
`push_github.py`, battle-tested over 290+ commits): mode switching goes through the
Clash RESTful API instead of GUI automation — silent, fast, and leaves no TUN/DNS residue.

## When to invoke

- `git push` / `git pull` / `git fetch` to GitHub fails with "Failed to connect … port 443" or "Connection was reset"
- Downloading from HuggingFace / raw GitHub / a foreign CDN
- User says "代理 / 网络失败 / push 失败 / 连不上 GitHub"
- Before Phase 2 (GitHub Discovery) or Phase 11 (deploy/push) on this machine

## Usage

```bash
# The one-command push (We-AIPO recipe: commit -> proxy -> push -> direct-fallback -> close)
python scripts/clash_proxy.py push -m "feat: something"
python scripts/clash_proxy.py push                  # push only, no commit
python scripts/clash_proxy.py push --branch master --repo-root /path/to/repo
python scripts/clash_proxy.py push --keep           # after: switch direct, leave Clash running

# API control (no GUI interaction)
python scripts/clash_proxy.py mode                  # diagnostic: API base, mode, DNS check
python scripts/clash_proxy.py global                # PATCH /configs -> global (proxy) mode
python scripts/clash_proxy.py direct                # direct + TUN/DNS off + flushdns (keeps running)

# Lifecycle
python scripts/clash_proxy.py start                 # launch Clash + poll port 7890 (<=120s)
python scripts/clash_proxy.py status                # exit 0 = up, 1 = down (real request, no side effects)
python scripts/clash_proxy.py stop                  # full exit: API direct FIRST, then Ctrl+Q / taskkill
python scripts/clash_proxy.py run -- <cmd...>       # any command with HTTP(S)_PROXY set
python scripts/clash_proxy.py run --close-after -- git push origin master   # 用完即关
```

**Direct git one-liner** (no Python wrapper, if you only need the proxy for one push):
```bash
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 push origin master
```

## Python API

```python
from clash_proxy import start, stop, status, run_with_proxy, push
push(["git", "push"])            # full recipe below (preferred for pushes)
start()                          # launch + poll until ready
run_with_proxy(["git", "push"])  # HTTPS_PROXY injected into the subprocess
stop()                           # full exit

# Clash REST API layer
from clash_proxy import api_base, api_reachable, get_mode, set_mode, pin_node, release
api_reachable()                  # GET /version == 200
get_mode()                       # "global" | "rule" | "direct" | None
set_mode("global")               # PATCH /configs; TUN stays OFF (explicit-proxy mode)
set_mode("direct")               # direct + tun/dns off — kills fake-IP residue
release()                        # direct switch but LEAVE Clash running (W18 pattern)
pin_node("🇯🇵 日本 01")          # PUT /proxies/GLOBAL — stable exit geo
```

## The push recipe (We-AIPO `scripts/push_github.py`, proven)

1. Optional `git add -A && git commit -m <msg>`
2. Show unpushed commits (`git log @{u}..HEAD`); exit 0 early if none
3. Bring the proxy up (`start()` if needed); API-switch to global + pin node
4. `git push` with `HTTP(S)_PROXY` env (120s timeout)
5. On failure: **one direct retry** with the proxy overridden empty (60s)
6. Close: `stop()` (full exit) — or `release()` with `--keep` (direct mode, Clash stays
   running; cheaper between repeated proxy sessions, We-AIPO W18 lesson)

## Clash API layer — how it works

| Function | Behaviour |
|----------|-----------|
| `api_base()` | Discovery: `CLASH_API` env → port parsed from `~/.config/clash/config.yaml` (`external-controller:`) → probe table (20225 CFW GUI, 11845 headless, 9090 upstream default), each probed with a real `GET /version`. Success cached. **Port drift is the #1 silent killer** — We-AIPO once hardcoded 18886 and every API call silently failed. |
| `api_secret()` | `CLASH_SECRET` env → parsed from config.yaml (`secret:`). Never hardcoded in this repo. |
| `set_mode("global")` | `PATCH /configs {"mode":"global"}`. **TUN off by default** — traffic opts in via explicit proxy env, so domestic DNS is never hijacked. `tun=True` opts into whole-system capture. |
| `set_mode("direct")` | Also disables `tun` + fake-IP DNS: killing/leaving Clash in TUN mode poisons DNS with `198.18.x.x` fake-IPs (We-AIPO 2026-08-07 lesson). |
| `pin_node()` | `PUT /proxies/GLOBAL {"name": node}` — exit-country drift across runs is a risk-control trigger for Google-class services (We-AIPO FIX-0818p). Node from arg or `CLASH_NODE`; no-op when unset. |
| `status()` | Ground truth — a real request through `127.0.0.1:7890` to `https://github.com`. Port-open alone is never trusted. |
| `dns_hijacked()` | `nslookup` a domain; any answer in `198.18.0.0/16` (Clash fake-IP range) means TUN DNS is still capturing. |
| `release()` | Direct mode + TUN/DNS off + system proxy off + `ipconfig /flushdns`, **Clash keeps running** (W18 NetworkOrchestrator pattern — avoids TUN/DNS churn between sessions). |
| `stop()` | Order matters: **API direct FIRST** (even if the kill fails, no TUN/DNS residue survives) → system proxy off → graceful `Ctrl+Q` → `taskkill` WM_CLOSE → `/F` only for residue (Clash runs as the current user, no UAC) → best-effort `sc stop "Clash Core Service"` → flushdns → verify no process remains. |
| `run_with_proxy(cmd)` | Spawns `cmd` with proxy env injected. `close_after=True` stops the proxy afterwards. |

## Configuration (no code edits)

| Env var | Default | Purpose |
|---------|---------|---------|
| `CLASH_EXE` | `C:\Program Files\Clash for Windows\Clash for Windows.exe` | Clash executable path |
| `CLASH_PORT` | `7890` | mixed-port to poll |
| `CLASH_TEST` | `https://github.com` | URL probed to confirm real internet reachability |
| `CLASH_API` | *(discovered)* | explicit Clash API base URL (skips discovery) |
| `CLASH_SECRET` | *(discovered)* | API bearer secret (skips config.yaml discovery) |
| `CLASH_NODE` | *(unset)* | exit node pinned on every `global`/`push` |

## Platform notes

- **Windows-focused** — the GUI launch, firewall dismissal, and `Ctrl+Q` exit are Windows/Clash-for-Windows specific.
- On other platforms `start`/`stop` are graceful no-ops (with a warning); `status`, `run`, and the API layer work anywhere a Clash API/proxy is reachable.
- The script is pure stdlib (`urllib`, `subprocess`, `ctypes`, `winreg`) — no dependencies.

## Tests

`scripts/test_clash_proxy.py` — 34 cases covering the deterministic logic: status on
dead/live port, env config resolution, `run_with_proxy` env injection, config.yaml
port+secret discovery (incl. caching and fallback), mode-switch payload correctness
(direct disables TUN+DNS; global defaults TUN off), node pinning, fake-IP DNS detection,
`release()` vs `stop()` semantics, and the full `push` recipe (commit → proxied push →
direct fallback → close/keep). GUI paths (`start`/`_gui_quit`/firewall) are intentionally
not live-tested. Auto-discovered by `scripts/health_check.py`.

## Integration with Super-Skill

- Phase 2 (GitHub Discovery) and Phase 11 (Deployment): wrap foreign-network fetches and pushes with this skill.
- Phase 7 (`auto-git-create`): repo creation/push on this machine goes through `push`.
- The We-AIPO lessons encoded here (port drift, silent API failure, TUN/DNS residue,
  verify-with-real-request) are the networking chapter of
  [../../references/audit-loop-case-study.md](../../references/audit-loop-case-study.md).

## Deliverables

- `scripts/clash_proxy.py` — CLI + Python API (lifecycle, Clash API layer, push recipe)
- `scripts/test_clash_proxy.py` — 34/34 tests
