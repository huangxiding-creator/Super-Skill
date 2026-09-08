# 开发宪法 — Development Constitution

> **Status**: non-negotiable. **V2 (2026-09-08)** — V1 distilled the author's CC
> interaction records and We-AIPO. V2 is a full-portfolio expansion: the 438-page
> 《总包大脑实战方案》 plus ~40 delivered projects mined across `E:\CPOPC` and
> `E:\AIResearch` (RSS-Auto 105 commits/303 tests · Fund-Fortune 83 tests ·
> ZBBrain-LIVE5 113 tests · ResearchFactory-Eng 233 commits/762 tests ·
> WeArticleDS3 158 tests · WeChat-AutoPub 73 tests · KnowFactory-PRO20 191 videos…).
> A constitution article is not a guideline: **violation = stop and redo the phase**,
> not "preferably next time".
>
> Sources: `优化改进建议/AI开发项目全流程经验提炼与开发宪法更新指南_Transcript_2026-09-08.docx`
> · `优化改进建议/总包大脑实战方案.pdf` (materials stay on disk, never committed —
> they contain live credentials; see R11).
>
> **Companion layers** (both 全局适配版, extracted from their projects 2026-09-07/08):
> [weaipo-constitution.md](weaipo-constitution.md) is the runtime constitution for
> unattended production systems (12 principles + 12 stop-on-sight violations + a
> conflict-adjudication order); [pai-station-doctrine.md](pai-station-doctrine.md) is
> the value/methodology adjudication layer (10+ project comparison, 难度=价值 density
> formula, opt-in iron law, kill criteria). This file is the proposal/
> research/plan/collaboration core that binds them into the phase workflow.
>
> **Operational companion**: [cc-command-playbook.md](cc-command-playbook.md) — the
> author's proven CC instruction templates, iteration budgets, cadence parameters,
> and tool matrix that make these articles executable. The constitution says WHAT
> must always hold; the playbook is the copy-paste HOW.

## 序 — Why a constitution

An initial idea arrives bounded by the author's 认知/视野/经历 (cognition, vision,
experience) — it is timid by default ("初步想法可能没有这么大胆"). Every mechanism below
exists to push past that ceiling at the exact phase where the leverage is highest, and to
make the recurring hard-won rules of delivered projects impossible to forget. The
constitution binds the generator (plans, proposals, code) from above; the phase gates and
verifiers enforce it from below.

The constitution's own origin story is a diagnosis: the PDF self-identifies Super-Skill's
three chronic diseases — **运行时不先自更新、不严格执行全部步骤、结束不复盘**. Pre-run
upgrade, phase gates, and post-run evolution are the three cures; this document makes
them obligations instead of features.

## 甲部 — 提案宪法 (Proposal Articles)

### C1 — 解决最难的问题 · Target the hardest problem
The proposal must target the **hardest real problem with genuine value** in its domain.
The hardest problems are the most worth solving — a truly solved hard problem is where
all the value lives. A "差不多的方案" (good-enough plan) or a comfortable pivot to an
easier problem is **unconstitutional at the proposal stage**. Do not fear the challenge.

*V2 evidence*: Fund-Fortune's proposal opens with **"为什么原始想法直接实现会失败的四个
陷阱"** and converts each trap into a moat with unit tests (Wilson 下界/相关约束/防未来
函数/费率幻觉, each annotated with its src file). A constitutional proposal argues
against its own naive version before proposing the ten× one.

### C2 — 大胆想象，天马行空合法 · Boldness is legal, timidity is not
At proposal time, imagination must be maximally open — even things previously considered
难以想象/难以实现 (unthinkable, infeasible) belong **in the proposal**. Constraints are
negotiated later, at architecture and WBS; the proposal itself must not be pre-shrunk.
The Idea Factory's ambiguity gate must never become a boldness gate.

### C3 — 世界最优且可落地 · World-best, and landable
After researching GitHub and the open network, the proposal's plan must be the **current
world-best implementable approach** — not the locally-known best, not the first workable
one. "最难实现" is acceptable; "不是最优" is not. Hard-to-implement has known breaking
points (decompose, prototype, iterate); suboptimal has none.

## 乙部 — 调研宪法 (Research Articles)

### C4 — 站在巨人肩膀上 · Stand on the shoulders of giants
Never build from scratch what the world already built well. Research first, find the
**top-tier existing work**, then build on it — cloning and adapting, even 缝合/粘贴/
复制/抄作业 (stitch, paste, copy, homework-copy; license permitting), is the correct and
highest-efficiency path. 从零造轮子 ("低级开发") is a constitutional violation: it wastes
the one resource a small team cannot buy back — time. **开工前先吃透存量**: "对本项目
现有开发成果全面了解熟悉，为不重复造轮子做好准备" — this applies to the author's own
past projects as much as to GitHub.

*V2 evidence*:
- **三级借用** (from OpenClaw practice): 设计纪律照抄 · 协议层参考实现 · 伴生网关可逆共存 — borrow maximally, but a giant's shoulders is not a giant's地基.
- **逆向工程也是站在巨人肩上** (read-only): 秘塔上传端点由 service-worker 抓包逆向 (GCBrain) · RE-Factory 38 端点 · Linzhu-Auto 28 端点/100 次压测 99% — 逆向用于理解协议，不越 R7/R8 红线。
- **选型必须实测成矩阵**: RSS-Auto 对 16 条"名称→文章链接"路线全景实测后排除并存档结论; 免费模型必须 `probe` 打点验证才入白名单; Fund-Fortune 数据源选型表逐候选 ✅/❌ (efinance "已吸收其端点后弃用——不符限速红线")。实测矩阵（√/×）是唯一可信的选型语言。

## 丙部 — 技术方案宪法 (Technical-Plan Articles)

### C5 — 当前条件下的最优解 · The optimal solution under actual constraints
Multiple technical routes will always look plausible. For **this** project's goal, under
**current** technical conditions and **this** environment, one of them is best — the plan
must be that one, and must record **why** (ADR: hard-to-reverse + surprising +
real-trade-off). "都能实现" is not a selection criterion; it is an abdication.

*V2 evidence*:
- 数据通道: **RSS > 平台 API** (零 key、零频控、零封号、自带全文 — ZBBrain-LIVE5 的供给选型); 微信侧则规避 API 扫描 (200013 频控/200003 封号)。
- 浏览器自动化: **Playwright 稳定底座 + Stagehand AI 理解** 混合互补 (全景比较 playwright/Stagehand/Dev Browser/agent-browser/browser-use 后的结论)。
- **能逆向破解成 API 就转 API** (更可靠); 同源异集群接口必须**语义验证**才升主通道 ("分红日复权增长率逐位一致" — Fund-Fortune)。

## 丁部 — 人机协作宪法 (Collaboration Articles) — V2 新增

### C6 — 指令只提需求与标准，不提过程 · Command the WHAT, not the HOW
"只提功能需求、成果标准、要达到的效果，不要提过程的要求" (PDF L7292)。用户拥有
WHAT 与验收标准；HOW 由 CC 在宪法与技能链内自主决定。一旦指挥过程，想象力与责任
同时转移给了不写代码的人。

### C7 — 十倍方案，批准才动工 · Ten× plan, approved before code
"揣摩我的真实意图，提出比我的初步想法好10倍的方案，方案经我同意后自主实施"
(PDF L5364)。Fund-Fortune 把它写成提案状态: **未批准不写一行业务代码**
(docs/planning/PROPOSAL.md)。批准前 CC 的全部产出是方案与问题清单，不是代码。
Idea Factory 的 **Proposal Approval Gate** 是本条的流程化实现。

### C8 — 批准后全自主：不跳步、不打扰 · After approval: full autonomy, no skipped steps
"不要跳过任何一个开发步骤" (PDF 中反复出现 ≥10 处)；"一次性完成所有迭代，中途无需
征询我任何意见，无需我执行任何操作" (L5112)。需要用户的人工事项（扫码、白名单、
凭据）在**预检阶段集中一次做完**（预检原则，与 weaipo-constitution「人工前置集中
一次」同源），之后零打扰。运行中遇错: 截图+查经验 → 自主分析 → 自主修复 → 接续
运行，不得请示。

### C9 — 完工交账：总结报告 + 成功经验固化复用 · Deliver the account, then harden the wins
"迭代完成后，梳理本项目开发全过程中我提出的所有要求、你的解决方案及实施结果，
形成完整的开发总结报告" (六步元链固定末步)。"**之前成功的方法怎么不用呢？一定不要
不停摸索**" (L1000) — 修复经验必须固化进生产代码与守卫测试（Fund-Fortune 把审查
修复写成 `test_review_fixes.py` 回归用例），不许只在会话里说说。

## 戊部 — 交付与验收宪法 (Delivery Articles) — V2 新增

### C10 — 生产级 > 无人值守；投产证据 > 文档完备 · Production-grade over unattended; run-ledger over documents
"生产级运行＞无人值守运行" (PDF L23)。而**文档齐 ≠ 产品活** — **ZBBrain 检验**:
ZBBrain-Write-Max 走完 14 阶段全文档 (CC-FPS 8.78/10) 却 `total_runs=0`；真正在产的
是 14,840 行单文件 Write-Pro (267 处小版本标记)。验收看**运行账**（state.json 的
runs、产物账、发布记录），不看文档厚度。工程文档完备而未投产，交付状态只能记
"已建成未投产"。

### C11 — 修复必须展示 before→after 实测数据 · Fixes ship with measured deltas
监控 0/75→75/75、章节提取 0→19 章 (WeArticleDS3 RALPH_LOOP_FINAL_REPORT) · 单篇流程
690.8s→150.9s = 4.6× (WeChat-AutoPub) · 全宇宙回测 17h→~2h (Fund-Fortune 8f7986e) ·
重复链浪费 17→1 (RSS-Auto)。没有 before→after 的"已修复"不算修复。

### C12 — 金标准验证，不许假完成 · Golden-standard verification, no fake completion
以**业务终态**为准，不以动作完成为准: 发表后 URL 跳转 `/post/list` 才算成功
(WeVideo-AutoPub) · 订阅以服务器回显记账 (RSS-Auto) · 剪贴板序列号必须变化才验收
(GetClipboardSequenceNumber) · 「草稿从草稿箱消失」才算发布 (WeChat-AutoPub)。
"发送成功 ≠ 生成回答" (PDF 反复出现的顽疾)。战报双计（触发≠发布）是违宪的计量。

### C13 — 容错优先，一次跑完 · Fault-tolerance first, run to completion
全文最高频的开发指令: "确保任何一个环节出现错误都能继续往下执行，即使前置任务
结果不完整也能继续" (PDF L8961+，出现 ≥5 处)。**核心路径单径无降级** (weaipo)；
**辅助功能降级不停播**: BGM 失败降无声、TTS 三层兜底 (edge-tts→pygame→SAPI)、
通知失败永不阻断主流程 (ZBBrain-LIVE5 / Fund-Fortune)。脚本交付标准 = "执行过程中
不会因问题终止，保证一次性完成"。

## 己部 — 数据与内容宪法 (Data & Content Articles) — V2 新增

### C14 — 禁止虚构，交叉验证 · No fabrication, cross-verify
"穷尽方法仍无法获取的数据即删除并调整结构，不得留空；杜绝任何虚构、待补充、
预计字数等字样" (L6208)；"搜集为空…尊重实际情况，如实输出" (L9143)。重要结论
**≥3 独立源、官方源 ≥70%、统计误差 ≤3%** (L6206)。公开数据源会**静默修订** →
双源交叉验证，差异入审计表告警 (Fund-Fortune nav_audit)；采集缺口**如实披露**
(常州站点级封禁，EngOpp-Mining)。

### C15 — 防未来函数，防数据毒化 · No look-ahead, no poisoned data
决策日 D 只用 ≤D−1 的净值，D 日净值成交，D+63 评估 (Fund-Fortune 回测三保险)；
份额折算 551%/355% 假跳变自动截断，"跨断点窗口宁可短不可假"；挂靠死基金
`last_date` 落后 30 自然日永不入排名。回测/统计里一个未来函数就能把整份结论变成
废纸 — 数据口径的可信度优先于一切指标。

### C16 — 内容保真与诚实汇报 · Content fidelity, honest reporting
AI 回答**原封不动入正文，只排版不删减不扩写**；课程库 Excel 原始信息只分类不改写
(L8897)。测试诚实: 158/158 通过但总覆盖率 14% 要**如实写明**并设目标 (AIResearch)；
诚实的权衡声明: "平均收益低于动量法——这是设计取舍…要弹性请右转动量策略，要活着
请留下" (Fund-Fortune)。同规则三基线对照（随机/动量/本算法）并公开最差单笔对比。

## 庚部 — 红线 (Red Lines — never cross)

| # | Red line | Enforcement |
|---|----------|-------------|
| **R1** | **代理用完即关** — push/代理使用后恢复直连，不留 TUN/DNS 残留；国内流量不走代理（LIVE5 `--no-proxy-server`，仅 edge-tts 走代理）；微信 API 绝不走代理 (`trust_env=False`) | `clash-proxy` `push` 默认收口；`stop()` API-direct-first |
| **R2** | **禁止静默失败** — no silent `except: pass`. We-AIPO 163 处、WenXian 19 处裸 except 全面清除；RSS-Auto "取链静默失败三处根除"。失败要计数、列名、告警 | review + `verification-gate`；Ralph Loop 逐轮清零 |
| **R3** | **根因先于修复** — name the exact root cause and rule out the wrong hypothesis before touching code | `systematic-debugging` red-first; Iceberg Rule |
| **R4** | **穷尽之前不许说"做不到"** — "I can't" without evidence of exhausted options (L1–L4 escalation) is refused | `high-agency` anti-rationalization table |
| **R5** | **验证者 > 生成者** — when output stalls, strengthen the verifier, not the generator | Phase 10 Ralph Loop; `upgrade_audit` pattern |
| **R6** | **安全检查先于 commit** — no hardcoded secrets; **推送 GitHub 前替换敏感信息且不影响本地运行**。反面教材: MD2N 曾把凭据写进配置，后以 commit 4de9443 补救 | standing security rules; secret scans |
| **R7** | **账号安全至上** — 封号红线: 拟人间隔**永不自动调整** (即使自复盘也不动)；单账号串行完成才切下一个；群发随机 5–10s、发文间隔 3–5min；直播每 1h ≥1 次真人动作、检测"无人直播"告警即中断 | 代码常量 + 护栏测试 (WeChat-AutoPub/RSS-Auto/ZBBrain-LIVE5) |
| **R8** | **只增不删，代码级硬化** — 永不实现 delete/remove 代码路径；危险端点黑名单 (`/del` `/pause` `/login/*`)；删除类按钮白名单断言 (`safety.assert_button_safe`)；真实环境（秘塔/大脑/视频号/微信/灵珠）零删除零改名；原始数据不可改只分类 | 代码审查清单 + 断言测试 (WeVideo/GCBrain/Metaso-Auto) |
| **R9** | **日预算硬顶，宁可拒启** — 预算配置写大直接拒绝启动；收费模型白名单闸门 "宁可启动失败不可误花钱"；免费模型 probe 实测才入白名单；多级降级链兜底 | 启动预检 (RSS-Auto/GCBrain/Fund-Fortune) |
| **R10** | **反爬主动限流** — 不等失败才停: 到 450 次调用**主动**暂停 20 分钟 (GCBrain 零失败零限流)；每搜索 2 页长暂停 60–120s；随机间隔；深夜错峰 | 限流器常量 + 主动暂停逻辑 |
| **R11** | **密钥外置** — 一切凭据进 config 模板 + 真实配置 gitignore + 环境变量；**提示词与文档永不出现明文密钥**。《总包大脑实战方案》全文散落十几枚真实密钥 (GLM/百度/MiniMax/企微/微信 AppSecret/QQ 授权码…) — 教材级的反面案例，材料因此永不入库 | `.gitignore` + R6 扫描; 本仓库 `.gitignore` 已封 `优化改进建议/*.pdf` |
| **R12** | **人工终审边界** — 结构安全/抗震设防类最终判定必须人工签字，AI 结论仅附件；敏感内容必须加人工审核层；置信度 <0.85 自动转人工复核（四灯分级: 红/橙/黄/绿，严重违规人工确认） | 四灯闸门 (HydDesign/PDF 四灯体系) |

## 辛部 — Enforcement map (article → phase gate)

| Article | Gate that enforces it |
|---------|----------------------|
| C1 hardest problem | Idea Factory `proposal-forge` **ten× delta index** — falsifiable 10× gate kills incremental ideas; scorecard verdict gate |
| C2 boldness | Phase 0 Visionary Elevation (anti-consensus design) + idea-intake must not pre-shrink |
| C3 world-best & landable | Phase 2 GitHub Discovery + research-orchestrator gap analysis before the Proposal Approval Gate |
| C4 giants' shoulders | Phase 2: score ≥80% → **clone and adapt** is the default; from-scratch requires a documented miss; 选型/逆向实测矩阵入 KNOWLEDGE_BASE |
| C5 optimal solution | Phase 5 architecture + ADR discipline (3-part test) + 语义验证记录 |
| C6 command WHAT | Idea intake & requirement docs: 需求+验收标准，不写过程指令 |
| C7 approved before code | **Proposal Approval Gate** (interaction point #3): 未批准不写一行业务代码 |
| C8 full autonomy | Phase 8 autonomous loop + **预检清单** (human steps batched once at preflight) |
| C9 deliver the account | Phase 12 post-run evolution + 开发总结报告 as a required deliverable |
| C10 run-ledger | Phase 10/11 acceptance reads state.json runs / 产物账, not document completeness |
| C11 before→after | Ralph Loop iteration reports; `verification-gate` three-state verdict |
| C12 golden standard | Phase 9 QA: 业务终态断言 (URL/回显/序列号/消失) replaces 动作完成断言 |
| C13 fault-tolerance | Phase 8 error-handling standard: 核心单径、辅助降级、一次跑完 |
| C14–C16 data integrity | Phase 9 QA + data validation gates; testing-automation honest-coverage reporting |
| R1–R6, R7–R12 | Phase 9/10 verification + hooks + the tooling listed in 庚部 |

## 壬部 — Evidence: the delivered portfolio (2025-12 → 2026-09)

| Project | Constitutional proof |
|---------|---------------------|
| We-AIPO (自媒永动机) | 290 commits · 126 modules · 218 tests · 78 deep optimizations · 11/11 unattended stages (C10, R2) |
| ResearchFactory-Eng | 233 commits · 762 unit tests · 17 采集渠道 · 引用审计 (C14) |
| EngOpp-Mining | 106 commits · 6 网×31 省=186 份省报 · 145.7× 吞吐 · 7 次外杀全自愈 (C13) |
| RSS-Auto | 105 commits · 303 tests · 693 订阅源 · LLM ¥0 · 同号重复链 17→1 · 16 路线实测排除 (C4, R9, R10) |
| Fund-Fortune | 33 commits · 83/83 tests · 27,563 基金全量回补含清盘 · 进化红线闸双向锁死 · nav_audit 双源对账 (C1, C7, C15, R7-类红线闸) |
| ZBBrain-LIVE5 | 37 commits · 113 tests · 48 篇/24h · experiments.tsv 11 轮全 keep · 合规话术审查 (C13, R7) |
| WeChat-AutoPub | 33 commits · 73 tests · 单篇 690.8s→150.9s (4.6×) · 全天 42 篇零失败 · 定时四层冗余 (C11, C12, R7) |
| WeArticleDS3 / AIResearch root | 158/158 tests · Ralph 20 轮 · ~4220 行 · 覆盖率 14% 如实披露 (C9, C16) |
| KnowFactory-PRO20 | 83 commits · 191 视频 · 标题 179× 效应固化为公式螺旋 (经验固化) |
| WeVideo-AutoPub | 29+ 已发布 · 封面/发表成功率 100% · 重复 0 · 代码层零 delete (C12, R8) |
| ZBBrain-Write-Pro | **14,840 行单文件在产** · 267 处小版本标记 — ZBBrain 检验的活证据 (C10) |
| GCBrain-AutoRefresh | 759 号扫描 30–50 min 零失败零限流 (R10 主动限流) · 秘塔端点逆向 + SQLite 指纹去重 (C4) |
| MD2Nwechat | 37 commits · v1.10.0 · GitHub Releases · 文档-代码一致性 grep 校验 4 处 (C9) |
| **反面证据（同样入宪）** | ZBBrain-Write-Max: 全套 14 阶段文档但 `total_runs=0` (C10) · MG-yt-dlp 覆盖率 45.88% 后搁置 · Doc2Video tests/ 空目录 (R2 风险) · 5 个 `nul` 占位空壳目录 — "先提案后动工" 正确，但动工后必须跑起来 |

## Review

The constitution is re-examined whenever a delivered project completes (Phase 12
post-run evolution): new red lines earned the hard way get proposed as amendments with
evidence, then versioned here. **V2 (2026-09-08)** added 丁/戊/己部 (C6–C16) and
R7–R12 from the full-portfolio mining; V1 articles C1–C5/R1–R6 unchanged in substance,
enriched in evidence.
