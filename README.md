<div align="center">

# Super-Skill

**AI-Native Autonomous Development Orchestrator for Claude Code | AI 原生自主开发编排器**

[![Version](https://img.shields.io/badge/version-5.0.0-blue.svg?style=for-the-badge)](.claude/skills/super-skill/CHANGELOG.md)
[![CI](https://img.shields.io/github/actions/workflow/status/huangxiding-creator/Super-Skill/ci.yml?style=for-the-badge&label=ci)](https://github.com/huangxiding-creator/Super-Skill/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-orange.svg?style=for-the-badge)](https://docs.claude.com/en/docs/claude-code)

[English](#overview) · [中文](#概述) · [Changelog](.claude/skills/super-skill/CHANGELOG.md) · [Engine reference](.claude/skills/super-skill/references/v5-engine.md) · [NOTICE](NOTICE.md)

*Raw idea → research → 10× proposal → your approval → 17 machine-checked phases → shipped product.*

*一个想法 → 调研 → 10 倍提案 → 你批准 → 17 个机器校验的阶段 → 交付产品。*

</div>

---

## Overview

Super-Skill is a Claude Code skill (and plugin) that runs software development as a gated,
auditable pipeline. **V5 turns its methodology into an executable engine**: rules that must hold
are enforced by code — phase contracts, a state machine, hooks and a circuit-breaker loop —
instead of prose the model is trusted to remember.

| Without Super-Skill | With Super-Skill V5 |
|---|---|
| "Done" is whatever the model claims | A phase is done only when `ss advance` passes its gate (files, EARS requirements, traceability, tests) |
| The agent stops halfway or asks needless questions | A Stop hook keeps autonomous phases running until the gate passes — with stall detection and a nudge cap |
| Destructive commands and secrets depend on luck | A PreToolUse guard denies `rm -rf ~`, force-push, `.env`/SSH-key reads and state tampering; approvals always ask you |
| Context lost on compaction | Hand-off written before compaction, re-injected on resume |
| Loops burn money on the same error | Circuit breaker + stuck detector + pressure ladder; budgets warn at 70 % and stop at 100 % |
| No way to know whether the skill helps | Offline benchmark (13 scenarios) + `claude plugin eval` with/without-skill ablation |

## Install

Requires **Python ≥ 3.9** (stdlib only) and Claude Code. Works on Windows, macOS and Linux.

```bash
git clone https://github.com/huangxiding-creator/Super-Skill.git
cd Super-Skill
python install.py --global --hooks     # copy skill + subagents, register hooks, run doctor
```

The installer writes hook commands using *this* machine's Python, merges them into
`~/.claude/settings.json` (existing settings are preserved and backed up) and finishes with a
doctor run. Hooks are no-ops outside Super-Skill projects.

Other routes:

```bash
# plugin (hooks via ${CLAUDE_PLUGIN_ROOT}) — inside Claude Code:
/plugin marketplace add huangxiding-creator/Super-Skill
/plugin install super-skill@super-skill

# skills CLI, then register hooks
npx skills add https://github.com/huangxiding-creator/Super-Skill --global --yes
python ~/.claude/skills/super-skill/install.py --hooks

python install.py --doctor             # verify on any machine
python install.py --uninstall-hooks    # remove only Super-Skill hooks
```

Use one hook route per machine (installer **or** plugin).

## Use

Describe what you want in Claude Code — *"I have an idea for …"* or *"build me …"*. The skill
initialises a run and drives it:

```text
ss init --project todo --from IF1      # raw idea (or --from P0 / P4)
ss next                                # what to do now
ss gate                                # which checks fail and why
ss advance                             # passes the gate → next phase
ss approve proposal                    # YOU confirm (the guard always asks)
ss task add "persist todos" --covers REQ-001.AC1 --verify "pytest -q"
ss ralph --max-iterations 30           # unattended one-task-per-iteration loop
ss cost report                         # per-phase time, failures, cost estimate
```

`ss` = `python <skill>/engine/ss.py`; the session brief prints the exact command for your machine.

## Architecture

```
            ┌──────────── hooks (fail-open, project-scoped) ────────────┐
SessionStart│ brief + hand-off   PreToolUse│ guard   PostToolUse│ log, stuck, budget │
PreCompact  │ hand-off           Stop      │ phase gate (anti-loop)                  │
            └────────────────────────────────────────────────────────────┘
                                   │
 IF1 Intake → IF2 Research → IF3 Proposal ✋ → P0 Vision → P1 Feasibility → P2 Discovery → P2b Skills
 → P3 Knowledge → P4 Requirements ✋ → P5 Architecture → P6 Task graph → P7 Init → P8 Build
 (ss-planner → ss-worker×N in worktrees → ss-judge) → P9 QA → P10 Ralph → P11 Deploy → P12 Evolve
                                   │
  phases.json contracts · state.json · ledger · tasks.json · trace matrix · loop guard · playbook
  · FTS5 memory · cost meter · evolver (DGM/GEPA, clean-room) · offline bench · plugin evals
```

✋ = the only two approvals you give. Everything else is autonomous and gated.

## Proof

- `python .claude/skills/super-skill/scripts/run_all_tests.py` — engine, hooks, installer
  (including a fresh-machine install simulation), evolver, all sub-skill tests, the offline
  benchmark and structural validation. CI runs it on ubuntu (py3.9, 3.12), macOS and Windows.
- `python .claude/skills/super-skill/evals/bench_offline.py --pretty` — 13 deterministic scenarios.
- `claude plugin eval . --runs 1` — model evals with and without the skill ([evals/](evals/)).

## Project structure

```
.claude/skills/super-skill/
  SKILL.md            router (≤300 lines)        phases.json   phase contracts
  engine/             ss.py + state machine, gates, task graph, trace, loop guard, ralph,
                      cost meter, playbook, memory index, skill router (+ tests)
  hooks/              8 hook scripts + hooks.json (plugin)
  agents/             ss-planner · ss-worker · ss-judge · ss-researcher · ss-spec-reviewer
  evolver/            benchmark-driven self-evolution      evals/  offline bench
  skills/             48 sub-skills                         references/  doctrine + engine docs
  install.py          portable installer + doctor
.claude-plugin/       plugin.json + marketplace.json
evals/                claude plugin eval cases
upgrade-workspace/    V5 proposal + 204-repo research dossier
automation/           weekly self-upgrade pipeline (maintainer machine)
```

## Standing on giants' shoulders

V5 was designed from a survey of **204 open-source projects** (skill ecosystems, autonomous coding
agents, spec-driven workflows, self-evolving agents & memory, orchestration/hooks/evals) — see
[upgrade-workspace/research](upgrade-workspace/research/) and [NOTICE.md](NOTICE.md). Key
influences: spec-kit, cc-sdd, beads, ralph (snarktank, frankbria), OpenHands, mini-swe-agent,
superpowers, planning-with-files, Continuous-Claude, ccusage, ACE, DGM, GEPA, Voyager,
karpathy/autoresearch, mattpocock/skills, Boris Cherny's AI-mastery talk.

## Contributing & licence

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Run `scripts/run_all_tests.py` before
opening one. MIT licence.

---

## 概述

Super-Skill 是一个 Claude Code 技能（也是插件），把软件开发变成**有闸门、可审计**的流水线。
**V5 把方法论变成了可执行的引擎**：必须遵守的规则由代码强制执行——阶段契约、状态机、hooks、熔断循环——而不是寄希望于模型记住文字。

| 没有 Super-Skill | 使用 Super-Skill V5 |
|---|---|
| "完成"全凭模型自述 | 只有 `ss advance` 通过闸门（文件、EARS 需求、追溯矩阵、测试）才算完成 |
| 做到一半停下或无谓提问 | Stop hook 让自主阶段持续推进直到闸门通过，带停滞检测与次数上限 |
| 危险命令和密钥全靠运气 | PreToolUse 守卫拦截 `rm -rf ~`、强推、读 `.env`/SSH 密钥、篡改状态；审批一律交给你确认 |
| 上下文压缩后失忆 | 压缩前写交接文档，恢复时自动注入 |
| 同一个错误循环烧钱 | 熔断器 + 卡死检测 + 压力升级梯；预算 70% 预警、100% 停止 |
| 不知道技能到底有没有用 | 离线基准（13 场景）+ `claude plugin eval` 装/不装对照评测 |

### 安装

需要 **Python ≥ 3.9**（仅标准库）和 Claude Code，支持 Windows / macOS / Linux：

```bash
git clone https://github.com/huangxiding-creator/Super-Skill.git
cd Super-Skill
python install.py --global --hooks     # 复制技能与子智能体、注册 hooks、自动体检
```

安装器用**本机**的 Python 生成 hook 命令，合并写入 `~/.claude/settings.json`（保留并备份原有设置），最后运行体检。在非 Super-Skill 项目里 hooks 不做任何事。
也可以用插件方式（`/plugin marketplace add huangxiding-creator/Super-Skill` → `/plugin install super-skill@super-skill`）或 `npx skills add` 后运行 `install.py --hooks`。任何电脑上都可用 `python install.py --doctor` 自检。

### 使用

在 Claude Code 里直接说"我有个想法……"或"帮我做一个……"。技能会 `ss init` 启动一次运行，然后按 17 个阶段推进；你只需要在**提案审批（IF3）**和**需求审批（P4）**两处确认。常用命令见上方 *Use* 一节。

### 证明它有效

- `python .claude/skills/super-skill/scripts/run_all_tests.py` —— 引擎、hooks、安装器（含"全新电脑"安装模拟）、进化器、全部子技能测试、离线基准、结构校验；CI 在 ubuntu / macOS / Windows 上运行。
- `python .claude/skills/super-skill/evals/bench_offline.py --pretty` —— 13 个确定性场景。
- `claude plugin eval . --runs 1` —— 装/不装技能的模型对照评测。

### 站在巨人肩膀上

V5 基于对 **204 个开源项目**的调研设计（技能生态、自主编码智能体、规范驱动开发、自进化与记忆、编排/hooks/评测），详见 [upgrade-workspace/research](upgrade-workspace/research/) 与 [NOTICE.md](NOTICE.md)。全部 V4 方法论（开发宪法 V2.1、缝合怪、任鑫方法论、混沌武器库、协调层、调研方法论、训虾派、判断层）完整保留在 `references/`。

### 许可证

[MIT](LICENSE) —— 个人与商业用途免费。
