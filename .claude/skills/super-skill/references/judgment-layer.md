# 判断层 (Judgment Layer) — Jev × TypeSafe System One

> 来源：typesafe-ai 官方 skill（docs.typesafe.ai）+ 站内 paistation.judgment
> E1-E3 实验谱系（2026-09-19/20）+ Super-Skill 融合实验
> （`automation/logs/jev_fusion_exp_20260922_v2.json`），V4.1.16 接线。

## 心智模型：判断是原语，不是生成

Jev 返回**类型化答案+概率**而非文本：`Noul`＝命题为真的概率（无独立
confidence，0.5≈五五开不是"中等"）；`Choice`＝集合中选一（分布对比竞争项，
confidence＝分布集中度≠正确性许可）；`Score`＝有序等级上的概率加权位置。
**代码拥有工作流，模型只供可编程的语义常识**——state 放证据、instructions
放判断、criteria 放答案定义。

## 三条使用铁律

1. **免费模型优先**：确定性检查（正则/行数/枚举/哈希对比）永远用代码做；
   Jev 只占免费做不到的**语义位**（相关性、兑现、路由）。定价 $0.0001 量级/次。
2. **fail-soft 契约**：Jev 缺席（开关关/熔断/网络/坏载荷）→ 调用方降级回
   原行为，**绝不反噬主链**。一键开关：`PAI_JEV` env 硬关 >
   `config/jev.ini` enabled > key 缺失。
3. **证据先行（V1→V2 铁教训）**：证据缺席 ≠ 模型错误——只给文件头部时
   中段增量 0.16 假阴、标题党报错页 0.54 假阳；**code 负责证据组装**
   （短文全文/关键词定向捞段/剥 base64），Jev 只管判断（sde_cascade 模式）。

## 本仓库接线点（automation/，周度管线）

| 位 | 接线 | 阈值 | 实测分离 |
|----|------|------|----------|
| routing | S2 材料预筛 `jev_legs.screen_material`：低值材料不进蒸馏省 token | 0.5 | 正 0.62-0.91 / 负 0.03-0.12 |
| completion | S3 manifest 核验 `jev_legs.verify_manifest`：文件是否兑现声称 | 0.5 | 正 0.80-0.95 / 负 0.02-0.24 |
| verification | S3 确定性硬门（**代码位**）：SKILL.md <500 行 + 版本脚注在位，违规整轮回滚 | — | 确定性 |

问句措辞**钉死不改**（E3 教训：抽象问句诱导保守 0.17-0.27，具体问句
0.94/0.08）；改问句＝重跑实验重新定阈值。

## 随身判断原语（assets/jev_ask.py，交互开发用）

```bash
# 完成判定：DoD/声称核验（verify & escalate：<0.5 升级人眼/推理模型）
python assets/jev_ask.py noul --state '{"claim":"...","evidence":"<实测输出>"}' \
  --instructions "证据是否支持该声称已完成？" --true "…" --false "…"

# 路由：Phase/处理流/方案选择（route & fill：分布对比再填参）
python assets/jev_ask.py choice --state '{"task":"..."}' \
  --instructions "该走哪条处理流？" --criteria '{"bug":"…","feature":"…"}'
```

key 取 `TYPESAFE_API_KEY` env 或 `--key-file`（ini `[typesafe] api_key`）；
**凭据永不入 git 永不打日志**。输出恒为 JSON（故障也是 `{"ok":false}`，
退出码 0），管道友好。

## 适用判断（何时伸手拿这个原语）

- **验收门/DoD**：声称与实测证据是否相符（对抗 AI 自报"已完成"）
- **材料/工单路由**：语义分诊（枚举集合中选一，分布可解释）
- **检索命中复核**：词面撞词≠语义命中（hollow/confirmed 分离，E3 结构）
- **不确定性守门**：noul∈[0.4,0.6] 或 confidence 低 → 升级，不硬拍板
