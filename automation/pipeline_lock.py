"""Machine-wide mutual exclusion for the unattended pipelines (daily + weekly).

Both pipelines rewrite the skill tree, run `git checkout -- .` on failure,
refresh the same global install and push to the same branch, so they must
never overlap. On the maintainer machine the weekly run (Sunday 22:00) and the
daily run (22:00) start in the same minute.

Design: an **OS-held lock** on byte 0 of ``<lock dir>/super-skill-pipeline.lock``
(``msvcrt.locking`` on Windows, ``fcntl.flock`` on POSIX) taken on a file
descriptor that stays open for the whole run. The operating system releases it
when the process exits for any reason — normal end, crash, Task Scheduler's
ExecutionTimeLimit, shutdown — so there is no stale lock to detect or break and
no check-then-delete race. Holder details live in a side file (``.info``) and
are used for log messages only.

The lock covers the pipeline *process*. Its children (``claude -p``, git,
the test suite …) would outlive a killed holder, so on Windows each pipeline
calls ``tie_children_to_this_process()`` first: a kill-on-close Job Object
ends every descendant the moment the pipeline dies. On POSIX a killed
pipeline's children are not reaped automatically (documented limitation).

The lock directory defaults to the user's Claude config dir (``~/.claude``), so
every clone on the machine shares it; override with ``SUPERSKILL_LOCK_DIR``.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
from pathlib import Path

LOCK_NAME = "super-skill-pipeline.lock"
INFO_SUFFIX = ".info"
_held: dict[str, tuple[int, str]] = {}   # resolved lock path -> (fd, owner) held by THIS process


def default_dir() -> Path:
    env = os.environ.get("SUPERSKILL_LOCK_DIR")
    if env:
        return Path(env)
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


def _lock_path(lock_dir=None) -> Path:
    return Path(lock_dir) / LOCK_NAME if lock_dir else default_dir() / LOCK_NAME


def _try_lock(fd: int) -> bool:
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:  # PermissionError on Windows, BlockingIOError on POSIX
        return False


def _unlock(fd: int) -> None:
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass


def holder(lock_dir=None) -> dict | None:
    """Last recorded holder (informational; may describe a finished run)."""
    try:
        path = _lock_path(lock_dir)
        data = json.loads(path.with_name(path.name + INFO_SUFFIX).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def is_held(lock_dir=None) -> bool:
    """True when some process currently holds the lock (probe without keeping it)."""
    path = _lock_path(lock_dir)
    if str(path.resolve()) in _held:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if _try_lock(fd):
            _unlock(fd)
            return False
        return True
    finally:
        os.close(fd)


def _write_info(path: Path, owner: str) -> None:
    info = path.with_name(path.name + INFO_SUFFIX)
    tmp = info.with_name(f"{info.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps({"owner": owner, "pid": os.getpid(),
                                   "since": dt.datetime.now().astimezone().isoformat(timespec="seconds")}),
                       encoding="utf-8")
        os.replace(tmp, info)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass


def acquire(lock_dir=None, owner: str = "pipeline", wait_s: float = 0, poll_s: float = 30,
            log=print) -> bool:
    """Take the lock, waiting up to ``wait_s`` seconds for the current holder."""
    path = _lock_path(lock_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    key = str(path.resolve())
    if key in _held:
        return _held[key][1] == owner          # already ours (re-entrant for the same owner)
    deadline = time.monotonic() + max(0.0, wait_s)
    announced = False
    while True:
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
        if _try_lock(fd):
            _held[key] = (fd, owner)
            _write_info(path, owner)
            return True
        os.close(fd)
        info = holder(lock_dir) or {}
        left = deadline - time.monotonic()
        if left <= 0:
            log(f"[lock] pipeline lock held by {info.get('owner', '?')} (pid {info.get('pid', '?')}, "
                f"since {info.get('since', '?')}) — giving up")
            return False
        if not announced:
            log(f"[lock] waiting up to {left / 60:.0f} min for {info.get('owner', '?')} to finish")
            announced = True
        time.sleep(min(poll_s, left))


_job = None   # Windows Job Object handle; must stay open for the life of the process


def tie_children_to_this_process() -> bool:
    """Windows: kill every descendant when this process exits (any reason). Best effort."""
    global _job
    if os.name != "nt" or _job is not None:
        return _job is not None
    try:
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOps", "WriteOps", "OtherOps",
                                                       "ReadBytes", "WriteBytes", "OtherBytes")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("Basic", BasicLimits), ("Io", IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        job = k32.CreateJobObjectW(None, None)
        if not job:
            return False
        info = ExtendedLimits()
        info.Basic.LimitFlags = 0x2000          # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            return False                         # 9 = JobObjectExtendedLimitInformation
        if not k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()):
            return False
        _job = job
        return True
    except (OSError, AttributeError, ValueError):
        return False


def release(lock_dir=None, owner: str = "pipeline") -> None:
    """Release the lock if this process holds it for ``owner``; otherwise do nothing."""
    key = str(_lock_path(lock_dir).resolve())
    entry = _held.get(key)
    if not entry or entry[1] != owner:
        return
    fd, _ = _held.pop(key)
    _unlock(fd)
    os.close(fd)
