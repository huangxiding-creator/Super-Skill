# CC 指挥手册 — CC Command Playbook

> Operational companion to [dev-constitution.md](dev-constitution.md). These are the
> author's own working instruction templates, iteration budgets, cadence parameters, and
> tool matrices, extracted from 《总包大脑实战方案》 (438 pp., 2026-09-08) and validated
> across the delivered portfolio (~40 projects, `E:\CPOPC` + `E:\AIResearch`). Copy-paste
> them; do not reinvent them. Every block cites the article it operationalizes.

## 1. 六步元链 · The six-step meta-chain (SkillMix)

The author's standing recipe for any non-trivial CC task (C6/C8/C9):

```text
请使用 prompt-engineering-skills 帮我优化上面的全部提示词。
基于优化后的提示词，请使用 Superpowers 帮我完善上述需求，形成质量更高的开发需求。
基于完善后的开发需求，使用 planning-with-files 详细拆解任务，制定详细的开发计划。
再使用 Superpowers 并组织开发，每项小任务完成后，记录完成状态。
执行每项具体开发任务前，先使用 Skill From Masters 发现和整合大师框架、原则和最佳实践。
整个项目开发完成后，使用 ralph-loop 对整体和每项功能进行迭代优化，实现项目的稳定高效、
生产级运行，最大迭代 N 次；一次性完成所有迭代，中途无需用户发送指令。
迭代完成后，梳理本项目开发全过程中我提出的所有要求、你的解决方案及实施结果，
形成完整的开发总结报告。
```

## 2. 批准制指令模板 · The approval-gated template (C7)

```text
首先检查全部全局 Skills 是否最新版，先更新再干活。
对本项目现有开发成果全面了解熟悉，为不重复造轮子做好准备。
在此基础上提出你认为 10 倍好的开发方案（含：为什么原始想法直接实现会失败；
需确认点逐一列出），经我批准同意后组织实施。
实施完成后在真实环境测试，自行迭代优化至 100% 完美执行到位（最大迭代 N 次），
完成后通过企业微信通知我。
```

红线约束随附: 替换敏感信息后才可推送 GitHub 且不影响本地运行 · 清理临时文件但
千万不要误删运行所需文件 · 只增不删 (见 R6/R8)。

## 3. ralph-loop 句式与预算 · Iteration syntax & budgets

`/ralph-loop [任务] --max-iterations N --completion-promise [完成标准]`

| 场景 | 预算 |
|------|------|
| 常规迭代 | 10–20 次 |
| 重点难点 (人设轮换/关键功能) | 50 次 |
| 生产运行-日志-修复循环 | 最高 100 次 |

**终止条件**（全部满足才停）: 测试全过 + 质量 A 级 + 性能达标 + 无高危漏洞 +
连续 3–5 次迭代无改进 + 达到最大次数。每轮留痕: 问题编号+症状日志+根因（修复前/
后代码对照）+验证结果+`文件:行号`。修复必须展示 before→after 实测数据 (C11)。

## 4. 无人值守三句式 · The three unattended sentences (C8/C13)

任何无人值守任务提示词的固定结尾：

1. **不要跳过任何一个步骤。**
2. **一次性完成所有迭代，中途无需征询我任何意见、无需我执行任何操作。**
3. **确保任何一个环节出现错误都能继续往下执行；即使前置任务结果不完整也能继续。**

遇错自救协议: 截图 + 查历史经验 → 自主分析 → 自主修复 → 接续运行，不得请示。

## 5. 需求文档回放法 · Requirement replay (before renovating a mature project)

把最初需求 + 全部交互记录整理成精确需求文档，要求 CC 验证: "把这份文档发给一个全新
会话，能一次性复现到当前开发成果"。固化需求后才开工改造 — 否则改造即失忆。

## 6. 运行节奏参数表 · Cadence parameters (from the portfolio)

| 场景 | 参数 | 出处 |
|------|------|------|
| NotebookLM 文件处理轮询 | 每 10 min | Auto-WriteBook |
| 专著撰写完成度轮询 | 每 30 min | 同上 |
| 大脑回答完成判定 | 每 1 min 检测；字数 3 次不再增长 = 完成；回复 <500 字符重发，≤5 次 | ZBBrain-Write |
| 节内容生成指令间隔 | 1–2 min | 同上 |
| 拟人间隔 | 3–10 min 随机 · **永不自动调整** (R7) | WeVideo/WeChat-AutoPub |
| 群发 / 发文间隔 | 随机 5–10 s / 3–5 min | PDF |
| 反爬 | 每搜索 2 页暂停 60–120 s；到 450 次调用**主动**暂停 20 min (R10) | GCBrain/SouGouWeDown2 |
| 错峰 | 深夜档 0:00–5:00；晚间模式 19:00 起 | RSS-Auto/ZBBrain |
| 超时止损 | 2 h 未完成即停，完成多少算多少 | PDF |
| 长任务汇报 | 每 15 min 中间汇报 + 最终成果；运行期每小时汇报 | PDF |
| 企微 markdown | ≤3800 字节，按字符边界截断 (errcode 40058) | WeChat-AutoPub |
| 大批量分片 | >20 条/项时每 20 条配一个生成智能体，防单智能体超载 | PDF (200 张漫画事故) |

## 7. 质量自查清单 · Quality self-checks (before & after)

**答前 8 问**: 理解本质？选对框架？≥3 层递归？数据支撑？多角度验证？交付物明确？
风险披露？值得追问？
**答后 5 问**: ≥1500 字？结构清晰？金字塔原理？独特洞察？直接可用？

内容红线: 一篇只讲一个观点 · 禁"随着…的发展/近年来"式开篇 · 结尾禁总结全文 ·
数字要具体 ("损失 800 万" 胜过 "损失惨重" 百倍) · 排版禁有序/无序列表样式（公众号
端易乱）· 信息图中文字号 ≥14pt 且留白充足 · 需求字数（"不少于50字"）不得泄漏进
成果。

**交付物导向**: 不写"你应关注合同条款"，写"这是 10 个关键条款清单和审查模板"。

## 8. 工具矩阵 · Tool matrix (实测 √/× 才可信)

- **采集**: SouGouWeDown√ · WeArticleDS√ · WenXian-AutoDown√ · HolePaperDown√ ·
  yt-dlp√ · Manus√ · AnyGen√ · refly√（定时稳定运行）· NoteBookLM-Auto√ ·
  **gpt-crawler×**（唯一失败项）
- **数据通道**: RSS > 平台 API（零 key、零频控、零封号、自带全文）；微信侧不走
  API 扫描（200013/200003）；知网/万方/维普无公开 API → RSSHub vs 自写爬虫择优
- **NotebookLM 硬限制**: 500 笔记本 / 每本 300 来源 / 日 500 对话·20 音频·20 视频
  → 来源预算控 290 预留提炼空间；"来源即原料"：加工完滚动移除最早来源，
  "根基知识"来源永久保留
- **情报四引擎并行**: Exa / Perplexity / Tavily / Jina（保覆盖）
- **浏览器**: Playwright 稳定底座 + Stagehand AI 理解（选择器难定位时）；
  能逆向破解成 API 就转 API（更可靠）；登录态以业务终态验证（下载入口再弹登录 =
  未真登录）
- **模型**: 免费优先 + 多模型轮换分摊限流 + probe 打点实测才入白名单 (R9)；
  高低分工（结构化/拟标题用高质量模型，排版用 flash）力争 0 成本

## 9. 通知与审计 · Notification & audit

企业微信 Webhook 关键节点 + 完成 + 失败告警（看护器 3 轮重拉失败才告警，60 min
节流防轰炸）；每次成功发布通知一次；每次运行落 `data/runs/{时间戳}.json` 可审计；
失败要计数、列文件名、提示重试 — 禁止静默 (R2)。
