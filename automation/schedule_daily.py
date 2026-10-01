#!/usr/bin/env python3
"""Register / remove / inspect the daily self-update schedule on THIS machine.

    python automation/schedule_daily.py            register (default 23:00 Beijing time)
    python automation/schedule_daily.py --at 23:00 --tz-offset 8
    python automation/schedule_daily.py --status | --remove

Beijing time is fixed UTC+8 (no DST), so the trigger is converted to the
machine's local wall-clock time without tzdata. Windows → Task Scheduler
(silent pythonw, StartWhenAvailable catch-up, single instance); macOS/Linux →
a tagged crontab line. Idempotent: re-running replaces the previous entry.
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


def local_time_for(hhmm: str, tz_offset_hours: float, today: dt.date | None = None) -> str:
    """Local HH:MM equal to ``hhmm`` in the fixed-offset zone UTC+tz_offset."""
    h, m = (int(x) for x in hhmm.split(":"))
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
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def register_windows(at_local: str) -> tuple[int, str]:
    py, script, repo = python_for_task(), str(SCRIPT), str(REPO)
    q = lambda s: s.replace("'", "''")  # noqa: E731 - PowerShell single-quote escaping
    cmd = (
        f"$a = New-ScheduledTaskAction -Execute '{q(py)}' -Argument '\"{q(script)}\"' -WorkingDirectory '{q(repo)}';"
        f"$t = New-ScheduledTaskTrigger -Daily -At '{at_local}';"
        "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries "
        "-DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 3);"
        f"Register-ScheduledTask -TaskName '{TASK}' -Description 'Super-Skill daily self-update: "
        "radar -> distill -> gates -> install -> push' -Action $a -Trigger $t -Settings $s -Force | Out-Null;"
        f"(Get-ScheduledTaskInfo -TaskName '{TASK}').NextRunTime.ToString('yyyy-MM-dd HH:mm')"
    )
    return _ps(cmd)


def register_cron(at_local: str) -> tuple[int, str]:
    h, m = at_local.split(":")
    line = (f"{int(m)} {int(h)} * * * cd \"{REPO}\" && \"{sys.executable}\" \"{SCRIPT}\" "
            f">> \"{AUTO / 'logs' / 'cron.log'}\" 2>&1 {TAG}")
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
        return _ps(f"$i = Get-ScheduledTaskInfo -TaskName '{TASK}' -ErrorAction Stop;"
                   "'next run: ' + $i.NextRunTime + ' | last run: ' + $i.LastRunTime + ' | last result: ' + $i.LastTaskResult")
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    lines = [l for l in cur.splitlines() if TAG in l]
    return (0, lines[0]) if lines else (1, "not scheduled")


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="schedule the Super-Skill daily self-update")
    ap.add_argument("--at", default="23:00", help="trigger time in the source zone (default 23:00)")
    ap.add_argument("--tz-offset", type=float, default=8.0, help="source zone UTC offset (Beijing = 8)")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args(argv)
    if args.status:
        rc, out = status()
    elif args.remove:
        rc, out = remove()
    else:
        local = local_time_for(args.at, args.tz_offset)
        if os.name == "nt":
            rc, out = register_windows(local)
            out = f"Task '{TASK}' daily at {local} local (= {args.at} UTC+{args.tz_offset:g}); next run {out}"
        elif shutil.which("crontab"):
            rc, out = register_cron(local)
            out = f"cron at {local} local (= {args.at} UTC+{args.tz_offset:g}): {out}"
        else:
            rc, out = 1, "no scheduler found (Task Scheduler / crontab)"
    print(out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
