# -*- coding: utf-8 -*-
"""Super-Skill 判断腿：Jev（TypeSafe System One）三原语接线（2026-09-22 融合）。

官方方法论（typesafe-ai skill）："identify where Jev could replace LLM-based
routing, completion judgment, or verification. Run experiments before changing
the implementation." 两问实验（automation/jev_fusion_experiments.py，
logs/jev_fusion_exp_20260922_v2.json）分离实证后产品化：

  screen_material  S2 材料预筛（routing 位）：Noul 判材料是否值得进蒸馏，
                   实测正样本 0.62-0.91 / 负样本 0.03-0.12，链接索引页
                   0.15（正确跳过——索引非内容，省 token 正是目的）。
  verify_manifest  S3 manifest 核验（completion-judgment 位）：Noul 判暂存
                   文件是否兑现声称增量，实测正 0.80-0.95 / 负（换绑+虚构）
                   0.02-0.24。

契约（继承站内 paistation.judgment 三令，09-19 深度融合谱系）：
  1. 一键开关——PAI_JEV env 硬关 > config/jev.ini enabled > key 缺失；
  2. 故障跳过——一切故障返回 None，调用方降级回原行为，绝不炸周管线；
  3. 熔断器——连续失败进冷却，防雪崩。
免费模型优先铁律：Jev 只占免费做不到的原语位（$0.0001 量级/次），
确定性检查（行数/版本脚注）用代码做，不烧判断。

问句措辞与证据组装钉死自实验 V2（V1 教训：证据缺席 ≠ 模型错误——
E1 报错页只给头部时标题盖过登录墙证据 0.54 假阳，全文进 state 后 0.12；
E2 增量在文件中后段时头采样 0.16 假阴，关键词定向捞段后 0.80+）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AUTO = Path(__file__).resolve().parent
STATION = AUTO.parents[2]                     # E:\AI-Station
try:
    sys.path.insert(0, str(STATION / "src"))
    from paistation.judgment.client import JudgmentClient  # noqa: E402
except ImportError:                            # 站外裸仓库 → 腿惰性
    JudgmentClient = None

TH = 0.5  # 分离缝（E3 谱系 + 融合 V2 实测：两侧零跨界）

_B64 = re.compile(r"data:image/[^)\s]{200,}")   # base64 图片载荷
_KW_SPLIT = re.compile(r"[+/，,、（）()：:；;\s—|·]+")

_client = None


def _jev():
    """惰性单例：开关关/熔断/站外 → None（腿全降级）。"""
    global _client
    if _client is None and JudgmentClient is not None:
        try:
            _client = JudgmentClient(
                traj_path=AUTO / "logs" / "jev_traj.jsonl")  # 调用轨迹审计
        except Exception:                       # noqa: BLE001 - fail-soft
            return None
    return _client if (_client and _client.enabled) else None


def available() -> bool:
    return _jev() is not None


# --------------------------------------------------------------- 证据组装
def material_text(path: Path, max_chars: int = 4000) -> str:
    """md 全文（<16KB）或头 4000 字；pdf 取前 3 页文本；base64 剥除。"""
    try:
        if path.suffix.lower() == ".pdf":
            import pymupdf  # 延迟导入，站外无依赖也不影响 md 路径
            with pymupdf.open(str(path)) as doc:
                text = "\n".join(pg.get_text() for pg in doc[:3])
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:                           # noqa: BLE001 - 读不了→空证据
        return ""
    text = _B64.sub("<图片>", text)
    return text if len(text) <= 16_000 else text[:max_chars]


def _claim_keywords(claim: str, limit: int = 8) -> list[str]:
    kws = []
    for tok in _KW_SPLIT.split(claim):
        tok = tok.strip("。.#§ ")
        if len(tok) >= 3 and not tok.isdigit() and tok not in kws:
            kws.append(tok)
    return kws[:limit]


def evidence_spans(text: str, claim: str) -> str:
    """头 600 + 声称关键词命中段（±150/250）+ 尾 400，封顶 6000 字。"""
    if not text:
        return ""
    parts = [f"〔开头〕{text[:600]}"]
    for kw in _claim_keywords(claim):
        i = text.find(kw)
        if i >= 0:
            parts.append(f"〔命中「{kw}」〕…{text[max(0, i - 150):i + 250]}…")
    parts.append(f"〔结尾〕{text[-400:]}")
    return "\n".join(parts)[:6000]


# --------------------------------------------------------------- S2 预筛腿
_S1_INSTR = ("这份材料的核心内容，是否值得为「用 AI 做产品 / 做 AI 产品」的"
             "开发者从中提炼方法论或经验教训？")
_S1_CRIT = {
    "true": "内容与 AI 产品开发、AI 工具实操、产品/创业方法论、调研与报告方法"
            "直接相关，能提炼出对开发者可操作的做法",
    "false": "纯垂直行业知识（工程建造/水利/法规条文等）、纯文学叙事、营销软文、"
             "或加载失败的报错页/权限页，与 AI 产品开发无直接关系",
}


def screen_material(title: str, channel: str, path: Path) -> float | None:
    """材料 → 值得蒸馏的概率。None=Jev 缺席（不筛，保持原行为）。"""
    jev = _jev()
    if jev is None:
        return None
    return jev.ask_noul(
        {"材料标题": title, "来源渠道": channel,
         "材料全文或开头": material_text(path)},
        _S1_INSTR, _S1_CRIT)


# --------------------------------------------------------------- S3 核验腿
_S2_INSTR = "对照「声称的增量」与「文件实际内容」：该文件是否真的兑现了声称？"
_S2_CRIT = {
    "true": "声称里提到的要点在文件内容中都能找到对应章节、条目或主题",
    "false": "声称提到的要点在文件中找不到，或文件内容与声称讲的是两回事",
}


def verify_manifest(summary: str, rel: str, file_text: str) -> float | None:
    """manifest 条目 → 兑现概率。None=Jev 缺席（记 unchecked，不算失败）。"""
    jev = _jev()
    if jev is None:
        return None
    return jev.ask_noul(
        {"声称的增量": summary, "文件名": rel,
         "文件证据摘录": evidence_spans(file_text, summary)},
        _S2_INSTR, _S2_CRIT)
