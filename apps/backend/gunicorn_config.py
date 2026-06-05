"""Gunicorn configuration for production deployment."""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "sapisehat-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed, configure in production)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Application
raw_env = ["PYTHONUNBUFFERED=1"]

# Hooks
def on_starting(server):
    print("Gunicorn server starting...")

def on_exit(server):
    print("Gunicorn server exiting...")
