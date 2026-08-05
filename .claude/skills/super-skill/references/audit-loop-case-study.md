# Run-Log-Driven Audit Loop — a case study from We-AIPO

> **Source**: the We-AIPO project (`自媒永动机`, `E:\CPOPC\We-AIPO`) — a WeChat-ecosystem
> content-autonomy engine: **126 Python modules · 218 tests · 78 deep optimizations ·
> 11/11 unattended stages · 290 commits in ~2 weeks**. This reference distills the
> development methodology that produced those numbers so Super-Skill can reuse it.
>
> It is a concrete, evidenced realization of Super-Skill's **Phase 10 (Ralph Loop)** and
> **Phase 9 (QA gates)**. Invoke this pattern whenever a run/iteration underperforms or
> when doing a Phase-10 optimization round.

## TL;DR — the 5 reusable patterns

| # | Pattern | One-line | We-AIPO evidence |
|---|--------|----------|------------------|
| 1 | **Run-log-driven audit** | Start every round from a reconstructed run timeline + waste calculation, never from speculation | each `PROPOSAL_ROUND*.md` opens with minute-by-minute run timeline + "有效产出4h / 浪费1.5h" |
| 2 | **Root-cause-before-fix** | Name the exact root cause with before/after code; explicitly rule out wrong hypotheses | "不是 `set_output_language` 的问题…是 `generate_video(language='zh')` 参数本身" |
| 3 | **Numbered, scoped fixes** | Tag each fix (S1-S5, F1-F5) and bind it to specific files in an impl table | every round ships an "实施" table: # / item / file-to-modify |
| 4 | **Fail-closed multi-judge gates** | Thresholds + ≥2 judges + explicit gates; never let bad output pass silently | GLM+DeepSeek 双裁判 阈值80 fail-closed · U1–U4 + H1/H2 quality gates · Q5 low-score retry |
| 5 | **Cumulative-metric tracking** | Track optimization-count / test-count / unattended-audit across rounds as the success signal | badges drift upward: 65→78项优化 · 211→218 tests · 11/11 unattended |

---

## Pattern 1 — Run-log-driven audit (the core discipline)

The single biggest difference between We-AIPO's optimization rounds and ad-hoc fixing:
**every round begins with data, not opinion.** Reconstruct what the last run *actually* did,
minute by minute, and quantify waste before proposing anything.

```text
10:00 第1次启动 → wx_channel UAC超时 → 0产出（1分钟浪费）
10:55 第3次启动 → RSS缓存跳过 → 0产出（15分钟浪费）
11:13 第4次启动 → 成功 ✅
  11:13-14:03 RSS扫描 436源（170分钟！太慢）
  14:43-15:19 NotebookLM视频（CDN token过期 → 0视频）
实际有效产出时间：4小时   浪费时间：1.5小时
```

**Why it works**: "the run felt slow" produces no fix targets; "170 min on RSS, 15 min wasted on 3 failed starts" produces exactly two. This is the Ralph Loop's *Analyze* step done honestly — turn the fuzzy feeling into a clear list (same spirit as `weekly_retrospective.py`).

## Pattern 2 — Root-cause-before-fix

Every fix names the **exact** root cause and shows before/after code. Crucially, it *rules out the wrong hypothesis* before committing the fix — this prevents the most expensive failure mode, fixing a symptom.

```python
# 根因（not the suspected set_output_language — that was already removed）:
#   generate_video(language="zh")  → 中文字体缺失 → 字幕空框■■■
# 修复前:  generate_video(language=language)   # language ctx 默认 "zh"
# 修复后:  generate_video(language="en")       # 英文字幕正常; 配音仍中文 (via instructions)
```

**Why it works**: the one-line "不是 X 的问题，是 Y" prevents re-fixing the same symptom next round. This is Super-Skill's **Iceberg Rule** (one problem in → one category out) made literal.

## Pattern 3 — Numbered, scoped fixes + implementation table

Each round ships a fixed, scannable shape: a handful of numbered fixes, each bound to the file(s) it touches.

| # | item | file |
|---|------|------|
| S1 | watchdog 连接后停止操作微信窗口 | `watchdog.py` |
| S2 | RSS 休息 129s→30s, 扫描 5s→3s | `rss_source.py` |
| S3 | UAC 超时 30s→60s + 自动重试 | `channels_fetcher.py` |
| S4 | 每篇大脑回答前检查 session + 重试3次 | `metaso_brain.py` |
| S5 | 下载失败自动重新生成 (fresh token) | `notebooklm_video.py` |

**Why it works**: small batches (5-ish), each independently shippable and testable, each traceable in the commit log (`fix: S1-S5 第六轮——...`). This is the Autonomous Loop's *small-commit* rule with a persistent round counter.

## Pattern 4 — Fail-closed multi-judge quality gates

No stage trusts a single judgment. The filter uses **two** judges (GLM-4-FlashX + DeepSeek) on 4 dimensions, threshold 80, **fail-closed** (ambiguous → reject). The pipeline runs a full quality mesh:

- **U1–U4** (upstream): 问题难度 / 人设风格 / 回复深度 / 去套话
- **H1/H2** (headline): 标题 CTR / 视频钩子
- **Q5**: low-score → retry (not discard-and-continue)
- `health_guard.py` — business-level health check + **graceful degradation**
- `pipeline_checkpoint.py` — 断点续跑 (resume after failure)

**Why it works**: this is Super-Skill's **Variance Inequality** (*strengthen the verifier, not the generator*) in production — a weak single-judge gate is the bottleneck; a fail-closed multi-judge gate makes the whole pipeline trustworthy enough to run unattended.

## Pattern 5 — Cumulative-metric tracking

Three numbers drift upward across rounds and are surfaced as badges: **optimization count** (65→78), **test count** (211→218), **unattended-audit** (11/11 stages). They are the *success signal* — if a round lands and a number goes *down*, the round failed.

**Why it works**: it gives every round a falsifiable pass/fail criterion (Super-Skill's "metric improved" KEEP rule) and makes regression visible immediately.

---

## Reusable audit-proposal template

Copy this shape at the start of each Phase-10 round (or after any failed/underperforming run):

```markdown
# 第 N 轮审计提案 —— 基于 <date> 运行记录深度分析

## 运行时间线（实际问题）
<minute-by-minute reconstruction of the last run, with waste time calculated>
有效产出时间：__   浪费时间：__

## 必须解决的 K 个问题
### <id1>. <problem title>
- 问题：<observed symptom, with the number>
- 根因：<exact root cause — rule out the wrong hypothesis explicitly>
- 修复：<before/after code or concrete change>

### <id2>. ...

## 实施
| # | item | file |
|---|------|------|
| <id1> | ... | <path> |
```

Tag commits `<type>: <id1>-<idK> 第N轮——<summary>` so the round is traceable in `git log`.

## How this maps back into Super-Skill

| We-AIPO pattern | Super-Skill home |
|-----------------|------------------|
| Run-log-driven audit | Phase 10 Ralph Loop *Analyze*; `ai-mastery-7/weekly_retrospective.py` |
| Root-cause-before-fix | Phase 8 Iceberg Rule; `systematic-debugging` |
| Numbered scoped fixes | Phase 8 small-commit rule; Autonomous Loop |
| Fail-closed multi-judge gates | Phase 9 QA; `verification-gate`; Variance Inequality |
| Cumulative-metric tracking | Phase 10 convergence; `health_check.py` |

**Packaged as GEP Capsule** `capsule_we_aipo_audit_loop_20260805` in `assets/gep/capsules.json` —
reusable by `darwin-evolution` so future projects inherit the pattern without re-deriving it.
