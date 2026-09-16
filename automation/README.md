# Super-Skill 周度自升级（automation/）

每周日 22:00（北京时间）无人值守执行一轮：**子技能更新 → 混沌新课蒸馏融合 → 全局安装 → GitHub 推送 → 企微通知**。

## 注册 / 查看计划任务

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\AI-Station\07 任务\Super-Skill\automation\register_weekly_task.ps1"
schtasks /Query /TN "SuperSkillWeekly" /V /FO LIST
```

- 静默执行：`pythonw.exe` 无控制台，全部子进程 `CREATE_NO_WINDOW`
- 错过补跑：关机/未登录错过 22:00 → 开机自动补跑（StartWhenAvailable）
- 并发保护：`MultipleInstances IgnoreNew` + 文件锁（陈锁 8h 自动破除）

## 六段流水线

| 段 | 内容 | 失败策略 |
|----|------|----------|
| S1 | `npx skills update -g`（注册表技能）+ 48 内嵌子技能结构审计（frontmatter/name/≤500行） | best-effort，不挡管线 |
| S2 | `hundun_census.py` 刷新 → **缺口 >40 门熔断** → `hundun_batch.py` 幂等增量（0.2s 节流 / 403 自动重登）→ 圈出本周 AI 新课 | 隔离失败（主链继续） |
| S3 | 无头 claude 蒸馏新课 → 四类资产归档 → 对账去重 → **暂存协议**（成品全文写 `automation/distill_out/` + manifest.json，编排器校验白名单后代落 `.claude/skills/super-skill/`——`.claude/**` 是权限敏感路径，LLM 直写必被拒，由确定性层执行写入）+ SKILL.md 接线 + CHANGELOG + 版本 bump；**干净工作树闸门**防混入人工改动 | 失败/无增量/声明与暂存不符 → `git checkout` 回滚 |
| S4 | robocopy 镜像 `.claude/skills/super-skill` → `%USERPROFILE%\.claude\skills\super-skill` | 失败即整体 ❌ |
| S5 | 提交 → 三层推送回退：`git push` → 剥代理重推 → `api_push.py`（gh api 数据通道，仅快进） | 全败保留本地提交，企微告警 |
| S6 | `tools/notify_wecom.py` 摘要（成功/失败均发） | best-effort |

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

- **claude 二进制**：npm 全局 shim 在本机 Win10 19045 报「不支持当前 Windows 版本」；实际可用的是 VSCode 扩展原生包 `~\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe`（认证共享，编排器按版本号自动择新）。
- **账号安全**：混沌凭据只经 `E:\AI-Station\config\hundun.secret.ini`（gitignored）由既有脚本读取；周级低频 + 0.2s 节流 + 缺口熔断（>40 门视为语料目录异常，中止待人工核查）。
- **只增不删**：蒸馏红线——不改写既有条目语义；语料本体（data/hundun）永不入仓库。
- **推送第三形态**：github.com receive-pack 经代理常死而 api.github.com 直连可用（gh 已登录，凭据在系统 keyring），`api_push.py` 走 blob→tree→commit→ref 快进推送。

## 首次部署清单

1. `register_weekly_task.ps1` 注册计划任务
2. 提交 automation/ 入库并推送
3. `run_now.cmd` 实跑一轮验证全链
