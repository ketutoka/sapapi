# Production Configuration for SAP API Flask Application
# gunicorn.conf.py - Gunicorn WSGI server configuration

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Optimal for CPU-bound apps
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeout
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/var/log/sapapi/access.log"
errorlog = "/var/log/sapapi/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "sapapi"

# Server mechanics
daemon = False
pidfile = "/var/run/sapapi/sapapi.pid"
tmp_upload_dir = None

# SSL (uncomment if using HTTPS directly through Gunicorn)
# keyfile = "/etc/ssl/private/sapapi.key"
# certfile = "/etc/ssl/certs/sapapi.crt"

# Worker process lifecycle
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("SAP API server is ready. Listening on: %s", server.address)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info("Worker exited (pid: %s)", worker.pid)