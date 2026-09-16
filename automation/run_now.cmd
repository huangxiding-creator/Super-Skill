@echo off
rem Super-Skill 周度自升级——前台手动运行（看全程输出；计划任务用 pythonw 静默跑）
chcp 65001 >nul
"E:\AI-Station\.venv\Scripts\python.exe" "E:\AI-Station\07 任务\Super-Skill\automation\superskill_weekly.py" %*
pause
