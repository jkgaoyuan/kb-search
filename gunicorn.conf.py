import multiprocessing
import os
from app.config import get_settings

settings = get_settings()

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "kb_search"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"

# SSL (optional)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
