<div align="center">

# Super-Skill

**AI-Native Autonomous Development Orchestrator | AI原生自主开发编排器**

[![Version](https://img.shields.io/badge/version-3.17-blue.svg?style=for-the-badge)](https://github.com/huangxiding-creator/Super-Skill)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-33+-purple.svg?style=for-the-badge)](.claude/skills/super-skill/skills/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-orange.svg?style=for-the-badge)](https://docs.anthropic.com/claude-code)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)

[English](#overview) · [中文](#概述) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [License](LICENSE) · [Issues](https://github.com/huangxiding-creator/Super-Skill/issues)

*One command to orchestrate 14 phases of autonomous software development, powered by self-evolving AI agents.*

*一条命令编排14个阶段的自主软件开发，由自进化AI智能体驱动。*

</div>

---

## Overview

Super-Skill is a **production-grade Claude Code skill** that transforms how AI builds software. Instead of ad-hoc prompting, it provides a structured 14-phase workflow with built-in self-evolution, autonomous experiment loops, and 33+ integrated specialized skills.

**Key innovation**: Applies [karpathy/autoresearch](https://github.com/karpathy/autoresearch)'s experiment loop pattern to software development — automatically run experiments, keep improvements, discard regressions, and never stop until you say so.

### Why Super-Skill?

| Before Super-Skill | After Super-Skill |
|-------------------|-------------------|
| Manual prompting for each step | 14-phase autonomous workflow |
| No quality enforcement | Built-in QA, security scans, coverage checks |
| Context lost between sessions | GEP self-evolution captures learnings |
| Single-agent development | Hierarchical Planner-Worker-Judge orchestration |
| Human must supervise | 24-hour unattended autonomous operation |

### Features

- **14-Phase Autonomous Workflow** — Vision → Feasibility → Discovery → Development → QA → Deploy → Evolve
- **Autonomous Experiment Loop** — Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) (58K+ stars)
- **GEP Self-Evolution** — Darwin Gödel Machine pattern for continuous improvement
- **33+ Integrated Skills** — Testing, security, API design, databases, monitoring, and more
- **Hooks-Based Auto-Execution** — Pre-run upgrade + Post-run evolution via Claude Code hooks
- **Hierarchical Orchestration** — Planner-Worker-Judge pattern for multi-agent coordination
- **Context Engineering** — JIT context loading, progressive disclosure, compaction survival
- **3 Interaction Points** — User only involved at: input, requirements approval, plan approval

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     NOTIFICATION HOOK (Session Start)            │
│                     Pre-Run Upgrade: Version → Upgrade → Sync    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 0: Vision ─────────────────────────────────────┐         │
│  Phase 1: Feasibility ────────────────────────────────┤         │
│  Phase 2: GitHub Discovery ───────────────────────────┤         │
│  Phase 2b: Skills Discovery ──────────────────────────┤         │
│  Phase 3: Knowledge Base ─────────────────────────────┤ 14      │
│  Phase 4: Requirements ──── (User Approval Gate) ─────┤ Phases  │
│  Phase 5: Architecture & Design ──────────────────────┤         │
│  Phase 6: WBS (Work Breakdown) ───────────────────────┤         │
│  Phase 7: Project Init ───────────────────────────────┤         │
│  Phase 8: Autonomous Dev ── (Experiment Loop) ────────┤         │
│  Phase 9: QA ─────────────────────────────────────────┤         │
│  Phase 10: Ralph Loop (10x Optimize) ─────────────────┤         │
│  Phase 11: Deploy ────────────────────────────────────┤         │
│  Phase 12: Evolution ─────────────────────────────────┘         │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                     STOP HOOK (Session End)                      │
│                     Post-Run Evolution: Retrospective → Improve  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Demo

> **Demo GIF coming soon!** Record your Super-Skill session and submit it via a PR.
>
> **演示GIF即将推出！** 录制你的 Super-Skill 会话并通过PR提交。

---

## Demo

> *Demo GIF coming soon — showing Super-Skill building a full-stack app in one command*

---

## Quick Start

### Install

```bash
# Clone the repository
git clone https://github.com/huangxiding-creator/Super-Skill.git
cd Super-Skill

# Install globally (requires Claude Code)
npx skills add .claude/skills/super-skill --global --yes
```

### Use

Just describe what you want to build in Claude Code:

```
> Build me a task management app with real-time collaboration
```

Super-Skill automatically triggers and orchestrates all 14 phases.

### One-Line Install

```bash
npx skills add https://github.com/huangxiding-creator/Super-Skill --global --yes
```

---

## 33+ Integrated Skills

| Category | Skills |
|----------|--------|
| **Core** | `autonomous-loop`, `pre-run-upgrade`, `post-run-evolution`, `darwin-evolution`, `high-agency`, `cognitive-modes` |
| **Development** | `api-patterns`, `data-patterns`, `state-management`, `real-time-websockets`, `code-transformation` |
| **Quality** | `testing-automation`, `security-scanning`, `accessibility-a11y`, `systematic-debugging` |
| **Infrastructure** | `cicd-automation`, `auto-git-create`, `monitoring-observability`, `mcp-integration` |
| **Optimization** | `performance-optimization`, `error-recovery`, `context-management`, `prompt-engineering` |
| **Discovery** | `github-discovery`, `find-skills`, `get-api-docs`, `brainstorming`, `continuous-learning-v2` |
| **Specialized** | `search-indexing`, `internationalization-i18n`, `feature-flags`, `file-storage`, `automated-documentation` |

---

## Autonomous Experiment Loop

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch):

```
┌─── Infinite Loop (runs until human interrupts) ───┐
│                                                     │
│  1. READ    → Analyze current state                 │
│  2. MODIFY  → Implement experimental improvement    │
│  3. COMMIT  → Git commit with description           │
│  4. TEST    → Run tests, capture output             │
│  5. EVALUATE → Parse against acceptance criteria    │
│  6. DECIDE  → KEEP (improved) or DISCARD (worse)   │
│  7. LOG     → Record to experiments.tsv             │
│  8. NEXT    → Next experiment idea                  │
│                                                     │
│  Simplicity Criterion:                              │
│  - Delete code that improves = KEEP                 │
│  - Add complexity for marginal gain = DISCARD       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Super-Skill/
├── .claude/
│   ├── settings.json              # Hooks configuration
│   └── skills/
│       └── super-skill/
│           ├── SKILL.md           # Main skill definition
│           ├── CHANGELOG.md       # Version history
│           ├── EVOLUTION.md       # GEP Protocol docs
│           ├── skills/            # 33 sub-skills
│           │   ├── autonomous-loop/
│           │   ├── pre-run-upgrade/
│           │   ├── post-run-evolution/
│           │   ├── darwin-evolution/
│           │   ├── high-agency/
│           │   ├── cognitive-modes/
│           │   └── ... (27 more)
│           ├── references/        # Detailed docs
│           └── assets/            # GEP Protocol assets
├── evolver/                       # GEP Evolver engine
├── README.md                      # This file
├── CONTRIBUTING.md                # Contribution guide
└── LICENSE                        # MIT License
```

---

## Influenced By

| Project | Stars | What We Took |
|---------|-------|-------------|
| [karpathy/autoresearch](https://github.com/karpathy/autoresearch) | 58K+ | Autonomous experiment loop, simplicity criterion |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 122K+ | Chain-based workflow patterns |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 52K+ | Multi-agent conversation patterns |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 30K+ | Role-based task delegation |
| [andrewyng/context-hub](https://github.com/andrewyng/context-hub) | - | Curated API documentation |
| [garrytan/gstack](https://github.com/garrytan/gstack) | - | 6 cognitive modes |
| [tanweai/pua](https://github.com/tanweai/pua) | - | High-agency execution methodology |
| [anthropics/skills](https://github.com/anthropics/skills) | - | Skill building best practices |

---

## Roadmap

- [ ] Web dashboard for experiment tracking
- [ ] Multi-project support
- [ ] Custom phase plugins
- [ ] Benchmark suite (SWE-bench, HumanEval)
- [ ] MCP server for external tool integration
- [ ] Community skill marketplace

---

## Contributing

We welcome contributions! AI/vibe-coded PRs welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- Add new sub-skills
- Improve existing phases
- Report bugs and suggest features
- Share your experience stories
- Translate documentation

## Contributors

Thanks to all the people who contributed to this project!

<a href="https://github.com/huangxiding-creator/Super-Skill/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=huangxiding-creator/Super-Skill" />
</a>

---

## License

[MIT License](LICENSE) - Free for personal and commercial use.

---

<div align="center">

**If you find Super-Skill useful, please consider giving it a star!**

[![Star History Chart](https://api.star-history.com/svg?repos=huangxiding-creator/Super-Skill&type=Date)](https://star-history.com/#huangxiding-creator/Super-Skill&Date)

</div>

---

## 概述

Super-Skill 是一个**生产级 Claude Code 技能**，通过结构化的14阶段工作流、内置自进化机制、自主实验循环和33+专业集成技能，彻底改变 AI 构建软件的方式。

**核心创新**：将 [karpathy/autoresearch](https://github.com/karpathy/autoresearch) 的实验循环模式应用于软件开发 — 自动运行实验、保留改进、丢弃退化，直到你叫停为止。

### 为什么选择 Super-Skill？

| 使用前 | 使用后 |
|--------|--------|
| 每步手动提示 | 14阶段自主工作流 |
| 无质量保障 | 内置QA、安全扫描、覆盖率检查 |
| 会话间上下文丢失 | GEP自进化捕获经验教训 |
| 单智能体开发 | 层级式 Planner-Worker-Judge 编排 |
| 需要人工监督 | 24小时无人值守自主运行 |

### 核心特性

- **14阶段自主工作流** — 愿景 → 可行性 → 发现 → 开发 → QA → 部署 → 进化
- **自主实验循环** — 灵感来自 [karpathy/autoresearch](https://github.com/karpathy/autoresearch)（58K+ Stars）
- **GEP自进化** — 达尔文哥德尔机模式，持续自我改进
- **33+集成技能** — 测试、安全、API设计、数据库、监控等
- **Hooks自动执行** — 通过 Claude Code hooks 实现运行前升级 + 运行后进化
- **层级编排** — Planner-Worker-Judge 模式实现多智能体协调
- **上下文工程** — JIT上下文加载、渐进式披露、压缩生存
- **3个交互点** — 用户仅在：输入、需求确认、方案审批时参与

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/huangxiding-creator/Super-Skill.git
cd Super-Skill

# 全局安装（需要 Claude Code）
npx skills add .claude/skills/super-skill --global --yes
```

在 Claude Code 中描述你想构建的内容即可：

```
> 帮我构建一个带实时协作的任务管理应用
```

Super-Skill 会自动触发并编排全部14个阶段。

### 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

### 许可证

[MIT 许可证](LICENSE) - 个人和商业用途免费。
