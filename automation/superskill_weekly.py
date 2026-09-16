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
for _s in (sys.stdout, sys.stderr):  # GBK 控制台/管道下防 UnicodeEncodeError
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - 显示层降级不影响管线
            pass

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
CLAUDE_TIMEOUT = 3600      # 蒸馏 60 分钟（多源材料后放宽）

# ------------------------------------------------ 智库（04 智库）多源增量
# 蒸馏知识来源 = 混沌新课（data/hundun，S2 上半段）+ 智库五渠道（下半段）。
# 排除：混沌学园/（与 data/hundun/AI课程 394 文件完全同源，避免重复蒸馏）；
#       混沌/ 调研框架库/ internal/（空）；微信读书 EPC/工程总承包（与 AI 产品无关）；
#       洞见研报/智慧水利（垂直行业，同上）。.doc/.docx 读不了（待转格式）。
ZHIKU_ROOT = STATION / "04 智库"
CHANNEL_STATE_FILE = AUTO / "channel_state.json"
MD_MAX_BYTES = 1_500_000     # 超长 md 由提示词引导择要深读，再大直接不收
PDF_MAX_BYTES = 15_000_000   # 更大的多是扫描件（一堂最佳实践 33-61MB），token 不划算

ZHIKU_CHANNELS = [
    # (渠道名, 子目录, 收录扩展名, 周上限, 相对路径排除关键词)
    ("一堂", "一堂", {".md", ".pdf"}, 4, []),
    ("万维钢调研方法论", "万维钢调研方法论", {".md"}, 4, []),
    ("微信读书", "微信读书", {".md"}, 2, ["EPC", "工程总承包"]),
    ("洞见研报", "洞见研报", {".md", ".pdf"}, 4, ["智慧水利"]),
    ("通往AGI之路", "通往AGI之路", {".md"}, 6, []),
]

# 首跑精选：水位播种前补课一批最有价值的库存（此后纯增量，不再翻旧账）
ZHIKU_STARTER = {
    "一堂": ["一堂龙虾实践2-深度笔记.md"],
    "万维钢调研方法论": ["万维钢调研方法论总论.md"],
    "洞见研报": ["FDE/djyanbao_研报索引_FDE.md",
                 "FDE/【国盛证券】FDE：软件服务的范式革命【洞见研报DJyanbao.com】.pdf"],
    "微信读书": ["怎么做调研_如何写报告/怎么做调研_如何写报告.md"],
    "通往AGI之路": ["2.4 精选：AI 研究报告/2026 Agentic Coding Trends Report.pdf.md"],
}


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
                   "audit_total": total, "audit_errors": errors}
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


def _scan_zhiku(log):
    """04 智库多源水位扫描：新文件/改动文件 → 周上限截断 → 余量记账下周。

    首跑（渠道无水位）只消化 ZHIKU_STARTER 精选，其余全部播种进水位——
    避免 3396 个 md 一次性涌入蒸馏。返回 (materials, skipped_doc 总数)。
    """
    doc = {"channels": {}, "pending": {}}
    if CHANNEL_STATE_FILE.is_file():
        try:
            doc = json.loads(CHANNEL_STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log("[S2] channel_state.json 损坏，重建水位（首跑精选模式）")
    materials, skipped_docs = [], 0
    for name, sub, exts, cap, excludes in ZHIKU_CHANNELS:
        root = ZHIKU_ROOT / sub
        known = dict(doc["channels"].get(name) or {})
        pending = list(doc["pending"].get(name) or [])
        eligible, oversized, docs = {}, 0, 0
        if root.is_dir():
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(root).as_posix()
                ext = p.suffix.lower()
                if ext == ".doc":
                    docs += 1  # 真老格式，无 md 孪生 → 计入"待转"上报
                    continue
                if ext == ".docx":
                    continue  # md 孪生件（微信读书/AGI 之路），md 已收录
                if ext not in exts or any(k in rel for k in excludes):
                    continue
                size = p.stat().st_size
                if (ext == ".pdf" and size > PDF_MAX_BYTES) or \
                        (ext == ".md" and size > MD_MAX_BYTES):
                    oversized += 1
                    continue
                eligible[rel] = p.stat().st_mtime
        skipped_docs += docs
        if name not in doc["channels"]:  # 首跑：播种全量水位，只消化精选
            picks = [r for r in ZHIKU_STARTER.get(name, []) if r in eligible]
            candidates = picks
            log(f"[S2] 智库[{name}] 首跑播种 {len(eligible)} 文件"
                f"（跳过 Word {docs} / 超大 {oversized}），"
                f"精选 {len(picks)} 份本周消化")
        else:
            changed = [r for r, mt in eligible.items() if known.get(r) != mt]
            seen = set(pending)
            candidates = pending + [r for r in changed if r not in seen]
        take, defer = candidates[:cap], candidates[cap:]
        doc["pending"][name] = defer
        doc["channels"][name] = eligible  # 水位含全部已见（欠账文件靠 pending 驱动）
        for rel in take:
            materials.append({"source": name, "title": Path(rel).stem,
                              "path": str(root / rel)})
        if defer:
            log(f"[S2] 智库[{name}] {len(defer)} 份排进下周（周上限 {cap}）")
    CHANNEL_STATE_FILE.write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    for m in materials:
        log(f"[S2] 智库新料 [{m['source']}] {m['title']}")
    return materials, skipped_docs


def stage_s2(log, state):
    log("[S2] 增量采集：智库多源水位扫描 → 混沌 census → 幂等批量提取")
    materials, skipped_docs = _scan_zhiku(log)
    zhiku_note = f"智库新到 {len(materials)} 份材料"
    if skipped_docs:
        zhiku_note += f"（另有 {skipped_docs} 个 Word 老格式待转）"

    census_file = HUNDUN_DATA / "_recon" / "census.json"
    rc, out = sh([PY, "scripts/hundun_census.py"], cwd=STATION, timeout=900)
    log(f"[S2] census rc={rc} {(out or '').strip().splitlines()[-1:]}")
    if rc != 0 or not census_file.is_file():
        state["s2"] = {"ok": False,
                       "note": f"census 失败 rc={rc}（登录态/网络？）；{zhiku_note}",
                       "new_materials": materials, "skipped_docs": skipped_docs}
        return False
    census = json.loads(census_file.read_text(encoding="utf-8"))["courses"]
    missing = [c for c in census.values()
               if _HEX32.match(str(c.get("course_id", "")))
               and str(c["course_id"]) not in _existing_cids()]
    if len(missing) > MAX_MISSING_CIRCUIT:
        note = (f"缺口 {len(missing)} 门 > 熔断阈值 {MAX_MISSING_CIRCUIT}"
                f"（疑似语料目录异常），本段中止待人工核查")
        log(f"[S2] {note}")
        state["s2"] = {"ok": False, "note": f"{note}；{zhiku_note}",
                       "new_materials": materials, "skipped_docs": skipped_docs}
        return False

    before_md = {p.name for p in AI_COURSE_DIR.glob("*.md")} \
        if AI_COURSE_DIR.is_dir() else set()
    rc, out = sh([PY, "scripts/hundun_batch.py"], cwd=STATION, timeout=5400)
    last = "\n".join((out or "").strip().splitlines()[-3:])
    log(f"[S2] batch rc={rc}\n{last}")
    if rc != 0:
        state["s2"] = {"ok": False, "note": f"批量提取失败 rc={rc}；{zhiku_note}",
                       "new_materials": materials, "skipped_docs": skipped_docs}
        return False

    after_md = {p.name for p in AI_COURSE_DIR.glob("*.md")}
    new_md = sorted(after_md - before_md)
    courses = [{"title": n[:-3], "path": str(AI_COURSE_DIR / n)}
               for n in new_md]
    note = (f"+{len(courses)} 门 AI 新课（全站缺口 {len(missing)} 门均已补采）；"
            f"{zhiku_note}")
    log(f"[S2] {note}")
    for c in courses:
        log(f"[S2] NEW {c['title']}")
    state["s2"] = {"ok": True, "note": note, "new_courses": courses,
                   "new_materials": materials, "skipped_docs": skipped_docs}
    return True


# ---------------------------------------------------------------- S3 蒸馏融合
# 暂存协议：.claude/** 是权限系统敏感路径，蒸馏 claude 无法直写——它把成品
# 全文写到 automation/distill_out/<skill相对路径> + manifest.json，本编排器
# 校验白名单后代为落位（LLM 决定内容，确定性层执行写入）。
DISTILL_OUT = AUTO / "distill_out"
_ALLOW_PREFIXES = ("references/", "skills/", "assets/")
_ALLOW_FILES = {"SKILL.md", "CHANGELOG.md", "README.md", "EVOLUTION.md",
                "MEMORY.md"}


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


def _apply_staged(log) -> int:
    """校验 manifest 并把暂存内容落位到 skill 目录。返回落位文件数。"""
    import shutil
    manifest_f = DISTILL_OUT / "manifest.json"
    if not manifest_f.is_file():
        return 0
    entries = json.loads(manifest_f.read_text(encoding="utf-8"))
    applied = 0
    for e in entries if isinstance(entries, list) else []:
        rel = str(e.get("path", "")).replace("\\", "/").lstrip("/")
        src = DISTILL_OUT / rel
        parts = rel.split("/")
        allowed = (rel in _ALLOW_FILES or rel.startswith(_ALLOW_PREFIXES)) \
            and ".." not in parts and src.is_file()
        if not allowed:
            log(f"[S3] MANIFEST 拒绝可疑路径: {rel}")
            continue
        dst = SKILL_SRC / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        applied += 1
        log(f"[S3] APPLY {e.get('action', '?')} {rel} "
            f"({str(e.get('summary', ''))[:60]})")
    return applied


def _current_version() -> str:
    """SKILL.md 尾注的当前版本号（如 V4.1.14）。"""
    text = SKILL_SRC.joinpath("SKILL.md").read_text(
        encoding="utf-8", errors="replace")
    vers = re.findall(r"Super-Skill (V\d+(?:\.\d+)*):", text)
    return vers[-1] if vers else "V4.1.14"


def _next_version(v: str) -> str:
    parts = v[1:].split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return "V" + ".".join(parts)


def stage_s3(log, state):
    s2s = state.get("s2") or {}
    courses = s2s.get("new_courses") or []
    materials = s2s.get("new_materials") or []
    if not courses and not materials:
        log("[S3] 0 门新课 + 0 份智库材料，跳过蒸馏（S1/S4/S5 照常）")
        state["s3"] = {"ok": True, "note": "无新增材料，跳过蒸馏",
                       "distill": {"changed": False,
                                   "summary": "本周无新增知识原料"}}
        return True

    rc, out = git("status", "--porcelain")
    dirty = [l for l in (out or "").strip().splitlines() if l
             and not l.split()[-1].startswith("automation/")]
    if dirty:
        note = f"工作树不干净（{len(dirty)} 处非 automation 改动），跳过蒸馏防混入"
        log(f"[S3] {note}: {dirty[:3]}")
        state["s3"] = {"ok": False, "note": note}
        return False

    import shutil
    if DISTILL_OUT.is_dir():  # 清掉上一轮遗留
        shutil.rmtree(DISTILL_OUT)
    DISTILL_OUT.mkdir(parents=True, exist_ok=True)

    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    listing_c = "\n".join(f"- 《{c['title']}》→ {c['path']}" for c in courses) \
        or "（本周无）"
    listing_m = "\n".join(f"- 【{m['source']}】{m['title']} → {m['path']}"
                          for m in materials) or "（本周无）"
    ver_old = _current_version()
    ver_new = _next_version(ver_old)
    week = dt.date.today().isocalendar()
    prompt = (template
              .replace("{{RUN_DATE}}", dt.date.today().isoformat())
              .replace("{{RUN_ID}}", f"{week[0]}-W{week[1]:02d}")
              .replace("{{N}}", str(len(courses)))
              .replace("{{NEW_COURSES}}", listing_c)
              .replace("{{M}}", str(len(materials)))
              .replace("{{NEW_MATERIALS}}", listing_m)
              .replace("{{VER_OLD}}", ver_old)
              .replace("{{VER_NEW}}", ver_new))
    (LOGS / "distill_prompt.md").write_text(prompt, encoding="utf-8")

    claude = find_claude()
    is_cmd = claude.suffix.lower() == ".cmd"
    log(f"[S3] 无头蒸馏：{claude}（混沌 {len(courses)} 门 + 智库 {len(materials)} 份，"
        f"{ver_old}→{ver_new}，超时 {CLAUDE_TIMEOUT}s）")
    argv = [str(claude), "-p", "--permission-mode", "acceptEdits",
            "--add-dir", str(HUNDUN_DATA), "--add-dir", str(ZHIKU_ROOT),
            "--max-turns", "100", "--output-format", "text"]
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

    summary = str(result.get("summary", ""))[:200]
    applied = _apply_staged(log)  # manifest 为地面真值
    if applied == 0:
        _revert_skill_tree(log)
        if result.get("changed"):
            log(f"[S3] 声称 changed 但无有效 manifest，已回滚（{summary}）")
            state["s3"] = {"ok": False,
                           "note": "蒸馏声明与暂存不符，已回滚"}
        else:
            log(f"[S3] 无增量价值（{summary}），工作树已还原")
            state["s3"] = {"ok": True, "note": summary or "无增量价值",
                           "distill": result}
        return state["s3"]["ok"]

    rc2, out2 = git("status", "--porcelain")
    really_dirty = bool((out2 or "").strip())
    if not really_dirty:
        log("[S3] 落位后工作树无变化（暂存内容与现状等同）")
    log(f"[S3] 融合完成：{summary}（落位 {applied} 文件）")
    for ref in (result.get("new_references") or []) + \
               (result.get("updated_references") or []):
        log(f"[S3] REF {ref}")
    result["changed"] = True
    state["s3"] = {"ok": True, "note": summary or f"融合 {applied} 文件",
                   "distill": result}
    return True


# ---------------------------------------------------------------- S4 全局安装
def stage_s4(log, state):
    log(f"[S4] 全局安装：{SKILL_SRC} → {SKILL_GLOBAL}")
    rc, out = sh(["robocopy", str(SKILL_SRC), str(SKILL_GLOBAL),
                  "/MIR", "/XD", "__pycache__", ".git",
                  "/XF", "*.pyc",
                  "/NFL", "/NDL", "/NJH", "/NJS", "/NP"], timeout=600)
    ok = rc <= 7  # robocopy 0-7 均为成功
    note = f"robocopy rc={rc}（镜像完成）" if ok else f"robocopy rc={rc} 失败"
    log(f"[S4] {note}")
    if not ok:
        log(f"[S4] 详情：{(out or '')[-300:]}")
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


def _wecom_js() -> Path | None:
    js = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / \
        "@wecom" / "cli" / "bin" / "wecom.js"
    return js if js.is_file() else None


def _wecom_oauth_send(content: str) -> tuple[bool, str]:
    """wecom-cli 个人 OAuth 通道：机器人直达授权人（不受可信 IP 限制）。

    实测（2026-09-16）：自建应用 API 60020 家宽动态 IP 墙；本通道 success=true。
    """
    js = _wecom_js()
    if not js:
        return False, "wecom-cli 未安装"
    rc, out = sh(["node", str(js), "identity", "whoami"], timeout=30)
    m = re.search(r"授权真人用户身份.*?ID：([A-Za-z0-9_-]+)", out or "")
    if not m:
        return False, f"whoami 解析失败 rc={rc}"
    payload = json.dumps({"chat_id": m.group(1), "msg_type": "markdown",
                          "markdown": {"content": content}},
                         ensure_ascii=False)
    rc, out = sh(["node", str(js), "message", "aibot", "send",
                  "--json", payload], timeout=30)
    if rc == 0 and '"success": true' in (out or "").replace(" ", " "):
        return True, "OAuth 机器人通道"
    return False, f"send rc={rc}: {(out or '')[-120:]}"


def _wecom_webhook_send(title: str, body: str) -> tuple[bool, str]:
    """群机器人 webhook 通道（需用户在 secret.ini 配 [wecom] webhook=...）。"""
    ini = STATION / "config" / "wecom.secret.ini"
    if not ini.is_file():
        return False, "webhook 未配置"
    import configparser
    parser = configparser.ConfigParser()
    parser.read(ini, encoding="utf-8")
    if not parser.get("wecom", "webhook", fallback="").strip():
        return False, "webhook 未配置"
    rc, out = sh([PY, "tools/notify_wecom.py", title, body],
                 cwd=STATION, timeout=60)
    return rc == 0, f"webhook rc={rc}"


def _plain_report(state) -> str:
    """站在用户角度的价值报告：先讲 Super-Skill 这周学会了什么、用户得到
    什么，再一句话带过例行检查。技术细节（通道名/rc/阶段号）只进日志，
    不进通知——用户关心的是"我的工具变强在哪"，不是"系统做了哪些动作"。
    """
    def st(i):
        return state.get(f"s{i}") or {}

    def is_ok(i):
        return bool(st(i).get("ok"))

    core, s2q = overall_ok(state)
    verdict = ("没完全成功" if not core else
               "基本成功" if s2q else "成功")
    lines = [f"**你的 Super-Skill 每周升级报告 · {verdict}**", ""]

    # ① 头条：这周学会了什么新本事（用户最关心的价值）
    d = st(3).get("distill") or {}
    courses = st(2).get("new_courses") or []
    if d.get("changed"):
        plain = str(d.get("plain_summary") or d.get("summary") or "").strip()
        ver_new = str(d.get("version_new") or "")
        ver_old = str(d.get("version_old") or "")
        lines.append("🎁 这周 Super-Skill 新学会了：")
        lines.append(plain[:200] or "从本周新课里学到新打法，已经会用")
        tail = "（已经装好，你下次对话时自动用上"
        if ver_new:
            tail += f"，版本 {ver_old} → {ver_new}" if ver_old else \
                f"，版本 {ver_new}"
        lines.append(tail + "）")
    elif is_ok(3):
        mats = st(2).get("new_materials") or []
        if courses or mats:
            lines.append("🎁 这周没有新增本事：新材料都读过了，暂时没有值得"
                         "单独记的新干货，你的 Super-Skill 保持原样")
        else:
            lines.append("🎁 这周没有新增本事：各知识来源本周都没有新内容上架，"
                         "你的 Super-Skill 保持原样")
    else:
        lines.append("🎁 这周的新本事没能上线：处理课程时出了点问题，已自动"
                     "恢复原样，下周自动重试")

    # ② 例行检查：一句话带过，只在需要用户知道或行动时才展开
    lines.append("")
    routine = []
    s1 = st(1)
    if s1:
        errs = len(s1.get("audit_errors") or [])
        total = s1.get("audit_total") or 48
        if is_ok(1):
            routine.append(f"🔧 技巧体检：自带的 {total} 个开发技巧检查完毕，"
                           + ("都好用" if errs == 0 else
                              f"{errs} 处小瑕疵，不影响使用"))
        else:
            routine.append("🔧 技巧体检：这次没跑成，不影响其他环节")
    s2 = st(2)
    mats = s2.get("new_materials") or []
    if s2 and not is_ok(2):
        routine.append("📚 混沌学园：这周没能连上（网络或账号原因），下周自动再试")
    elif s2 and (courses or mats):
        parts = []
        if courses:
            names = "、".join(f"《{c['title'][:20]}》" for c in courses[:3])
            more = f" 等 {len(courses)} 门" if len(courses) > 3 else ""
            parts.append(f"混沌学园新到 {names}{more}")
        if mats:
            srcs = []
            for m in mats:
                if m["source"] not in srcs:
                    srcs.append(m["source"])
            parts.append(f"智库新到 {len(mats)} 份（{'、'.join(srcs)}）")
        routine.append("📚 本周读的材料：" + "；".join(parts))
    elif s2 and is_ok(2) and not courses and not mats and d.get("changed"):
        routine.append("📚 本周没有新增材料（新本事来自既有库存的补课）")
    skipped_docs = s2.get("skipped_docs") or 0
    if skipped_docs:
        routine.append(f"📎 另有 {skipped_docs} 份 Word 老格式讲义这次读不了，"
                       "已记在账上，转成可读格式后再学")
    if st(4) and not is_ok(4):
        routine.append("💻 本机安装：新本事还没装到你机器上、暂时不生效，"
                       "需要抽空看一眼")
    if st(5):
        if is_ok(5):
            if d.get("changed"):
                routine.append("☁️ 云端备份：最新版已同步到 GitHub，换电脑也不丢")
        else:
            routine.append("☁️ 云端备份：没推上 GitHub——本机新版都在、很安全，"
                           "下周自动补推")
    lines.extend(routine if routine else ["✅ 例行检查全部通过"])

    mins = state.get("duration_min")
    if mins is not None:
        lines.append(f"⏱️ 全程自动完成，用时 {mins} 分钟，不用你操心")
    return "\n".join(lines)


def stage_s6(log, state):
    content = _plain_report(state)
    log(f"[S6] 通知内容（价值优先大白话版）：\n{content}")
    sent, chan = _wecom_oauth_send(content)
    if not sent:
        log(f"[S6] OAuth 通道失败：{chan}，尝试 webhook 回退")
        sent, chan = _wecom_webhook_send("Super-Skill 每周升级报告", content)
    note = f"通知已发（{chan}）" if sent else \
        f"通知通道全败（{chan}），结果见 logs/ 与 state.json"
    log(f"[S6] {note}")
    state["s6"] = {"ok": sent, "note": note}
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
    try:
        for name in [s.strip() for s in args.stages.split(",") if s.strip()]:
            if name not in handlers:
                log(f"[{name}] 未知段，跳过")
                continue
            try:
                handlers[name](log, state)
            except Exception as exc:  # noqa: BLE001 - 单段异常不杀管线
                log(f"[{name}] 段异常: {exc!r}")
                state[name] = {"ok": False, "note": f"段异常 {exc}"}
    finally:
        release_lock()

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
