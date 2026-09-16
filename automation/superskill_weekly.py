# -*- coding: utf-8 -*-
"""Super-Skill 周度自升级管线（无人值守）。

Windows 计划任务「SuperSkillWeekly」每周日 22:00（北京时间）拉起：
  S1 子技能升级   npx skills update -g + 48 个内嵌子技能结构审计
  S2 混沌增量采集 census 刷新 → 幂等批量提取（0.2s 节流 / 403 自动重登 /
                  新课缺口 > 40 熔断）→ 圈出本周 AI 新课
  S3 智能蒸馏融合 无头 claude 蒸馏新课 → 识别增量价值 → 融合进
                  references/ + SKILL.md 接线 + CHANGELOG + 版本号；
                  失败或无增量 → 回滚（干净工作树闸门防混入人工改动）
  S4 全局安装     robocopy 镜像 → %USERPROFILE%\\.claude\\skills\\super-skill
  S5 Git 提交推送 git push → 剥代理重推 → gh api 数据通道（三层回退）
  S6 企微通知     tools/notify_wecom.py 摘要（成功/失败均通知）

运维：
  暂停   新建 automation/PAUSE 文件（main 首行早退，免提权）
  恢复   删除该文件
  手跑   automation/run_now.cmd（前台看全程输出）
  日志   automation/logs/weekly_*.log + state.json
  单段   python superskill_weekly.py --stages s2,s3

安全红线：凭据只经 config/hundun.secret.ini（gitignored）由既有脚本读取，
本文件不接触任何凭据；账号安全 = 既有 0.2s 节流 + 周级低频 + 缺口熔断。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout is None:  # pythonw 无控制台
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# ---------------------------------------------------------------- 路径常量
REPO = Path(__file__).resolve().parents[1]          # 07 任务/Super-Skill
AUTO = REPO / "automation"
STATION = Path(r"E:\AI-Station")
SKILL_SRC = REPO / ".claude" / "skills" / "super-skill"
SKILL_GLOBAL = Path.home() / ".claude" / "skills" / "super-skill"
HUNDUN_DATA = STATION / "data" / "hundun"
AI_COURSE_DIR = HUNDUN_DATA / "AI课程"
OTHER_BASE = HUNDUN_DATA / "课程资料"
PY = sys.executable                                  # venv python(w).exe
LOGS = AUTO / "logs"
PAUSE_FLAG = AUTO / "PAUSE"
LOCK_FILE = LOGS / "weekly.lock"
STATE_FILE = AUTO / "state.json"
PROMPT_TEMPLATE = AUTO / "weekly_distill_prompt.md"

NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW（不弹窗铁律）
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
MAX_MISSING_CIRCUIT = 40   # 混沌缺口熔断阈值（正常周增量 0~5 门）
CLAUDE_TIMEOUT = 2700      # 蒸馏 45 分钟


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- 基础设施
class Tee:
    """日志同时落 journal 与 stdout。"""

    def __init__(self, path: Path):
        self.fh = open(path, "a", encoding="utf-8", buffering=1)

    def __call__(self, msg: str = ""):
        line = f"{now()} {msg}" if msg else ""
        print(line, flush=True)
        self.fh.write(line + "\n")

    def close(self):
        self.fh.close()


def sh(args, cwd=None, timeout=300, input_text=None, is_cmd=False):
    """统一子进程：无窗口、UTF-8 宽容解码。返回 (rc, stdout)。"""
    argv = args if is_cmd else [str(a) for a in args]
    if is_cmd:  # .cmd/.bat 必须经 cmd /c
        argv = ["cmd", "/c"] + [str(a) for a in args]
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        p = subprocess.run(
            argv, cwd=str(cwd) if cwd else None, timeout=timeout,
            input=input_text.encode("utf-8") if input_text else None,
            capture_output=True, creationflags=NO_WINDOW, env=env)
        out = (p.stdout or b"").decode("utf-8", errors="replace")
        err = (p.stderr or b"").decode("utf-8", errors="replace")
        return p.returncode, (out + ("\n[stderr] " + err if err.strip() else ""))
    except subprocess.TimeoutExpired:
        return 124, f"[timeout after {timeout}s]"
    except Exception as exc:  # noqa: BLE001 - 单段异常不杀管线
        return 125, f"[spawn-fail] {exc}"


def git(*args, timeout=120):
    return sh(["git", *args], cwd=REPO, timeout=timeout)


def find_claude() -> Path:
    """可用的 claude 二进制：VSCode 扩展原生包（按版本号取最新）优先。

    npm 全局 shim 在本机 Win10 19045 报「不支持当前 Windows 版本」，
    扩展原生 claude.exe 实测可用（2.1.272，认证共享）。
    """
    ext_root = Path.home() / ".vscode" / "extensions"
    if ext_root.is_dir():
        cands = []
        for p in ext_root.glob("anthropic.claude-code-*/resources/"
                               "native-binary/claude.exe"):
            m = re.search(r"claude-code-(\d+(?:\.\d+)*)", str(p))
            key = tuple(int(x) for x in m.group(1).split(".")) if m else (0,)
            cands.append((key, p))
        if cands:
            return max(cands)[1]
    return Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd"


# ---------------------------------------------------------------- 锁与旗标
def acquire_lock(log) -> bool:
    if LOCK_FILE.exists():
        age_h = (time.time() - LOCK_FILE.stat().st_mtime) / 3600
        if age_h < 8:
            log(f"[lock] 已有实例在跑（{age_h:.1f}h 前），退出")
            return False
        log(f"[lock] 陈锁（{age_h:.1f}h），破锁续跑")
        LOCK_FILE.unlink(missing_ok=True)
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock():
    LOCK_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------- S1 子技能
def stage_s1(log, state):
    log("[S1] 子技能升级：npx skills update -g + 内嵌子技能结构审计")
    rc, out = sh(["npx", "-y", "skills", "update", "-g", "-y"],
                 cwd=STATION, timeout=420, is_cmd=True)
    tail = "\n".join((out or "").strip().splitlines()[-6:])
    log(f"[S1] npx skills rc={rc}\n{tail}")
    npx_note = "npx skills update 完成" if rc == 0 else \
        f"npx skills update 异常 rc={rc}（best-effort，不挡管线）"

    # 内嵌 48 子技能结构审计（frontmatter / name==目录 / 正文 ≤500 行）
    errors, total = [], 0
    skills_dir = SKILL_SRC / "skills"
    for d in sorted(skills_dir.iterdir()) if skills_dir.is_dir() else []:
        if not d.is_dir():
            continue
        total += 1
        sm = d / "SKILL.md"
        if not sm.is_file():
            errors.append(f"{d.name}: 缺 SKILL.md")
            continue
        text = sm.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            errors.append(f"{d.name}: 缺 frontmatter")
        m = re.search(r"^name:\s*(\S+)", text, re.M)
        if not m or m.group(1) != d.name:
            errors.append(f"{d.name}: name 与目录不符")
        if text.count("\n") + 1 > 500:
            errors.append(f"{d.name}: 正文超 500 行")
    audit_note = f"审计 {total} 个子技能，{len(errors)} 处问题"
    if errors:
        for e in errors:
            log(f"[S1] AUDIT {e}")
    log(f"[S1] {audit_note}")
    state["s1"] = {"ok": True, "note": f"{npx_note}；{audit_note}",
                   "audit_errors": errors}
    return True


# ---------------------------------------------------------------- S2 混沌增量
def _existing_cids() -> set:
    done = set()
    dirs = [AI_COURSE_DIR]
    if OTHER_BASE.is_dir():
        dirs += [d for d in OTHER_BASE.iterdir() if d.is_dir()]
    for d in dirs:
        if not d.is_dir():
            continue
        for name in os.listdir(d):
            if name.endswith(".json") and _HEX32.match(name[:-5]):
                done.add(name[:-5])
    return done


def stage_s2(log, state):
    log("[S2] 混沌增量：census 刷新 → 缺口熔断检查 → 幂等批量提取")
    census_file = HUNDUN_DATA / "_recon" / "census.json"
    rc, out = sh([PY, "scripts/hundun_census.py"], cwd=STATION, timeout=900)
    log(f"[S2] census rc={rc} {(out or '').strip().splitlines()[-1:]}")
    if rc != 0 or not census_file.is_file():
        state["s2"] = {"ok": False, "note": f"census 失败 rc={rc}（登录态/网络？）"}
        return False
    census = json.loads(census_file.read_text(encoding="utf-8"))["courses"]
    missing = [c for c in census.values()
               if _HEX32.match(str(c.get("course_id", "")))
               and str(c["course_id"]) not in _existing_cids()]
    if len(missing) > MAX_MISSING_CIRCUIT:
        note = (f"缺口 {len(missing)} 门 > 熔断阈值 {MAX_MISSING_CIRCUIT}"
                f"（疑似语料目录异常），本段中止待人工核查")
        log(f"[S2] {note}")
        state["s2"] = {"ok": False, "note": note}
        return False

    before_md = {p.name for p in AI_COURSE_DIR.glob("*.md")} \
        if AI_COURSE_DIR.is_dir() else set()
    rc, out = sh([PY, "scripts/hundun_batch.py"], cwd=STATION, timeout=5400)
    last = "\n".join((out or "").strip().splitlines()[-3:])
    log(f"[S2] batch rc={rc}\n{last}")
    if rc != 0:
        state["s2"] = {"ok": False, "note": f"批量提取失败 rc={rc}"}
        return False

    after_md = {p.name for p in AI_COURSE_DIR.glob("*.md")}
    new_md = sorted(after_md - before_md)
    courses = [{"title": n[:-3], "path": str(AI_COURSE_DIR / n)}
               for n in new_md]
    note = f"+{len(courses)} 门 AI 新课（全站缺口 {len(missing)} 门均已补采）"
    log(f"[S2] {note}")
    for c in courses:
        log(f"[S2] NEW {c['title']}")
    state["s2"] = {"ok": True, "note": note, "new_courses": courses}
    return True


# ---------------------------------------------------------------- S3 蒸馏融合
def _revert_skill_tree(log):
    log("[S3] 回滚蒸馏产生的部分改动")
    git("checkout", "--", ".")
    git("clean", "-fd", ".claude/skills/super-skill")


def _parse_result_json(text: str):
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not blocks:
        return None
    try:
        return json.loads(blocks[-1])
    except json.JSONDecodeError:
        return None


def stage_s3(log, state):
    courses = (state.get("s2") or {}).get("new_courses") or []
    if not courses:
        log("[S3] 0 门新课，跳过蒸馏（S1/S4/S5 照常）")
        state["s3"] = {"ok": True, "note": "无新课，跳过蒸馏",
                       "distill": {"changed": False,
                                   "summary": "本周无混沌新课"}}
        return True

    rc, out = git("status", "--porcelain")
    dirty = [l for l in (out or "").strip().splitlines() if l
             and not l.split()[-1].startswith("automation/")]
    if dirty:
        note = f"工作树不干净（{len(dirty)} 处非 automation 改动），跳过蒸馏防混入"
        log(f"[S3] {note}: {dirty[:3]}")
        state["s3"] = {"ok": False, "note": note}
        return False

    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    listing = "\n".join(f"- 《{c['title']}》→ {c['path']}" for c in courses)
    week = dt.date.today().isocalendar()
    prompt = (template
              .replace("{{RUN_DATE}}", dt.date.today().isoformat())
              .replace("{{RUN_ID}}", f"{week[0]}-W{week[1]:02d}")
              .replace("{{N}}", str(len(courses)))
              .replace("{{NEW_COURSES}}", listing))
    (LOGS / "distill_prompt.md").write_text(prompt, encoding="utf-8")

    claude = find_claude()
    is_cmd = claude.suffix.lower() == ".cmd"
    log(f"[S3] 无头蒸馏：{claude}（{len(courses)} 门，超时 {CLAUDE_TIMEOUT}s）")
    argv = [str(claude), "-p", "--permission-mode", "acceptEdits",
            "--add-dir", str(HUNDUN_DATA),
            "--max-turns", "80", "--output-format", "text"]
    rc, out = sh(argv, cwd=REPO, timeout=CLAUDE_TIMEOUT,
                 input_text=prompt, is_cmd=is_cmd)
    (LOGS / "distill_output.md").write_text(out or "", encoding="utf-8")
    result = _parse_result_json(out or "")
    if rc != 0 or result is None:
        _revert_skill_tree(log)
        note = f"蒸馏异常 rc={rc}（结果 JSON 缺失或崩溃），已回滚"
        log(f"[S3] {note}")
        state["s3"] = {"ok": False, "note": note}
        return False

    changed = bool(result.get("changed"))
    summary = str(result.get("summary", ""))[:200]
    if not changed:
        rc2, out2 = git("status", "--porcelain")
        still = [l for l in (out2 or "").strip().splitlines() if l]
        if still:
            _revert_skill_tree(log)
        log(f"[S3] 无增量价值（{summary}），工作树已还原")
    else:
        log(f"[S3] 融合完成：{summary}")
        for ref in (result.get("new_references") or []) + \
                   (result.get("updated_references") or []):
            log(f"[S3] REF {ref}")
    state["s3"] = {"ok": True,
                   "note": summary or ("融合 " + str(len(courses)) + " 门"),
                   "distill": result}
    return True


# ---------------------------------------------------------------- S4 全局安装
def stage_s4(log, state):
    log(f"[S4] 全局安装：{SKILL_SRC} → {SKILL_GLOBAL}")
    rc, out = sh(["robocopy", str(SKILL_SRC), str(SKILL_GLOBAL),
                  "/MIR", "/XD", "__pycache__", ".git",
                  "/XF", "*.pyc",
                  "/NFL", "/NDL", "/NJ", "/NJS", "/NP"], timeout=600)
    ok = rc <= 7  # robocopy 0-7 均为成功
    note = f"robocopy rc={rc}（镜像完成）" if ok else f"robocopy rc={rc} 失败"
    log(f"[S4] {note}")
    state["s4"] = {"ok": ok, "note": note}
    return ok


# ---------------------------------------------------------------- S5 提交推送
def stage_s5(log, state):
    distill = (state.get("s3") or {}).get("distill") or {}
    summary = distill.get("summary") or "周度自升级（子技能审计 + 混沌语料巡检）"
    date = dt.date.today().isoformat()

    rc, out = git("status", "--porcelain")
    dirty = bool((out or "").strip())
    if dirty:
        msg = (f"feat(super-skill): 周度自升级 {date} — {summary}\n\n"
               f"- 子技能: npx skills update + 结构审计\n"
               f"- 混沌: {(state.get('s2') or {}).get('note', '-')}\n"
               f"- 蒸馏: {summary}\n"
               f"- 全局安装: robocopy 镜像\n\n"
               f"Co-Authored-By: Claude Code <noreply@anthropic.com>\n")
        git("add", "-A")
        rc, out = git("commit", "-m", msg)
        log(f"[S5] commit rc={rc} {(out or '').strip().splitlines()[-1:]}")
        if rc != 0:
            state["s5"] = {"ok": False, "note": "git commit 失败"}
            return False
    else:
        log("[S5] 无待提交改动")

    # 三层推送回退：直连 git → 剥代理 git → gh api 数据通道
    layers = [
        ("git-push", lambda: git("push", "origin", "master", timeout=150)[0] == 0),
        ("git-push-noproxy",
         lambda: git("-c", "http.https://github.com.proxy=", "push",
                     "origin", "master", timeout=150)[0] == 0),
        ("gh-api",
         lambda: sh([PY, str(AUTO / "api_push.py")], cwd=REPO,
                    timeout=420)[0] == 0),
    ]
    for name, fn in layers:
        rc = fn()
        if rc:
            log(f"[S5] 推送成功（通道：{name}）")
            state["s5"] = {"ok": True, "note": f"已推送（{name}）",
                           "layer": name}
            return True
        log(f"[S5] 通道 {name} 失败，降级下一层")
    state["s5"] = {"ok": False, "note": "三层推送通道全部失败（本地提交已保留）"}
    return False


# ---------------------------------------------------------------- 汇总与通知
def overall_ok(state) -> tuple[bool, bool]:
    """返回 (整体成功, 混沌段隔离失败)。S2 按设计隔离：失败不判整体 ❌。"""
    core = all((state.get(f"s{i}") or {}).get("ok") for i in (1, 3, 4, 5))
    s2 = state.get("s2") or {}
    return core, core and not s2.get("ok", False)


def stage_s6(log, state):
    icons = {True: "✅", False: "❌"}
    ok, s2_quarantined = overall_ok(state)
    if ok and s2_quarantined:
        verdict = "⚠️ 主链成功·混沌段隔离"
    else:
        verdict = "✅ 成功" if ok else "❌ 失败"
    title = f"Super-Skill 周度自升级 {verdict}"
    lines = []
    for i in range(1, 6):
        st = state.get(f"s{i}") or {}
        lines.append(f"S{i} {icons.get(bool(st.get('ok')), '⚠️')} "
                     f"{(st.get('note') or '未运行')[:80]}")
    courses = (state.get("s2") or {}).get("new_courses") or []
    for c in courses[:10]:
        lines.append(f"- 新课《{c['title'][:40]}》")
    if len(courses) > 10:
        lines.append(f"- …等 {len(courses)} 门")
    lines.append(f"耗时 {state.get('duration_min', '?')} 分钟")
    body = "\n".join(lines)
    rc, _ = sh([PY, "tools/notify_wecom.py", title, body],
               cwd=STATION, timeout=60)
    log(f"[S6] 企微通知 rc={rc}")
    state["s6"] = {"ok": rc == 0, "note": "通知已发" if rc == 0 else "通知失败"}
    return True


# ---------------------------------------------------------------- 主流程
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="superskill_weekly")
    parser.add_argument("--stages", default="s1,s2,s3,s4,s5,s6",
                        help="逗号分隔，如 s2,s3")
    args = parser.parse_args(argv)

    LOGS.mkdir(parents=True, exist_ok=True)
    if PAUSE_FLAG.exists():
        STATE_FILE.write_text(json.dumps(
            {"last_run": now(), "last_result": "paused",
             "note": "PAUSE 旗标生效，整轮跳过"}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"{now()} [pause] PAUSE 旗标生效，本轮跳过", flush=True)
        return 0
    if not acquire_lock(lambda m: print(m, flush=True)):
        return 0

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log = Tee(LOGS / f"weekly_{ts}.log")
    t0 = time.time()
    state = {"last_run": now(), "stages": {}}
    log(f"===== Super-Skill 周度自升级 开始（pid={os.getpid()}） =====")
    log(f"REPO={REPO}")

    handlers = {"s1": stage_s1, "s2": stage_s2, "s3": stage_s3,
                "s4": stage_s4, "s5": stage_s5, "s6": stage_s6}
    for name in [s.strip() for s in args.stages.split(",") if s.strip()]:
        if name not in handlers:
            log(f"[{name}] 未知段，跳过")
            continue
        try:
            handlers[name](log, state)
        except Exception as exc:  # noqa: BLE001 - 单段异常不杀管线
            log(f"[{name}] 段异常: {exc!r}")
            state[name] = {"ok": False, "note": f"段异常 {exc}"}

    state["duration_min"] = round((time.time() - t0) / 60, 1)
    state["last_run_ok"], state["s2_quarantined"] = overall_ok(state)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    log(f"===== 结束（{state['duration_min']} 分钟，"
        f"整体 {'OK' if state['last_run_ok'] else 'FAIL'}） =====")
    log.close()
    release_lock()
    return 0 if state["last_run_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
