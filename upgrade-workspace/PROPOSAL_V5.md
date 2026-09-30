# Super-Skill V5.0 提案：从「说明书」到「发动机」

> 日期：2026-09-30 · 调研规模：**204 个去重 GitHub 仓库**（5 组并行调研，逐个用 `gh api` 核验星数、许可证、最近推送），证据见 [research/](research/)
> 状态：**待审批**。批准前不改动任何现有代码。

---

## 一、诊断：V4.1.16 的真实能力底座

Super-Skill 的**方法论厚度**在同类项目里是第一梯队：14 阶段、开发宪法 C0–C16、缝合怪三律、任鑫选品、判断层等，合计约 18.5k 行。
但把它放进 Claude Code 实际运行时，**能被机器强制执行的部分接近于零**：

| 维度 | 现状（实测） | 后果 |
|---|---|---|
| Hooks | `.claude/settings.json` 使用了不存在的结构（`handler` 字段、对象形式的 matcher、`Notification` 当作会话启动事件、`$CLAUDE_TOOL_INPUT_FILE_PATH` 这个变量不存在） | **6 个生命周期 hook 实际上 0 个会生效**；"会话启动升级"和"会话结束进化"从未真正执行过 |
| 阶段闸门 | 14 个阶段的 Gate 全部写在文字里 | 模型可以跳阶段、谎报完成，没有任何机制拦截 |
| 状态 / 续跑 | 没有机读状态文件 | 上下文压缩或会话中断后，无法从正确的阶段接着跑 |
| 追溯 | 需求、任务、测试之间没有 ID 关联 | 验收全凭"感觉覆盖了" |
| 多智能体 | Planner-Worker-Judge 只是一段描述，没有 agent 定义，也没有 worktree 脚本 | 实际还是单线程 |
| 实验循环 | "NEVER STOP" 停在文字层面，没有熔断，也没有卡死检测 | 无人值守时可能空转、烧钱，或陷入重复修错 |
| 评测 | 没有基准，没有"装与不装"的对照 | **无法证明 Super-Skill 让结果变好**，自进化也没有适应度函数 |
| 自进化 | `evolver/` 是空目录；GEP 基因只是 JSON 描述 | "进化"无法度量，也无法回滚 |
| 记忆 | cerebrum / buglog 是纯 markdown，没有检索 | 记忆越积越多、越积越噪 |
| 预算 / 可观测 | 没有 | 看不到哪个阶段花了多少 token 和钱 |
| 工程卫生 | `__pycache__/*.pyc` 共 31 个被提交进仓库；1 个测试在 Windows 中文路径下失败；SKILL.md 已到 500 行上限 | — |

**结论**：短板不在"知道什么"，而在"**能强制做到什么、能证明做到什么**"。V5.0 的主线是把文字规则变成**可执行、可验证、可进化**的机制。

---

## 二、"100 倍"如何定义（可证伪）

"能力提升 100 倍"没有办法事先精确测量，因此本提案用 **5 个可计数指标**来定义，每项都给出 V4 基线和 V5 目标，交付时逐项实测：

| # | 指标 | V4 基线 | V5 目标 | 倍数 |
|---|---|---|---|---|
| K1 | **真正会触发的强制机制数**（hook 守卫、阶段闸门、熔断、预算阈值等） | 0 | ≥ 25 | 0 → 25（从无到有） |
| K2 | **有机器校验的阶段闸门** | 0 / 14 | 14 / 14 | ∞ |
| K3 | **可自动执行的端到端检查项**（单元测试 + 闸门检查 + 评测用例） | 131 个单测，不覆盖流程 | ≥ 400，并覆盖全流程 | 3×，且覆盖面从脚本扩展到流程 |
| K4 | **评测证据**：装与不装 Super-Skill 的对照差值（Δ 通过率 / Δ 成本） | 无法测量 | 有基准、可复跑、进 CI | 从不可测到可测 |
| K5 | **自进化闭环**：变体 → 评测打分 → 保留或回滚，全部自动 | 0 个环节可执行 | 4/4 环节可执行 | ∞ |

"100 倍"的实质是：从 **"0 个可强制机制"** 到 **"一整套会自己守门、自己证明、自己进化的机制"**。
任何声称"变好"的改动，今后都必须由 K4 的评测给出数字，这本身就是宪法 C12（金标准验证）和 C14（不造数据）的机械化。

---

## 三、方案总览：10 个工作流（W1–W10）

每项都标注了**来源项目**和**采用方式**："直接复用"= 许可证允许，复制并保留署名；"借鉴模式"= 只参考设计、自己重写，不复制代码。

### 🔴 P0：地基（先做，其余都依赖它）

#### W1 Hooks 重建：从"0 个生效"到"全部可测试"
- 按官方 schema 重写 `settings.json`：`SessionStart` / `UserPromptSubmit` / `PreToolUse` / `PostToolUse` / `PreCompact` / `Stop` / `SubagentStop` / `SessionEnd`
- 新增 `hooks/*.py`，每个事件一个纯标准库 Python 脚本，从 stdin 读 JSON，Windows 可用：
  - `session_start.py`：注入当前阶段、下一步动作和交接信息（通过 `additionalContext`）
  - `guard_bash.py`：拦截 `rm -rf`、强推、推送到 main、读 `.env` 或 `~/.ssh`（通过 `permissionDecision: deny`）
  - `phase_gate.py`（Stop）：阶段未完成时阻止模型提前结束。它检查 `stop_hook_active`，设有 20 次上限，并且只在进度账本推进过时才阻止，避免死循环
  - `log_event.py`：所有事件写入 `.super-skill/events.jsonl`
  - `write_handoff.py`（PreCompact）：压缩前写 `handoff.yaml`
- **只在 Super-Skill 项目内生效**：没有 `.super-skill/state.json` 的项目，所有 hook 立即放行，不影响你的其他项目
- 新增 `validate_hooks.py`（schema 静态校验）和 `test_hooks.py`（喂入样例载荷，断言退出码和 JSON 输出）
- 来源：obra/superpowers（MIT，含 Windows 的 `run-hook.cmd`）、planning-with-files（MIT，Stop 闸门）、Continuous-Claude（MIT，交接）、cchooks（MIT）；disler/hooks-mastery 与 trailofbits 只借鉴模式（无许可证）

#### W2 阶段状态机与阶段契约
- `.super-skill/state.json`：记录当前阶段、下一步动作、各阶段状态和审批、产物清单、`state_head` 提交 SHA、中断位置
- `phases.yaml`：14+ 个阶段各自的 **inputs / outputs / gate（可执行检查）/ approval（人工或自动）**，把现有"阶段转换表 + 缝合契约"写成数据
- `ss.py` CLI：`status` · `next` · `gate <phase>` · `advance` · `goto <phase>`（下游阶段标记为 stale）· `resume` · `approve <gate>`
- 阶段边界打 git tag（`ss/P6-done`），支持"回退到某个阶段"
- 来源：GSD Core `STATE.md`（MIT）、cc-sdd `spec.json`（MIT）、spec-kit Constitution Gate（MIT）、LangGraph checkpoint（借鉴）、goose recipes（借鉴）

#### W5 循环引擎安全化：autonomous-loop 与 Ralph Loop 落成脚本
- `loop_guard.py` 熔断器：CLOSED / HALF_OPEN / OPEN 三态。连续 3 轮无进展、5 次同一错误、或 2 次权限拒绝时跳闸，冷却 30 分钟
- **卡死检测**：扫描最近 20 个事件，识别 4 种模式：重复同一动作和结果、重复同一错误、自言自语、来回摇摆
- **双条件退出**：全部任务完成 **并且** 显式给出 `EXIT_SIGNAL: true`，防止谎报完成
- **压力升级梯**：第 2 次失败强制换一条根本不同的路线，L3 强制走 7 点诊断清单（沿用现有 high-agency / PUA 方法论）
- `ralph.py`：每一轮用全新上下文 → 只做 1 个任务 → 跑该任务的 verify 命令 → 通过才提交 → 追加到 `progress.txt`；`experiments.tsv` 记录保留、丢弃或崩溃
- 来源：frankbria/ralph-claude-code（MIT）、snarktank/ralph（MIT）、OpenHands 卡死检测（MIT）、mini-swe-agent（MIT）

#### W6 评测基准：让"变好"有数字
- `evals/`：采用 Claude Code 官方 `claude plugin eval` 格式。每个用例在装和不装 Super-Skill 两种条件下各跑 3 次，报告 Δ 通过率和 Δ 成本，`--threshold` 可接入 CI
- `evals/cases/`：首批 12 个用例，覆盖 5 类：触发、Idea Factory 产物、阶段闸门、守卫拦截、端到端小产品
- `evals/grading/`：确定性评分器，包括文件存在、章节齐全、测试通过、没有残留 `[NEEDS CLARIFICATION]`
- 不依赖模型的**离线评测**（`bench_offline.py`）：对 fixture 项目跑全部闸门和追溯检查，秒级完成，每次提交都跑
- 来源：Claude Code `plugin eval`（官方）、anthropics/skills `skill-creator` 评测栈（Apache-2.0）、Harbor / Terminal-Bench 任务格式（Apache-2.0）、SWE-bench 的 FAIL_TO_PASS 思想（MIT）

#### W10 瘦身、打包与工程卫生
- **SKILL.md 改为路由器**，控制在 ≤ 300 行：只保留阶段 → 子技能路由表、闸门协议和命令速查；原有长段落**原文迁入** `references/`，一个字都不删，遵守宪法"只增不删"红线
- 新增 `.claude-plugin/plugin.json` 和 `marketplace.json`，支持 `/plugin install`
- `validate_skills.py`：按 agentskills 规范校验每个子技能（name 格式、description 长度、body < 500 行）；有 `scripts/` 的子技能必须带测试（K-Dense 规则）
- `.github/workflows/ci.yml`：跑单测、hook 校验、技能校验和离线评测
- 移除已提交的 `__pycache__`，修复 Windows 中文路径测试，新增 `NOTICE.md`（第三方许可证署名）
- 来源：agentskills spec / skills-ref（Apache-2.0）、K-Dense CI（MIT）、gstack 模板（MIT）

### 🟠 P1：放大（多智能体与可追溯）

#### W3 需求可追溯与任务依赖图
- 需求用 **EARS 句式**，带稳定编号 `REQ-001`、`REQ-001.AC1`；任务用 `covers:` 标注覆盖哪条需求，测试名里带 ID
- `trace_matrix.py`：生成 REQ → 任务 → 测试 → 状态的追溯矩阵；必需需求覆盖率低于 100% 或存在孤儿任务时，QA 闸门直接失败
- `taskgraph.py`：支持 `ready` / `next` / `claim`（原子认领）/ `done` / `waves`（拓扑排序出可并行的波次）/ `validate`（检测循环依赖、缺失覆盖）/ `complexity`（1–10 分，超过 5 分建议拆分）
- 前端澄清升级：最多 5 个问题，按"影响 × 不确定性"排序，答案回写到需求文档（spec-kit clarify 模式）
- 来源：spec-kit（MIT）、cc-sdd EARS 模板（MIT）、beads ready 队列（MIT）、Task Master 复杂度分析（Commons Clause 许可，**只借鉴模式**）

#### W4 真正的多智能体：Planner-Worker-Judge 落地
- `.claude/agents/`：
  - `ss-planner.md`：只读，产出任务图
  - `ss-worker.md`：`isolation: worktree`，每个 worker 独立 worktree，Claude Code 原生强制隔离
  - `ss-judge.md`：只读工具，按规范符合度 + 代码质量两轴评审，给出 keep / discard 结论
  - `ss-researcher.md`（便宜模型）、`ss-spec-reviewer.md`
- 执行协议：阶段 8 按 `taskgraph waves` 的结果，每个任务派一个新的 worker → spec-review → code-review；高风险任务可用 **best-of-N**（2–3 个 worker 各走一种策略，由 Judge 挑出测试通过的那个）
- `fanout.py`（可选，无头模式）：`claude -p --max-budget-usd --max-turns` 批量在多个 worktree 里跑，记录 base commit，结束后 `worktree remove` + `prune`
- 来源：superpowers subagent-driven-development（MIT）、Claude Code subagent 的 `isolation: worktree`（官方）、claude-squad worktree 生命周期（AGPL，**只借鉴模式**）、Crystal best-of-N（MIT）

#### W9 预算与可观测
- `cost_meter.py`：解析 `transcript_path` 的 JSONL，按 (message.id, requestId) 去重（ccusage 规则）来累计 token 和成本
- 预算三层：硬顶用 `--max-budget-usd` / `maxTurns`；软阈值由 hook 在 70% 时警告、100% 时阻止；按消耗速率预测何时触顶
- `ss.py report`：按阶段汇总时长、token、成本、闸门失败次数和熔断次数；复盘改用这些数据，不再靠文字
- 可选配置：原生 OpenTelemetry 环境变量模板
- 来源：ccusage（MIT）、Claude-Code-Usage-Monitor（MIT）、disler observability 事件结构（**只借鉴模式**）

### 🟡 P2：复利（自进化与记忆）

#### W7 进化引擎落地：填上空的 `evolver/`（clean-room 自研）
- **适应度函数** = W6 评测通过率 − λ·token 成本 − μ·新增行数（行数项就是 autoresearch 的"简洁性准则"）
- `evolver/archive.jsonl`：保存**所有**变体，不只保存最优的那个。选父代的权重为 `sigmoid(10·(score−0.5)) / (1+children)`，偏向"好但还没被充分探索"的变体（DGM）
- **反思式变异**：读取父代失败用例的日志，一次只改一个 SKILL.md 段落（GEPA 做法）；保留在任一用例上最优的变体（Pareto 前沿）
- **分级评测**：先跑 3 个用例做冒烟，分数达到第二名水平才跑全量（DGM 做法）
- **停滞检测**：同一信号或基因 N 次都没提分就标记停滞，强制换基因（evolver GEP 做法）
- 只有评测胜出才固化（git commit + event），否则 `git reset`
- 来源：DGM（Apache-2.0，选择算法可直接移植）、GEPA（MIT）、autoresearch（无许可证，只借鉴）；**evolver 已改为 GPL-3.0，只做 clean-room 重写，绝不复制其代码**

#### W8 记忆升级：ACE 手册 + 检索
- cerebrum 升级为 `playbook.jsonl`：每条规则带 helpful / harmful 计数；只允许增量操作（ADD / UPDATE / +helpful / +harmful），**从不整体重写**；harmful 比 helpful 多 2 以上时自动淘汰；过时条目标记 `superseded_by` 而不是删除（Graphiti 做法）
- `memindex.py`：基于 SQLite FTS5 的纯标准库索引，覆盖 cerebrum、buglog、KNOWLEDGE_BASE、handoff。检索分三层：`search` 返回 ID 和一行摘要 → `timeline` 返回前后邻居 → `get` 返回全文。排序用 BM25 叠加时间衰减
- 子技能按需检索：每个阶段只加载最相关的 top-5 子技能（Voyager 技能库做法，节省 token）
- 来源：ACE（Apache-2.0）、claude-mem 三层检索（借鉴）、mem0（Apache-2.0）、Voyager（MIT）

---

## 四、交付物清单（新增为主，不删除现有内容）

```
.claude/
├── settings.json                 # 重写：合法的 hooks schema
├── agents/                       # 新增：5 个 subagent 定义（W4）
└── skills/super-skill/
    ├── SKILL.md                  # 瘦身为 ≤300 行路由器，原文迁入 references/（W10）
    ├── phases.yaml               # 新增：阶段契约（W2）
    ├── hooks/                    # 新增：8 个 hook 脚本 + 测试（W1）
    ├── engine/                   # 新增：ss.py 状态机 · taskgraph · trace_matrix · loop_guard · ralph · cost_meter · memindex · gate_check（W2/3/5/8/9）
    ├── evolver/                  # 新增：archive · selector · mutate · fitness（W7）
    ├── evals/                    # 新增：plugin-eval 用例 + 离线 bench（W6）
    ├── templates/                # 新增：EARS 需求 / 任务 / 交接模板（W3）
    └── references/               # 保留全部原文件 + 新增 v5-engine.md 等
.claude-plugin/plugin.json · marketplace.json      # 新增（W10）
.github/workflows/ci.yml                            # 新增（W10）
NOTICE.md · CHANGELOG（V5.0.0）· README（中英）     # 更新
install.py                                         # 新增：跨平台安装器（全局或项目级，可选注册 hooks）
```

## 五、实施顺序与验收

| 批次 | 内容 | 验收标准（全部为机器可验证） |
|---|---|---|
| 1 | W10 卫生 + W1 Hooks + W2 状态机 | `test_hooks.py` 全绿；`validate_hooks.py` 通过；用真实 Claude Code 会话实测 SessionStart 注入生效、守卫拦截生效 |
| 2 | W5 循环引擎 + W6 评测 | 熔断、卡死检测、双条件退出各自有单测；离线 bench 可以复跑；至少 1 个 plugin-eval 用例实跑出 WITH / W/OUT 对照 |
| 3 | W3 追溯 + W4 多智能体 + W9 预算 | fixture 项目上追溯矩阵正确判定覆盖和孤儿任务；worker agent 在 worktree 中完成一个任务的演示 |
| 4 | W7 进化 + W8 记忆 | 在离线 bench 上跑一轮完整进化，产生 keep 和 discard 记录；memindex 检索的单测 |
| 5 | SKILL.md 瘦身、README、CHANGELOG、全局安装、推送 | 原有 131 个单测 + 新增测试全绿；K1–K5 实测表写进 CHANGELOG |

**原则**：每批完成后先跑全量测试，再进入下一批；遇到结果与预期不符时，如实写进报告（宪法 C14）。

## 六、风险与边界

1. **许可证**：以下项目只借鉴模式、不复制代码——evolver（GPL-3.0）、openwolf（AGPL）、claude-squad（AGPL）、Task Master（Commons Clause）、pua / autoresearch / hooks-mastery / trailofbits（无许可证）、awesome-claude-code（CC BY-NC-ND）。所有直接复用的内容都在 `NOTICE.md` 里署名。
2. **全局 hooks 的影响面**：hooks 默认只注册在项目级 `.claude/settings.json`。如果注册到全局，脚本内置"非 Super-Skill 项目直接放行"的保护，但仍然会在每个会话里多执行一次毫秒级的 Python 调用。**需要你决定**。
3. **评测成本**：`claude plugin eval` 每个用例要跑 6 次（装与不装各 3 次），会消耗真实额度。我先实跑 1–2 个用例验证链路，全量评测留给你按需触发。
4. **推送权限**：当前 gh 登录的账号 `martinleo761010` 对 `huangxiding-creator/Super-Skill` 的权限是 push = false，**推送前需要你解决**（见审批问题）。
5. **周度自动化兼容**：`automation/` 的 S3 硬门会检查"SKILL.md < 500 行 + 版本脚注"，瘦身后的 SKILL.md 满足这一条；S4 用 robocopy 镜像安装的路径保持不变。
