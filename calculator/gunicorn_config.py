import multiprocessing
import os

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 工作进程数，推荐为 CPU 核心数的 2-4 倍
workers = multiprocessing.cpu_count() * 2
# 绑定端口
bind = '127.0.0.1:8090'
# 工作模式
worker_class = 'sync'
# 最大请求数
max_requests = 2000
# 超时时间
timeout = 120
# 日志级别
loglevel = 'info'
# 错误日志
errorlog = os.path.join(log_dir, 'gunicorn_error.log')
# 访问日志
accesslog = os.path.join(log_dir, 'gunicorn_access.log')
