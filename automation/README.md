# Super-Skill 自动化（automation/）

## 每日自更新（每天 22:00 北京时间，任何电脑可用）

调研 GitHub 与网络上同类项目的最新优秀做法 → 吸收 ≤3 个小而高价值的改进 → 全量门禁 → 提交 → 全局安装 → 推送。

```bash
python automation/schedule_daily.py            # 注册（Windows 计划任务按 UTC+8 锚定、夏令时不漂移；macOS·Linux crontab 换算本地时间）
python automation/schedule_daily.py --status   # 查看下次运行
python automation/superskill_daily.py --dry-run   # 手动演练：只扫描+蒸馏，不改仓库
python automation/superskill_daily.py             # 立即完整跑一轮
python automation/schedule_daily.py --remove   # 取消
```

| 段 | 内容 | 失败策略 |
|---|---|---|
| D0 预检 | PAUSE 旗标 · 操作系统级文件锁 `~/.claude/super-skill-pipeline.lock`（进程退出即由系统释放；周日 22:00 与周度同时启动时后者排队，每日最多等 150 分钟）· 中断恢复（上次运行被关机/超时打断 → 能证明是它的残留改动才 `git stash` 保存后继续：只在技能/插件文件内、HEAD 未动、修改时间在那次运行窗口内）· 已跟踪文件必须干净 · 从 origin 快进 | 等锁超时 → 当天跳过；残留改动混有人工修改 / 不干净 / 分叉 → 跳过，绝不混入人工改动 |
| D1 雷达 | `radar.py`：GitHub 搜索（`radar_config.json` 关键词/话题，近 7 天活跃）+ 观察名单新版本 + Hacker News；首跑以 `upgrade-workspace/research` 204 个已研究仓库为种子去重 | 单源失败不影响其他源 |
| D2 蒸馏 | 无头 `claude -p`（`daily_research_prompt.md`，预算 `SUPERSKILL_DAILY_BUDGET` 默认 $3）阅读候选 README/版本说明，**只写暂存区** `automation/daily_out/` + `manifest.json` | 直接改仓库 → 自动丢弃；无结果 JSON → 回滚 |
| D3 落位 | 确定性白名单：允许 `SKILL.md`/`references/`/`skills/`/`engine/`/`agents/`/`assets/`；**禁止**改裁判与关键接线（`hooks/` `scripts/` `evals/` `install.py` `phases.json` 现有测试） | 违规条目逐条拒绝 |
| D4 记录 | `references/radar/<日期>.md` 日报 + 索引 · 补丁版本号 +1（SKILL.md 脚注 / plugin.json）· CHANGELOG | — |
| D5 门禁 | `scripts/run_all_tests.py` 全量 14 组 + `claude plugin validate` | 任一失败 → 整轮回滚 |
| D6–D8 | 提交 → `install.py --global`（doctor）→ 推送（gh 凭据 → 普通 git → `api_push.py`） | 推送全败保留本地提交 |
| D9 报告 | `automation/logs/daily_<日期>.md`；设置 `SUPERSKILL_NOTIFY_WEBHOOK` 可推送到企微/通用 webhook | best-effort |

已注册过的电脑：改动默认时间后需重新运行一次 `python automation/schedule_daily.py` 才会生效（`--status` 会提示不一致）。
前提：Python ≥ 3.9、git、Claude Code CLI 已登录、`gh auth login` 账号对仓库有推送权限。暂停：新建 `automation/PAUSE`。
可移植：所有路径都从脚本位置推导，计划任务由 `schedule_daily.py` 在每台电脑上本地生成。

---

## 周度自升级（维护机专用）

每周日 22:00（北京时间）无人值守执行一轮：**子技能更新 → 混沌新课蒸馏融合 → 全局安装 → GitHub 推送 → 企微通知**。

## 注册 / 查看计划任务

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\AI-Station\07 任务\Super-Skill\automation\register_weekly_task.ps1"
schtasks /Query /TN "SuperSkillWeekly" /V /FO LIST
```

- 静默执行：`pythonw.exe` 无控制台，全部子进程 `CREATE_NO_WINDOW`
- 错过补跑：关机/未登录错过 22:00 → 开机自动补跑（StartWhenAvailable）
- 并发保护：`MultipleInstances IgnoreNew` + 带标记的 `weekly.lock`（被杀后留下的直接接管；旧版无标记的 8h 后破除）+ 与每日自更新共用的操作系统级管线锁（周日 22:00 两者同时启动时，周度最多等 120 分钟，`SUPERSKILL_WEEKLY_LOCK_WAIT_MIN` 可调；超时跳过并记入 `logs/weekly_lock_skips.log` 与 `state.json`）

## 六段流水线

| 段 | 内容 | 失败策略 |
|----|------|----------|
| S1 | `npx skills update -g`（注册表技能）+ 48 内嵌子技能结构审计（frontmatter/name/≤500行） | best-effort，不挡管线 |
| S2 | **智库多源水位扫描**（04 智库五渠道：一堂/万维钢/微信读书/洞见研报/通往AGI之路；新文件/改动 → 周上限截断，余量记账下周；首跑只消化精选）→ **Jev 预筛**（routing 位：低值材料 <0.5 不进蒸馏省 token，fail-soft 缺席全量放行）→ `hundun_census.py` 刷新 → **缺口 >40 门熔断** → `hundun_batch.py` 幂等增量（0.2s 节流 / 403 自动重登）→ 圈出本周 AI 新课 | 隔离失败（主链继续；智库材料独立存活） |
| S3 | 无头 claude 蒸馏新课 → 四类资产归档 → 对账去重 → **暂存协议**（成品全文写 `automation/distill_out/` + manifest.json，编排器校验白名单后代落 `.claude/skills/super-skill/`——`.claude/**` 是权限敏感路径，LLM 直写必被拒，由确定性层执行写入）→ **确定性硬门**（暂存 SKILL.md <500 行 + 版本脚注在位，违规整轮拒绝）→ **Jev 独立核验**（completion 位：逐条判文件是否兑现 manifest 声称，hollow 升级到企微报告）+ SKILL.md 接线 + CHANGELOG + 版本 bump；**干净工作树闸门**防混入人工改动 | 失败/无增量/声明与暂存不符/硬门违规 → `git checkout` 回滚 |
| S4 | robocopy 镜像 `.claude/skills/super-skill` → `%USERPROFILE%\.claude\skills\super-skill` | 失败即整体 ❌ |
| S5 | 提交 → 三层推送回退：`git push` → 剥代理重推 → `api_push.py`（gh api 数据通道，仅快进；远端含本地历史没有的内容时拒推，防止把别人的成果静默回滚） | 全败保留本地提交，企微告警 |
| S6 | 企微通知：**站在用户角度的价值报告**（先讲这周 Super-Skill 学会了什么新本事、用户得到什么，例行检查一句话带过，技术细节只进日志）；通道回退 OAuth 机器人直达 → webhook → 日志降级 | best-effort |

## 运维操作

```text
暂停    新建 automation/PAUSE 文件（main 首行早退，免提权；计划任务照常触发但整轮跳过）
恢复    删除 automation/PAUSE
手跑    automation/run_now.cmd（前台看全程）
单段    python automation/superskill_weekly.py --stages s2,s3
日志    automation/logs/weekly_YYYYMMDD_HHMMSS.log（蒸馏输入输出同目录）
状态    automation/state.json（last_run / 各段结果 / 新课清单）
```

## 关键事实

- **判断层（2026-09-22 Jev×TypeSafe 融合）**：`automation/jev_legs.py` 复用站内 `paistation.judgment.JudgmentClient`（熔断/一键开关/fail-soft 三契约），两位接线= S2 材料预筛（routing）+ S3 manifest 核验（completion）；确定性检查（行数/版本脚注）用代码不烧判断（免费模型优先铁律）。实验先行：`jev_fusion_experiments.py` 两轮（V1 证据构造缺陷→V2 修复），分离实证见 `logs/jev_fusion_exp_20260922_v2.json`；调用轨迹审计 `logs/jev_traj.jsonl`（只落 hash 与数值摘要）。开关：`PAI_JEV=0` env 硬关 > `config/jev.ini` enabled=0 > key 缺失，任何形态缺席=管线回退接线前行为。
- **知识来源 = 混沌 + 智库五渠道**：蒸馏原料不限于混沌新课——`E:\AI-Station\04 智库\` 下的一堂（创业五步法/AI实操）、万维钢调研方法论、微信读书（智能商业/调研方法等，EPC 工程书排除）、洞见研报 FDE 系列（智慧水利排除）、通往AGI之路（3396 md，waytoagi-sync 维护）全部纳入周度水位扫描（`automation/channel_state.json`）。排除渠道：`混沌学园/`（与 data/hundun/AI课程 394 文件完全同源）、混沌/调研框架库/internal（空）。.doc 老格式读不了（计数上报"待转格式"）；.docx 是 md 孪生件直接忽略；超大文件（md>1.5MB / pdf>15MB）不收。
- **claude 二进制**：npm 全局 shim 在本机 Win10 19045 报「不支持当前 Windows 版本」；实际可用的是 VSCode 扩展原生包 `~\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe`（认证共享，编排器按版本号自动择新）。
- **账号安全**：混沌凭据只经 `E:\AI-Station\config\hundun.secret.ini`（gitignored）由既有脚本读取；周级低频 + 0.2s 节流 + 缺口熔断（>40 门视为语料目录异常，中止待人工核查）。
- **只增不删**：蒸馏红线——不改写既有条目语义；语料本体（data/hundun）永不入仓库。
- **推送第三形态**：github.com receive-pack 经代理常死而 api.github.com 直连可用（gh 已登录，凭据在系统 keyring），`api_push.py` 走 blob→tree→commit→ref 快进推送。

## 首次部署清单

1. `register_weekly_task.ps1` 注册计划任务
2. 提交 automation/ 入库并推送
3. `run_now.cmd` 实跑一轮验证全链

### 安全约定（V5.1.2，两条管线共用 `pipeline_recovery.py`）
- 回滚绝不销毁：只还原"内容仍与管线写入时一致"的文件，其余（如运行期间你手改的文件）收进 `git stash`；不再整库 checkout / clean。
- 只提交 `.claude/skills/super-skill` 与 `.claude-plugin/plugin.json`，别处未提交的人工改动不会被无人值守地推上 GitHub。
- 每日蒸馏的模型在临时 git worktree 沙箱里运行，只读 GitHub；只有 `automation/daily_out/` 里的普通文件被拷回，沙箱用完即删，真实工作树碰不到。
- 只提交本轮写入且内容未被他人改过的文件；雷达扫描期间工作树有变动则本轮放弃。
- Windows 上管线进程被杀时，其子进程（claude / git / 测试）随 Job Object 一并结束。
- **另一台机器若有 SuperSkillWeekly 从另一个克隆运行：下次周日运行前务必先 `git pull` 那个克隆**，否则旧版 `api_push.py` 会把它的旧树推上去覆盖新版。
