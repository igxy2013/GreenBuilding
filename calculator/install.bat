@echo off
chcp 65001
echo 正在创建虚拟环境...
python -m venv venv

:: 激活虚拟环境
call venv\Scripts\activate

:: 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt

:: 创建必要的目录
mkdir static 2>nul
mkdir templates 2>nul

echo 安装完成！
echo 请运行 start.bat 启动应用
pause
