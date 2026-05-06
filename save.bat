@echo off
git add -A
git commit -m "备份 %date% %time%"
if %errorlevel% neq 0 echo 备份失败，检查 Git 仓库
pause
