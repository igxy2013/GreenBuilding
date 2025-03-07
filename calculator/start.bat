@echo off
chcp 65001
:: 激活虚拟环境
call venv\Scripts\activate

:: 启动应用（不要直接运行此文件，请运行 run.vbs）
python app.py
