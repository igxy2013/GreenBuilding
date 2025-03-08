@echo off
chcp 65001
:: 激活虚拟环境
call venv\Scripts\activate

:: 启动应用并记录进程ID
python app.py > nul 2>&1 & echo %ERRORLEVEL% > pid.txt
