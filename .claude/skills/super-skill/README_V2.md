# Super-Skill V2: Autonomous Development Orchestrator

## 🎯 核心理念："Think First, Code Later"（先想后做）

### 核心原则

**最大化前期思考，最小化返工和迭代**

通过12个系统化阶段，从可行性分析到生产交付，完全自主执行，零用户交互。

---

## 📋 What's New in V2

### 主要升级

1. **12阶段工作流**（原8阶段）
   - Phase 1: 可行性检查 (CC-FPS) - **最高优先级**
   - Phase 2: GitHub Discovery - **第二优先级**
   - Phase 3: Knowledge Base - **第三优先级**
   - Phase 4: Requirements Engineering
   - Phase 5-5b: Architecture & Design
   - Phase 6: WBS (Work Breakdown Structure)
   - Phase 7: Project Initialization
   - Phase 8: Autonomous Development - **完全自主，零用户交互**
   - Phase 9: QA (Quality Assurance)
   - Phase 10: Ralph Loop Optimization - **10次迭代**
   - Phase 11: Deployment
   - Phase 12: Project Summary

2. **三个交互点模式**
   - 交互点1：原始需求输入
   - 交互点2：最终需求确认（Phase 4结束）
   - 交互点3：完整开发方案确认
   - **之后**：完全自主执行，零用户交互

3. **自动更新和版本控制**
   - 启动时自动检查所有嵌套技能版本
   - 自动下载并安装更新
   - 创建版本快照（支持回撤）
   - 使用 `skill-version-manager` 管理版本

4. **自我进化能力**
   - 使用 `self-evolving-skill`
   - 每次项目后自动学习
   - 提取成功模式和失败教训
   - 持续优化工作流

5. **整合关键技能**
   - ✅ `feasibility-check` - 可行性分析
   - ✅ `github-discovery` - GitHub开源发现
   - ✅ `continuous-learning-v2` - 知识库构建
   - ✅ `ralph-loop` - 智能迭代优化
   - ✅ `tdd-workflow` - TDD测试驱动
   - ✅ `security-review` - 安全审查
   - ✅ `code-review` - 代码质量

---

## 🚀 快速开始

### 方式1：自动激活（推荐）

直接告诉 Claude 你想构建什么：

```
"我想构建一个任务管理应用，使用React和Node.js"
```

Super-Skill V2 会自动激活并引导你通过所有12个阶段。

### 方式2：使用初始化脚本

快速创建新项目（包含所有文档模板）：

```bash
python C:\Users\91216\.claude\skills\super-skill\scripts\init_project.py my-project-name ./output-dir
```

这将创建：
- 完整项目结构
- 所有阶段文档模板
- 每个阶段的适当目录
- README 和 .gitignore

### 方式3：显式调用

```
"使用 super-skill 帮我构建..."
```

---

## 📊 完整的12阶段工作流

### 执行模型

```
用户输入 → Phase 1-3 (规划) → 用户确认 →
Phase 4-12 (自主执行) → 交付
```

**关键规则**：
- **Phase 1-3**：需求分析和可行性检查，可以询问用户
- **Phase 4开始后**：零用户交互，完全自主决策和执行
- **所有决策基于**：最佳实践、GitHub发现、技术可行性、质量标准

### Phase 1: 可行性检查 (CC-FPS) - **最高优先级**

**触发器**：用户提出任何开发需求时立即启动

**目标**：
- 评估技术可行性
- 评估经济可行性
- 评估运营可行性
- 评估时间可行性
- 识别关键风险和阻塞因素

**使用技能**：`feasibility-check`

**输出**：`FEASIBILITY_REPORT.md`

**决策点**：
- 可行性评分 ≥ 60/100：自动继续 Phase 2
- 可行性评分 < 60：停止并呈现发现，请求用户决策

### Phase 2: GitHub Discovery - **第二优先级**

**目标**：
- 搜索现有开源解决方案
- 评估最佳实践
- 克隆并适配现有项目（如适用）
- 决定：复制 vs 从头开发

**使用技能**：`github-discovery`

**输出**：`GITHUB_DISCOVERY_REPORT.md`

**决策点**：
- 找到合适项目（≥80%需求覆盖）：克隆并设置，自动继续 Phase 4
- 无合适项目：自动继续 Phase 3

### Phase 3: Knowledge Base - **第三优先级**

**目标**：
- 建立项目领域知识库
- 收集最佳实践和模式
- 记录技术决策和依据
- 准备开发环境

**使用技能**：`continuous-learning-v2`、`skill-from-masters`

**输出**：`KNOWLEDGE_BASE.md`

**自动继续**：Phase 4（需求工程）

### Phase 4: Requirements Engineering

**交互点2：需求确认**

这是用户三个交互点中的**第二个**。需要用户确认需求。

**使用技能**：`prompt-architect`

**输出**：`REQUIREMENTS.md`

**自动继续**：用户确认需求后 → Phase 5

### Phase 5-5b: Architecture & Design

**目标**：
- 设计系统架构
- 选择技术栈
- 定义接口和数据模型
- 确保可扩展性和性能

**使用技能**：`architect`、`skill-from-masters`、`frontend-patterns`/`backend-patterns`

**输出**：
- `ARCHITECTURE.md`
- `API_DESIGN.md`（如适用）
- `DATABASE_SCHEMA.md`（如适用）

**自动继续**：Phase 6（WBS）

### Phase 6: WBS (Work Breakdown Structure)

**目标**：
- 创建详细工作分解
- 识别任务依赖关系
- 估算工作量
- 规划里程碑

**使用技能**：`planner`、`planning-with-files`

**输出**：`WBS.md`

**自动继续**：Phase 7（项目初始化）

### Phase 7: Project Initialization

**目标**：
- 初始化项目结构
- 配置开发工具
- 设置测试框架
- 准备 CI/CD 流水线

**输出**：完整的项目设置（仓库、工具、CI/CD）

**自动继续**：Phase 8（自主开发）

### Phase 8: Autonomous Development - **零用户交互**

**核心原则**

**从此阶段开始，Claude Code 完全自主执行，不再征求用户任何意见。**

**所有决策自主做出**：
- 技术选型决策
- 实现方案选择
- 优先级排序
- 资源分配
- 风险应对

**使用技能**：`tdd-workflow`、`security-review`、`code-review`、`superpowers`

**开发流程**（每个功能模块）：

1. 写测试 (RED) → 2. 实现最小代码 (GREEN) → 3. 运行测试 → 4. 重构优化 → 5. 安全审查 → 6. 代码审查 → 7. 提交代码 → 8. 更新文档

**完成条件**：
- ✅ 所有功能需求已实现
- ✅ 所有验收标准已满足
- ✅ 测试覆盖率 ≥ 80%
- ✅ 所有安全审查通过
- ✅ 所有代码审查通过
- ✅ 文档完整

**自动继续**：Phase 9（QA）

### Phase 9: QA (Quality Assurance)

**目标**：
- 全面质量保证检查
- 端到端测试
- 性能测试
- 安全扫描

**使用技能**：`code-review`、`security-review`、`e2e`、`test-coverage`

**输出**：`QA_REPORT.md`

**质量门**：
- ✅ 代码质量：无 CRITICAL 或 HIGH 问题
- ✅ 安全扫描：无 HIGH 或 CRITICAL 漏洞
- ✅ 性能：满足所有非功能需求
- ✅ E2E 测试：所有关键路径通过
- ✅ 测试覆盖率：≥80%
- ✅ 所有测试通过

**自动继续**：所有质量门通过 → Phase 10（Ralph Loop）

### Phase 10: Ralph Loop Optimization - **10次迭代**

**目标**：
- 系统性优化代码质量
- 优化性能
- 清理技术债务
- 迭代至生产级质量

**使用技能**：`ralph-loop`、`refactor-clean`

**迭代终止条件**（满足任一即可停止）：

**提前终止**：
- ✅ 项目达到生产级运行质量（各子功能100%优秀）
- ✅ 连续3次迭代无显著改进
- ✅ 所有关键指标达到优秀级别

**强制终止**：
- ✅ 完成10次完整迭代

**每次迭代包含**：
1. 分析（识别优化机会）
2. 优化（性能+重构+债务清理）
3. 测试（全测试套件+基准测试）
4. 质量验证（安全+代码质量）
5. 文档（更新迭代日志）

**输出**：`ITERATION_LOG.md`

**自动继续**：满足任一完成条件 → Phase 11（部署）

### Phase 11: Deployment

**目标**：
- 准备生产部署
- 执行部署
- 验证部署成功
- 配置监控

**输出**：
- `DEPLOYMENT_PLAN.md`
- 发布标签（v1.0.0）
- 发布说明

**部署后监控**：
- 错误率 < 0.1%
- 响应时间满足需求
- 资源利用率健康

**自动继续**：部署成功且系统稳定 → Phase 12（项目总结）

### Phase 12: Project Summary

**目标**：
- 生成项目总结报告
- 归档所有交付物
- 知识转移
- 项目回顾

**使用技能**：`doc-updater`、`self-evolving-skill`

**输出**：`PROJECT_SUMMARY.md`

**自我进化**：
- 捕取教训学习
- 提取成功模式
- 记录需避免的陷阱
- 更新技能知识库
- 进化决策逻辑

---

## 🔄 自动更新和版本控制

### 启动序列

每次 Super-Skill 启动时自动执行：

```bash
# 检查技能更新
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py check

# 创建版本快照
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py snapshot <project-dir>

# 列出快照（如需回撤）
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py list <project-dir>

# 回撤到快照（如需回撤）
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py rollback <project-dir> <snapshot-name>
```

### 检查的技能

- `feasibility-check`
- `github-discovery`
- `continuous-learning-v2`
- `skill-version-manager`
- `self-evolving-skill`
- `ralph-loop`
- `tdd-workflow`
- `security-review`
- `code-review`
- `refactor-clean`
- 以及所有其他引用技能

### 版本管理

使用 `skill-version-manager` 进行：
- 快照创建（每个phase开始前）
- 版本对比
- 一键回撤到任意版本点
- 版本元数据记录（时间、原因、结果）

---

## 🤖 人机高效协同模式

### 三个关键节点

用户**只在**这3个关键节点介入：

#### 1️⃣ 原始需求输入

**示例**：
```
用户："我想构建一个在线教育平台"
```

**Claude 行动**：
- 理解用户意图
- 启动 Phase 1（可行性格查）

#### 2️⃣ 最终需求确认（交互点2）

**位置**：Phase 4（需求工程）结束时

**Claude 行动**：
- 呈现完整需求规格
- 列出所有功能和优先级
- 说明约束和假设
- 估算时间线和努力

**用户需要确认**：
- "是的，继续" 或
- 提出修改建议

#### 3️⃣ 完整开发方案确认（交互点3）

**位置**：Phase 4 确认后，Phase 5 开始前

**Claude 行动**：
- 呈现完整开发计划
- 包括工作分解结构
- 里程碑和时间线
- 资源分配策略

**用户需要确认**：
- "是的，自主执行" 或
- 提出方案调整建议

### 确认后的完全自主执行

**用户确认后**：
- ✅ **零用户交互**
- ✅ Claude Code 完全自主决策
- ✅ 所有技术选择自主做出
- ✅ 所有实现方案自主决定
- ✅ 只在项目完成时报告

**自主决策框架**：
1. 咨询 `KNOWLEDGE_BASE.md` 获取领域模式
2. 咨询 `ARCHITECTURE.md` 获取设计指导
3. 使用相关专业技能获取建议
4. 基于以下因素做出决策：
   - ✅ 最佳实践
   - ✅ 项目约束
   - ✅ 质量要求
   - ✅ 性能要求
5. 记录决策并说明理由
6. 继续实施

**永不停止征求用户意见。始终自主做出明智决策。**

---

## 📦 技能结构

### 文件组织

```
super-skill/
├── SKILL.md                      # 核心技能定义（12阶段流程）
├── README_V2.md                 # 本使用说明
├── scripts/                      # 辅助脚本
│   ├── auto_update.py            # 自动更新和版本控制
│   ├── init_project.py           # 项目初始化脚本
│   └── package_skill.py          # 技能打包脚本
├── references/                   # 参考文档和模板
│   ├── templates.md
│   ├── KNOWLEDGE_BASE_TEMPLATE.md
│   └── REQUIREMENTS_TEMPLATE.md
└── assets/                      # 资源文件（空）
```

---

## 📖 使用示例

### 示例：完全自主执行流程

```
用户："构建一个任务管理应用"

Claude (Super-Skill V2 激活):

[Phase 1: 可行性格查]
→ 运行 feasibility-check
→ 生成 FEASIBILITY_REPORT.md
→ 评分：85/100 - GO
→ 自动继续

[Phase 2: GitHub Discovery]
→ 运行 github-discovery
→ 找到47个任务管理应用
→ 分析前3名
→ 最佳匹配覆盖75%需求
→ 决策：克隆 + 适配
→ 自动克隆并设置
→ 自动继续

[Phase 3: Knowledge Base]
→ 运行 continuous-learning-v2
→ 构建领域知识
→ 记录技术决策
→ 自动继续

[Phase 4: Requirements - 交互点2]
→ 与用户澄清需求
→ 呈现完整规格说明
→ 用户确认："是的，继续"
→ REQUIREMENTS.md 基线化
→ 自动继续

[Phase 5: Architecture]
→ 设计系统
→ 创建 ARCHITECTURE.md
→ 自动继续

[Phase 5b: Detailed Design]
→ 设计组件
→ 创建 API_DESIGN.md
→ 自动继续

[Phase 6: WBS]
→ 创建工作分解
→ 定义127个任务
→ 识别关键路径
→ 自动继续

[Phase 7: Initialization]
→ 设置仓库
→ 配置工具
→ 设置 CI/CD
→ 自动继续

[Phase 8: Autonomous Development - 零用户交互]
→ 自主执行127个任务
→ 做出234个自主决策
→ 提交347次
→ 零用户交互
→ 所有功能完成
→ 所有测试通过（100%）
→ 覆盖率87%
→ 自动继续

[Phase 9: QA]
→ 运行 code-review
→ 运行 security-review
→ 运行 E2E 测试
→ 运行性能测试
→ 所有质量门通过
→ 自动继续

[Phase 10: Ralph Loop - 10次迭代]
→ 迭代1/10：性能 +15%
→ 迭代2/10：代码质量 B→A
→ 迭代3/10：安全清洁
→ ...
→ 迭代7/10：连续3次无改进
→ 达到生产级质量
→ 提前终止
→ 自动继续

[Phase 11: Deployment]
→ 创建部署计划
→ 执行部署
→ 验证成功
→ 创建发布 v1.0.0
→ 自动继续

[Phase 12: Project Summary]
→ 生成 PROJECT_SUMMARY.md
→ 归档交付物
→ 自我进化（吸取教训）
→ 更新技能到 v2.1

[最终交付]
→ "🎉 任务管理应用完成！
→ 交付版本：v1.0.0
→ 覆盖率：87%
→ 质量：A
→ 所有功能正常工作
→ 总结：[PROJECT_SUMMARY.md 路径]
→ 仓库：[路径]
→ 准备生产使用"

Phase 4 之后零用户交互。
```

---

## ⚙️ 配置和定制

### 环境变量（可选）

可以设置环境变量来自定义行为：

```bash
# Super-Skill 配置
SUPER_SKILL_AUTO_UPDATE=true           # 自动检查更新（默认：true）
SUPER_SKILL_SNAPSHOT_ENABLED=true       # 启用版本快照（默认：true）
SUPER_SKILL_MAX_ITERATIONS=10          # Ralph Loop 最大迭代次数
SUPER_SKILL_TARGET_COVERAGE=80         # 目标测试覆盖率
```

### 自定义工作流

如需自定义工作流，可以编辑 `SKILL.md`，但保持核心12阶段结构。

---

## 🔧 故障排除

### 常见问题

**Q: Super-Skill 没有自动激活？**

A: 确保描述中包含关键词如：
- "构建"
- "开发"
- "实现"
- "创建项目"
- "完整应用"

或显式调用：
```
"使用 super-skill 帮我..."
```

**Q: 如何回撤到之前的版本？**

A:
```bash
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py list <project-dir>
# 选择快照名称
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py rollback <project-dir> <snapshot-name>
```

**Q: 如何查看当前技能版本？**

A:
```bash
python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py check
```

---

## 📈 版本历史

- **v2.0** (2026-02-12): 完全重写，包含：
  - 12阶段自主工作流
  - GitHub Discovery 集成
  - Feasibility-First 原则
  - 自动更新和版本控制
  - 自我进化能力
  - 三个交互点模式

- **v1.0** (2026-02-12): 初始8阶段工作流

---

## 🎯 总结

### 核心特点

✅ **"Think First, Code Later"** - 最大化前期思考
✅ **12阶段工作流** - 从可行性格查到项目总结
✅ **三个交互点** - 用户只在关键节点介入
✅ **完全自主执行** - Phase 4后零用户交互
✅ **GitHub Discovery** - 优先使用开源最佳实践
✅ **Feasibility-First** - 最优先级可行性格查
✅ **自动更新** - 启动时检查并更新所有技能
✅ **版本控制** - 快照和回撤支持
✅ **自我进化** - 每次项目后自动学习和优化
✅ **生产级质量** - Ralph Loop 10次迭代至优秀级别
✅ **全面集成** - 与所有专业技能无缝协作

### 适用场景

- ✅ 完整的全栈应用开发
- ✅ 复杂功能的系统化实现
- ✅ 需要结构化项目管理的工作流
- ✅ 从需求到交付的完整生命周期
- ✅ 需要最佳实践和GitHub发现的项目

---

**🚀 Super-Skill V2：自主、全面、生产级！**
