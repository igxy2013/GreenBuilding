@echo off
cd /d D:\PY\calculator
set PYTHONPATH=D:\PY\calculator
D:\PY\calculator\venv\Scripts\gunicorn.exe -c gunicorn_config.py app:app
