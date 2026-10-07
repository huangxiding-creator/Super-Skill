#!/usr/bin/env python3
"""Register / remove / inspect the daily self-update schedule on THIS machine.

    python automation/schedule_daily.py            register (default 22:00 Beijing time)
    python automation/schedule_daily.py --at 22:00 --tz-offset 8
    python automation/schedule_daily.py --status | --remove

Windows → Task Scheduler. The trigger's StartBoundary carries the source
offset (``2026-10-02T22:00:00+08:00``), so Task Scheduler fires at 22:00
Beijing time whatever the machine's zone or DST; the boundary is always the
*next* occurrence, so registering never causes an immediate catch-up run.
Silent pythonw, StartWhenAvailable catch-up after missed runs, single instance.
macOS/Linux → a tagged crontab line at the equivalent local time (re-run
after a local DST change). Idempotent: re-running replaces the previous entry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

AUTO = Path(__file__).resolve().parent
REPO = AUTO.parent
SCRIPT = AUTO / "superskill_daily.py"
TASK = "SuperSkillDaily"
TAG = "# super-skill-daily"
DEFAULT_AT = "22:00"          # Beijing time
DEFAULT_TZ_OFFSET = 8.0       # UTC+8, no DST
# worst case, every timeout hit: 150 min lock wait + preflight git (status/stash/fetch×2/merge ≤ 15)
# + radar budget 15 + distill 60 + gates 60 + plugin validate 5 + install 15 + push 20 ≈ 340 min
# → 7 h keeps ~80 min of headroom (a run killed at the limit is still recovered next time)
EXEC_LIMIT_HOURS = 7


def _parse_hhmm(hhmm: str) -> tuple[int, int]:
    h, m = (int(x) for x in hhmm.split(":"))
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"bad time {hhmm!r}")
    return h, m


def next_run(hhmm: str, tz_offset_hours: float, now: dt.datetime | None = None) -> dt.datetime:
    """Next instant (aware, in the source zone) when its wall clock shows ``hhmm``."""
    h, m = _parse_hhmm(hhmm)
    src = dt.timezone(dt.timedelta(hours=tz_offset_hours))
    now_src = (now or dt.datetime.now().astimezone()).astimezone(src)
    cand = now_src.replace(hour=h, minute=m, second=0, microsecond=0)
    if cand <= now_src:
        cand += dt.timedelta(days=1)
    return cand


def local_time_for(hhmm: str, tz_offset_hours: float, today: dt.date | None = None) -> str:
    """Local HH:MM equal to ``hhmm`` in the fixed-offset zone UTC+tz_offset."""
    h, m = _parse_hhmm(hhmm)
    src = dt.timezone(dt.timedelta(hours=tz_offset_hours))
    moment = dt.datetime.combine(today or dt.date.today(), dt.time(h, m), tzinfo=src)
    return moment.astimezone().strftime("%H:%M")


def python_for_task() -> str:
    exe = Path(sys.executable)
    if os.name == "nt":
        pyw = exe.with_name("pythonw.exe")
        if pyw.exists():
            return str(pyw)  # no console window at night
    return str(exe)


def _ps(cmd: str) -> tuple[int, str]:
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                        "[Console]::OutputEncoding=[Text.Encoding]::UTF8;" + cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def windows_register_script(py: str, script: str, repo: str, start: dt.datetime) -> str:
    """PowerShell that (re)registers the task; ``start`` must be timezone-aware."""
    q = lambda s: s.replace("'", "''")  # noqa: E731 - PowerShell single-quote escaping
    boundary = start.isoformat(timespec="seconds")          # e.g. 2026-10-02T22:00:00+08:00
    local_hhmm = start.astimezone().strftime("%H:%M")
    return (
        f"$a = New-ScheduledTaskAction -Execute '{q(py)}' -Argument '\"{q(script)}\"' -WorkingDirectory '{q(repo)}';"
        f"$t = New-ScheduledTaskTrigger -Daily -At '{local_hhmm}';"
        f"$t.StartBoundary = '{boundary}';"
        "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries "
        "-DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew "
        f"-ExecutionTimeLimit (New-TimeSpan -Hours {EXEC_LIMIT_HOURS});"
        f"Register-ScheduledTask -TaskName '{TASK}' -Description 'Super-Skill daily self-update: "
        "radar -> distill -> gates -> install -> push' -Action $a -Trigger $t -Settings $s -Force | Out-Null;"
        f"$r = Get-ScheduledTask -TaskName '{TASK}'; $n = (Get-ScheduledTaskInfo -TaskName '{TASK}').NextRunTime;"
        "$r.Triggers[0].StartBoundary + ' | next run ' + $(if ($n) { $n.ToString('yyyy-MM-dd HH:mm zzz') } "
        "else { 'none' })"
    )


def boundary_mismatch(start_boundary: str, at: str = DEFAULT_AT, tz_offset: float = DEFAULT_TZ_OFFSET) -> str | None:
    """Warning text when a registered StartBoundary is not ``at`` in UTC+tz_offset, else None."""
    try:
        registered = dt.datetime.fromisoformat(start_boundary.strip())
    except ValueError:
        return f"cannot parse registered trigger {start_boundary!r}"
    h, m = _parse_hhmm(at)
    want = dt.timezone(dt.timedelta(hours=tz_offset))
    if registered.tzinfo is None:
        return (f"trigger {start_boundary} has no UTC offset (registered by an older version) — "
                "re-run `python automation/schedule_daily.py`")
    got = registered.astimezone(want)
    if (got.hour, got.minute) != (h, m):
        return (f"registered for {got:%H:%M} UTC{tz_offset:+g}, default is {at} — "
                "re-run `python automation/schedule_daily.py` to apply it")
    return None


def register_windows(start: dt.datetime) -> tuple[int, str]:
    return _ps(windows_register_script(python_for_task(), str(SCRIPT), str(REPO), start))


def cron_line(at_local: str) -> str:
    h, m = _parse_hhmm(at_local)
    return (f"{m} {h} * * * cd \"{REPO}\" && \"{sys.executable}\" \"{SCRIPT}\" "
            f">> \"{AUTO / 'logs' / 'cron.log'}\" 2>&1 {TAG}")


def register_cron(at_local: str) -> tuple[int, str]:
    (AUTO / "logs").mkdir(parents=True, exist_ok=True)  # cron redirects into it before python runs
    line = cron_line(at_local)
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    kept = [l for l in cur.splitlines() if TAG not in l]
    new = "\n".join(kept + [line]) + "\n"
    p = subprocess.run(["crontab", "-"], input=new, capture_output=True, text=True)
    return p.returncode, line if p.returncode == 0 else p.stderr


def remove() -> tuple[int, str]:
    if os.name == "nt":
        return _ps(f"Unregister-ScheduledTask -TaskName '{TASK}' -Confirm:$false; 'removed'")
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    new = "\n".join(l for l in cur.splitlines() if TAG not in l) + "\n"
    p = subprocess.run(["crontab", "-"], input=new, capture_output=True, text=True)
    return p.returncode, "removed"


def status() -> tuple[int, str]:
    if os.name == "nt":
        rc, out = _ps(
            f"$t = Get-ScheduledTask -TaskName '{TASK}' -ErrorAction Stop; $i = $t | Get-ScheduledTaskInfo;"
            "$n = if ($i.NextRunTime) { $i.NextRunTime.ToString('yyyy-MM-dd HH:mm zzz') } else { 'none' };"
            # a never-run task reports the placeholder 1999-11-30, not $null
            "$l = if ($i.LastRunTime -and $i.LastRunTime.Year -gt 2000) "
            "{ $i.LastRunTime.ToString('yyyy-MM-dd HH:mm') } else { 'never' };"
            "'trigger ' + $t.Triggers[0].StartBoundary + ' | state ' + $t.State + ' | next run ' + $n + "
            "' | last run ' + $l + ' | last result ' + $i.LastTaskResult + "
            "' | time limit ' + $t.Settings.ExecutionTimeLimit")
        if rc == 0 and out.startswith("trigger "):
            warn = boundary_mismatch(out.split()[1])
            if warn:
                out += f"\n⚠ {warn}"
        return rc, out
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    lines = [l for l in cur.splitlines() if TAG in l]
    return (0, lines[0]) if lines else (1, "not scheduled")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="schedule the Super-Skill daily self-update")
    ap.add_argument("--at", default=DEFAULT_AT, help=f"trigger time in the source zone (default {DEFAULT_AT})")
    ap.add_argument("--tz-offset", type=float, default=DEFAULT_TZ_OFFSET,
                    help="source zone UTC offset (Beijing = 8)")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--status", action="store_true")
    return ap


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    if args.status:
        rc, out = status()
    elif args.remove:
        rc, out = remove()
    else:
        start = next_run(args.at, args.tz_offset)
        zone = f"UTC{args.tz_offset:+g}"
        if os.name == "nt":
            rc, out = register_windows(start)
            out = f"Task '{TASK}' daily at {args.at} {zone} (local {start.astimezone():%H:%M}); trigger {out}"
        elif shutil.which("crontab"):
            local = local_time_for(args.at, args.tz_offset)
            rc, out = register_cron(local)
            out = f"cron at {local} local (= {args.at} {zone}): {out}"
        else:
            rc, out = 1, "no scheduler found (Task Scheduler / crontab)"
    print(out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
