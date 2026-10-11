#!/usr/bin/env python3
"""Register / remove / inspect the self-update schedule on THIS machine.

    python automation/schedule_daily.py                  register (default: every Monday 02:00 Beijing time)
    python automation/schedule_daily.py --day mon --at 02:00 --tz-offset 8
    python automation/schedule_daily.py --day daily --at 22:00   every day instead
    python automation/schedule_daily.py --status | --remove

Windows → Task Scheduler, an "every N days" trigger (N = 7 for a weekday,
1 for daily) whose StartBoundary is the *next* occurrence written with the
source offset (``2026-10-12T02:00:00+08:00``). Recurrence is interval
arithmetic on that instant, so it fires at the Beijing wall-clock time
whatever the machine's zone or DST (no day-of-week ambiguity across zones),
and registering never causes an immediate catch-up run. Silent pythonw,
StartWhenAvailable catch-up after missed runs (e.g. the PC was off at 02:00),
single instance. macOS/Linux → a tagged crontab line at the equivalent local
time and weekday (re-run after a local DST change). Idempotent: re-running
replaces the previous entry. (File and task names keep "daily" for
compatibility with existing installs.)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

AUTO = Path(__file__).resolve().parent
REPO = AUTO.parent
SCRIPT = AUTO / "superskill_daily.py"
TASK = "SuperSkillDaily"
TAG = "# super-skill-daily"
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DEFAULT_DAY = "mon"           # weekly, on Mondays
DEFAULT_AT = "02:00"          # Beijing time
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


def parse_day(day: str | None) -> int | None:
    """'mon'…'sun' (or full names) → 0…6; 'daily' / '*' → None (every day)."""
    d = (day or "").strip().lower()
    if d in ("daily", "every", "*", "everyday", "every-day"):
        return None
    if not d or d[:3] not in DAYS:
        raise ValueError(f"bad day {day!r} (use mon…sun or daily)")
    return DAYS.index(d[:3])


def every_days(weekday: int | None) -> int:
    return 1 if weekday is None else 7


def schedule_label(day: str | None, at: str, tz_offset: float) -> str:
    wd = parse_day(day)
    when = "every day" if wd is None else f"every {dt.date(2026, 10, 12 + wd):%A}"   # 2026-10-12 is a Monday
    return f"{when} {at} UTC{tz_offset:+g}"


def next_run(hhmm: str, tz_offset_hours: float, now: dt.datetime | None = None,
             weekday: int | None = None) -> dt.datetime:
    """Next instant (aware, in the source zone) whose wall clock shows ``hhmm`` (on ``weekday``)."""
    h, m = _parse_hhmm(hhmm)
    src = dt.timezone(dt.timedelta(hours=tz_offset_hours))
    now_src = (now or dt.datetime.now().astimezone()).astimezone(src)
    cand = now_src.replace(hour=h, minute=m, second=0, microsecond=0)
    if weekday is not None:
        cand += dt.timedelta(days=(weekday - cand.weekday()) % 7)
    if cand <= now_src:
        cand += dt.timedelta(days=every_days(weekday))
    return cand


def local_time_for(hhmm: str, tz_offset_hours: float, today: dt.date | None = None) -> str:
    """Local HH:MM equal to ``hhmm`` in the fixed-offset zone UTC+tz_offset."""
    h, m = _parse_hhmm(hhmm)
    src = dt.timezone(dt.timedelta(hours=tz_offset_hours))
    moment = dt.datetime.combine(today or dt.date.today(), dt.time(h, m), tzinfo=src)
    return moment.astimezone().strftime("%H:%M")


def local_slot(start: dt.datetime, weekday: int | None) -> tuple[str, str]:
    """(local HH:MM, cron day-of-week) of an aware source-zone instant; '*' when daily."""
    local = start.astimezone()
    return local.strftime("%H:%M"), "*" if weekday is None else str((local.weekday() + 1) % 7)


def python_for_task() -> str:
    exe = Path(sys.executable)
    if os.name == "nt":
        pyw = exe.with_name("pythonw.exe")
        if pyw.exists():
            return str(pyw)  # no console window
    return str(exe)


def _ps(cmd: str) -> tuple[int, str]:
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                        "[Console]::OutputEncoding=[Text.Encoding]::UTF8;" + cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def windows_register_script(py: str, script: str, repo: str, start: dt.datetime, every: int = 7,
                            label: str = "") -> str:
    """PowerShell that (re)registers the task; ``start`` must be timezone-aware."""
    q = lambda s: s.replace("'", "''")  # noqa: E731 - PowerShell single-quote escaping
    boundary = start.isoformat(timespec="seconds")          # e.g. 2026-10-12T02:00:00+08:00
    local_hhmm = start.astimezone().strftime("%H:%M")
    return (
        f"$a = New-ScheduledTaskAction -Execute '{q(py)}' -Argument '\"{q(script)}\"' -WorkingDirectory '{q(repo)}';"
        f"$t = New-ScheduledTaskTrigger -Daily -DaysInterval {int(every)} -At '{local_hhmm}';"
        f"$t.StartBoundary = '{boundary}';"
        "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries "
        "-DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew "
        f"-ExecutionTimeLimit (New-TimeSpan -Hours {EXEC_LIMIT_HOURS});"
        f"Register-ScheduledTask -TaskName '{TASK}' -Description 'Super-Skill self-update ({q(label)}): "
        "radar -> distill -> gates -> install -> push' -Action $a -Trigger $t -Settings $s -Force | Out-Null;"
        f"$r = Get-ScheduledTask -TaskName '{TASK}'; $n = (Get-ScheduledTaskInfo -TaskName '{TASK}').NextRunTime;"
        "$r.Triggers[0].StartBoundary + ' | every ' + $r.Triggers[0].DaysInterval + ' day(s) | next run ' + "
        "$(if ($n) { $n.ToString('yyyy-MM-dd ddd HH:mm zzz') } else { 'none' })"
    )


def boundary_mismatch(start_boundary: str, at: str = DEFAULT_AT, tz_offset: float = DEFAULT_TZ_OFFSET,
                      day: str | None = DEFAULT_DAY, every: int | None = None) -> str | None:
    """Warning text when a registered trigger is not the default schedule, else None."""
    fix = "re-run `python automation/schedule_daily.py` to apply it"
    try:
        registered = dt.datetime.fromisoformat(start_boundary.strip())
    except ValueError:
        return f"cannot parse registered trigger {start_boundary!r}"
    if registered.tzinfo is None:
        return f"trigger {start_boundary} has no UTC offset (registered by an older version) — {fix}"
    h, m = _parse_hhmm(at)
    wd = parse_day(day)
    got = registered.astimezone(dt.timezone(dt.timedelta(hours=tz_offset)))
    if every == 1:
        have = "every day"
    elif every == 7:
        have = f"every {got:%A}"
    else:
        have = f"every {every} day(s) from {got:%A}"
    have += f" {got:%H:%M} UTC{tz_offset:+g}"
    wrong_time = (got.hour, got.minute) != (h, m)
    wrong_day = wd is not None and got.weekday() != wd
    wrong_every = every is not None and every != every_days(wd)
    if wrong_time or wrong_day or wrong_every:
        return f"registered {have}, default is {schedule_label(day, at, tz_offset)} — {fix}"
    return None


def register_windows(start: dt.datetime, every: int, label: str) -> tuple[int, str]:
    return _ps(windows_register_script(python_for_task(), str(SCRIPT), str(REPO), start, every, label))


def cron_line(at_local: str, dow: str = "*") -> str:
    h, m = _parse_hhmm(at_local)
    return (f"{m} {h} * * {dow} cd \"{REPO}\" && \"{sys.executable}\" \"{SCRIPT}\" "
            f">> \"{AUTO / 'logs' / 'cron.log'}\" 2>&1 {TAG}")


def register_cron(at_local: str, dow: str = "*") -> tuple[int, str]:
    (AUTO / "logs").mkdir(parents=True, exist_ok=True)  # cron redirects into it before python runs
    line = cron_line(at_local, dow)
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
            "$n = if ($i.NextRunTime) { $i.NextRunTime.ToString('yyyy-MM-dd ddd HH:mm zzz') } else { 'none' };"
            # a never-run task reports the placeholder 1999-11-30, not $null
            "$l = if ($i.LastRunTime -and $i.LastRunTime.Year -gt 2000) "
            "{ $i.LastRunTime.ToString('yyyy-MM-dd HH:mm') } else { 'never' };"
            "'trigger ' + $t.Triggers[0].StartBoundary + ' | every ' + $t.Triggers[0].DaysInterval + ' day(s)'"
            " + ' | state ' + $t.State + ' | next run ' + $n + "
            "' | last run ' + $l + ' | last result ' + $i.LastTaskResult + "
            "' | time limit ' + $t.Settings.ExecutionTimeLimit")
        if rc == 0 and out.startswith("trigger "):
            m = re.search(r"\| every (\d+) day", out)
            warn = boundary_mismatch(out.split()[1], every=int(m.group(1)) if m else 0)
            if warn:
                out += f"\n⚠ {warn}"
        return rc, out
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    lines = [l for l in cur.splitlines() if TAG in l]
    return (0, lines[0]) if lines else (1, "not scheduled")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="schedule the Super-Skill self-update")
    ap.add_argument("--day", default=DEFAULT_DAY,
                    help=f"weekday mon…sun, or 'daily' (default {DEFAULT_DAY})")
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
        weekday = parse_day(args.day)
        start = next_run(args.at, args.tz_offset, weekday=weekday)
        label = schedule_label(args.day, args.at, args.tz_offset)
        if os.name == "nt":
            rc, out = register_windows(start, every_days(weekday), label)
            out = f"Task '{TASK}' {label} (local {start.astimezone():%a %H:%M}); trigger {out}"
        elif shutil.which("crontab"):
            local, dow = local_slot(start, weekday)
            rc, out = register_cron(local, dow)
            out = f"cron at {local} local, day-of-week {dow} (= {label}): {out}"
        else:
            rc, out = 1, "no scheduler found (Task Scheduler / crontab)"
    print(out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
