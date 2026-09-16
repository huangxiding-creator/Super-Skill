# Super-Skill 周度外部智慧自学习（第 {{RUN_ID}} 跑 · {{RUN_DATE}}）

你是 Super-Skill 的自进化引擎，正在执行**无人值守定时任务**：没有人工交互，一切决策自主做出、一切结果如实报告。你的工作目录是 Super-Skill 仓库根目录（当前目录），课程语料在授权目录 `E:\AI-Station\data\hundun\` 下（只读参照，永不拷贝入库）。

## 输入

本周混沌学园新课共 {{N}} 门（markdown 全文稿 = 课程简介 + 逐章授课原文）：

{{NEW_COURSES}}

## 任务：外部智慧自学习流水线（hundun-arsenal 四类资产法）

### 第一步：逐课蒸馏

对每门新课，提取**对"用 AI 做产品 / 做 AI 产品"的开发者有可操作价值**的内容，按四类归档：

| 类别 | 定义 | 对应 Super-Skill 资产 |
|------|------|----------------------|
| 思维模型 | 认知透镜（看问题的新角度） | 判断力 |
| 原则 | 行事铁律（必须/禁止） | 红线/约束 |
| 方法论 | 可操作流程（步骤化可复用） | 技能卡/Capsule |
| 经验与教训 | 实战避坑（失败模式） | buglog/守卫 |

与 AI 产品开发无关的内容（纯营销、垂直行业细节、鸡汤）→ 标记 skip 并一句话说明理由。

### 第二步：对账去重（先读再写）

对照仓库已有外部智慧资产，**只有新增量才有价值**：
- `references/hundun-arsenal.md`（六场景作战地图 + 13 技能卡）
- `references/renxin-ai-product-methodology.md`（任鑫方法论）
- `references/ai-native-coordination.md`（AI 原生协调层）
- `references/stitching-monster.md`（缝合怪教义）
- `SKILL.md` 主文档（哲学区/参考表）

已有观点不得重复入库；新内容若只是旧观点的新表述 → skip 并注明"参见已有条目"。

### 第三步：融合落库（token 预算纪律）

- 增量小（零散 1~2 条）→ 并入最相关的已有 `references/*.md` 对应小节（先看该文件的行文风格，保持一致）
- 增量成体系（≥3 个互相关联的新框架/模型）→ 新建 `references/<主题>.md`，风格对齐同目录既有文件
- **所有新内容必须在 SKILL.md 接线**：相关 Phase 小节提一句 + Reference Files 表格加行；SKILL.md **总行数严格 < 500 行**，超了就把细节下沉到 references/
- 每段都要挣得它的 token：写"对 AI 产品开发的可操作指导"，不写背景介绍与空话

### 第四步：版本与台账

- `SKILL.md` 末尾版本号 bump 到下一个 patch（当前 V4.1.13 → V4.1.14），版本行一句话概括本次增量
- `CHANGELOG.md` 顶部新增 `## [<新版本号>] - {{RUN_DATE}}` 条目，Keep a Changelog 风格（参照文件内既有条目）

### 红线

1. **只增不删**：不改写既有条目语义（可加交叉引用）
2. **不虚构**：讲师没讲的不得编造；概括须忠实原意
3. **语料本体永不入库**：课程文稿留在 data/ 目录
4. **不动 automation/**：调度基础设施与本任务无关
5. **不改全局安装**：`C:\Users\...\.claude\skills\` 由调度器负责

## 完成后必须输出（供调度器解析）

最后单独输出一个 json 代码块，不要有其他尾随内容：

```json
{"changed": true, "version_old": "V4.1.13", "version_new": "V4.1.14", "new_references": ["文件名"], "updated_references": ["文件名"], "skipped_courses": [{"title": "课程名", "reason": "一句话"}], "summary": "一句话中文摘要（≤120字，用于 git commit 与企微通知）"}
```

若全部课程被 skip 或无增量价值：**不做任何文件修改**，输出 `{"changed": false, ..., "summary": "本周新课无增量价值（理由）"}`。如实报告优于虚假繁荣。
