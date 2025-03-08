@echo off
chcp 65001

:: 查找 Python 进程
for /f "tokens=2" %%i in ('tasklist ^| findstr "python.exe"') do (
    :: 终止进程
    taskkill /F /PID %%i
    echo 服务已停止
)

:: 如果没有找到进程
if %ERRORLEVEL% NEQ 0 (
    echo 未发现运行中的服务
)

pause
