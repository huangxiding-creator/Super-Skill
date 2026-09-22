# -*- coding: utf-8 -*-
"""Jev×Super-Skill 融合前实验（官方方法论：先实验后改实现）。

两问定生死，2026-09-22 两轮实跑：
  E1 材料预筛（routing 位）——Noul 判「材料是否值得为 AI 产品开发者蒸馏」，
     正样本=ZHIKU_STARTER 精选，负样本=EPC 工程书×2 + 飞书权限报错页×1。
  E2 manifest 核验（completion-judgment 位）——Noul 判「文件是否兑现 manifest
     声称的增量」，正样本=V4.1.15 真实 5 条 manifest，负样本=张冠李戴换绑
     2 条 + 虚构主题 1 条。
  期望：正样本 ≥0.5、负样本 <0.5（0.5=E3 实测分离缝）。

V1 教训（第一轮，状态构造缺陷而非模型错误——官方指引「Separate missing
evidence, model errors」）：E2 正样本只给头 2500 字，SKILL.md 增量在 140/
225 行与文件尾，证据缺席 → 0.16 假阴；E1 报错页只给头 1500 字，标题
"Agentic Coding" 盖过登录墙证据 → 0.54 假阳。V2 修法=code 负责证据组装：
E1 短文（<16KB）全文进 state + 剥 base64；E2 按声称关键词定向捞文件中
证据段（sde_cascade 模式：代码检索、Jev 判断）。

复用站内久经考验的 paistation.judgment.JudgmentClient（熔断/fail-soft/一键
开关三契约，E1-E3 实验谱系 2026-09-19/20）；问句措辞钉死——E3 教训：
抽象问句诱导保守 0.17-0.27，具体问句 0.94/0.08。
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # GBK 控制台防崩（同 superskill_weekly）
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

_B64 = re.compile(r"data:image/[^)\s]{200,}")  # base64 图片载荷（飞书墙页特征）

AUTO = Path(__file__).resolve().parent
REPO = AUTO.parent
STATION = Path(r"E:\AI-Station")
sys.path.insert(0, str(STATION / "src"))
from paistation.judgment.client import JudgmentClient  # noqa: E402

ZHIKU = STATION / "04 智库"
TH = 0.5  # E3 实测分离缝

# --------------------------------------------------------------- E1 材料
E1_SAMPLES = [  # (label, 渠道, 相对路径)
    ("pos", "一堂", "一堂/一堂龙虾实践2-深度笔记.md"),
    ("pos", "万维钢调研方法论", "万维钢调研方法论/万维钢调研方法论总论.md"),
    ("pos", "洞见研报", "洞见研报/FDE/djyanbao_研报索引_FDE.md"),
    ("pos", "微信读书", "微信读书/怎么做调研_如何写报告/怎么做调研_如何写报告.md"),
    ("neg", "微信读书", "微信读书/EPC工程总承包项目过程控制概论/EPC工程总承包项目过程控制概论.md"),
    ("neg", "微信读书", "微信读书/工程总承包_EPC_DB_争议解决实战攻略/工程总承包_EPC_DB_争议解决实战攻略.md"),
    ("neg", "通往AGI之路", "通往AGI之路/2.4 精选：AI 研究报告/2026 Agentic Coding Trends Report.pdf.md"),
]

E1_INSTR = "这份材料的核心内容，是否值得为「用 AI 做产品 / 做 AI 产品」的开发者从中提炼方法论或经验教训？"
E1_CRIT = {
    "true": "内容与 AI 产品开发、AI 工具实操、产品/创业方法论、调研与报告方法"
            "直接相关，能提炼出对开发者可操作的做法",
    "false": "纯垂直行业知识（工程建造/水利/法规条文等）、纯文学叙事、营销软文、"
             "或加载失败的报错页/权限页，与 AI 产品开发无直接关系",
}

# --------------------------------------------------------------- E2 manifest
E2_EXTRA_NEGATIVES = [  # (summary, staged 相对路径) —— 张冠李戴 + 虚构
    ("训虾派·AI 角色配置工程（文档=能力上限/IPO/双三角/口喷输入法/六维段位评估/民主集中会议）",
     "references/research-methodology.md"),  # 换绑：调研方法论文件 ≠ 训虾派声称
    ("V4.1.15：Idea Factory 调研读判写接线 + Phase 8 Agent 角色配置 + 版本块",
     "references/yitang-agent-forge.md"),  # 换绑：训虾派文件 ≠ SKILL 接线声称
    ("新增区块链供应链金融完整章节：链上存证三模式/智能合约五模板/跨境结算七步法",
     "references/research-methodology.md"),  # 虚构：文件里根本没有
]

E2_INSTR = "对照「声称的增量」与「文件实际内容」：该文件是否真的兑现了声称？"
E2_CRIT = {
    "true": "声称里提到的要点在文件内容中都能找到对应章节、条目或主题",
    "false": "声称提到的要点在文件中找不到，或文件内容与声称讲的是两回事",
}


def _read(path: Path) -> str:
    try:
        return _B64.sub("<图片>", path.read_text(encoding="utf-8",
                                                 errors="replace"))
    except OSError:
        return ""


def _e1_text(path: Path) -> str:
    """V2：短文全文（登录墙页全貌进 state），长文取头 4000 字。"""
    text = _read(path)
    return text if len(text) <= 16_000 else text[:4000]


_KW_SPLIT = re.compile(r"[+/，,、（）()：:；;\s—|·]+")


def _claim_keywords(claim: str, limit: int = 8) -> list[str]:
    """声称 → 检索词：≥3 字符、丢纯数字/单个字母。"""
    kws = []
    for tok in _KW_SPLIT.split(claim):
        tok = tok.strip("。.#§ ")
        if len(tok) >= 3 and not tok.isdigit() and tok not in kws:
            kws.append(tok)
    return kws[:limit]


def _e2_evidence(path: Path, claim: str) -> str:
    """V2：头 600 + 声称关键词命中的证据段（±150/250 字）+ 尾 400。"""
    text = _read(path)
    if not text:
        return ""
    parts = [f"〔开头〕{text[:600]}"]
    for kw in _claim_keywords(claim):
        i = text.find(kw)
        if i >= 0:
            parts.append(f"〔命中「{kw}」〕…{text[max(0, i - 150):i + 250]}…")
    parts.append(f"〔结尾〕{text[-400:]}")
    out = "\n".join(parts)
    return out[:6000]


def main() -> int:
    client = JudgmentClient(traj_path=AUTO / "logs" / "jev_traj.jsonl")
    if not client.enabled:
        print("[exp] Jev 开关关闭或 key 缺失，实验无法进行（fail-soft 契约下管线照旧）")
        return 2

    rows = {"e1": [], "e2": []}

    # ---- E1 材料预筛
    for label, channel, rel in E1_SAMPLES:
        p = ZHIKU / rel
        state = {"材料标题": p.stem, "来源渠道": channel,
                 "材料全文或开头": _e1_text(p)}
        noul = client.ask_noul(state, E1_INSTR, E1_CRIT)
        rows["e1"].append({"label": label, "title": p.stem, "noul": noul})
        print(f"[E1] {label} {p.stem[:28]:<30} noul={noul}")
        time.sleep(0.3)

    # ---- E2 manifest 核验（正=真实 V4.1.15 manifest；负=换绑/虚构）
    manifest = json.loads((AUTO / "distill_out" / "manifest.json")
                          .read_text(encoding="utf-8"))
    cases = [(e["summary"], e["path"]) for e in manifest] + E2_EXTRA_NEGATIVES
    labels = ["pos"] * len(manifest) + ["neg"] * len(E2_EXTRA_NEGATIVES)
    for label, (summary, rel) in zip(labels, cases):
        p = AUTO / "distill_out" / rel
        state = {"声称的增量": summary, "文件名": rel,
                 "文件证据摘录": _e2_evidence(p, summary)}
        noul = client.ask_noul(state, E2_INSTR, E2_CRIT)
        rows["e2"].append({"label": label, "file": rel, "noul": noul})
        print(f"[E2] {label} {rel[:34]:<36} noul={noul}")
        time.sleep(0.3)

    # ---- 分离度结算
    verdict = {}
    for name in ("e1", "e2"):
        pos = [r["noul"] for r in rows[name]
               if r["label"] == "pos" and r["noul"] is not None]
        neg = [r["noul"] for r in rows[name]
               if r["label"] == "neg" and r["noul"] is not None]
        sep = (min(pos) > TH >= max(neg)) if pos and neg else None
        verdict[name] = {"pos_min": min(pos) if pos else None,
                         "neg_max": max(neg) if neg else None,
                         "separated_at_0.5": sep,
                         "n_pos": len(pos), "n_neg": len(neg)}
        print(f"[{name.upper()}] pos_min={verdict[name]['pos_min']} "
              f"neg_max={verdict[name]['neg_max']} 分离={'✓' if sep else '✗'}")

    out = AUTO / "logs" / "jev_fusion_exp_20260922_v2.json"
    out.write_text(json.dumps(
        {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "threshold": TH,
         "verdict": verdict, "rows": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"[exp] 结果落盘 {out}")
    ok = all(v["separated_at_0.5"] for v in verdict.values())
    print(f"[exp] 总结论：{'两问全分离，融合放行' if ok else '存在跨界，问句/阈值需调'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
