"""
Gunicorn configuration file for CRM Maroc
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/opt/app/logs/gunicorn_access.log"
errorlog = "/opt/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "crm-maroc"

# Server mechanics
daemon = False
pidfile = "/opt/app/gunicorn.pid"
user = "master"
group = "master"
tmp_upload_dir = None

# SSL (uncomment for HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Server hooks
def on_starting(server):
    server.log.info("Starting CRM Maroc Gunicorn server")

def on_reload(server):
    server.log.info("Reloading CRM Maroc Gunicorn server")

def on_exit(server):
    server.log.info("Stopping CRM Maroc Gunicorn server")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)

def nworkers_changed(server, new_value, old_value):
    server.log.info("Number of workers changed from %s to %s", old_value, new_value)

def on_exit(server):
    server.log.info("Server is shutting down")
