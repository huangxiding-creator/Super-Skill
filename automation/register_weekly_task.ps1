# Super-Skill 周度自升级计划任务注册（幂等，可重复运行）
# 时间：每周日 22:00（北京时间 = 本机 China Standard Time）
# 静默：pythonw.exe 直跑无控制台，子进程全部 CREATE_NO_WINDOW
# 补跑：错过触发点（关机/未登录）开机后自动补跑（StartWhenAvailable）
# 暂停：新建同目录 PAUSE 文件即整轮跳过（免提权），删除即恢复
$ErrorActionPreference = "Stop"

$pyw     = "E:\AI-Station\.venv\Scripts\pythonw.exe"
$script  = "E:\AI-Station\07 任务\Super-Skill\automation\superskill_weekly.py"

if (-not (Test-Path $pyw)) { throw "pythonw 不存在: $pyw" }

$action   = New-ScheduledTaskAction -Execute $pyw -Argument "`"$script`""
$trigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "22:00"
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "SuperSkillWeekly" `
    -Description "Super-Skill 周度自升级：子技能更新 + 混沌新课蒸馏融合 + 全局安装 + GitHub 推送 + 企微通知" `
    -Action $action -Trigger $trigger -Settings $settings -Force

Write-Host "已注册 SuperSkillWeekly（每周日 22:00）"
schtasks /Query /TN "SuperSkillWeekly" /V /FO LIST | Select-String "任务名|状态|下次运行|Task Name|Status|Next Run"
