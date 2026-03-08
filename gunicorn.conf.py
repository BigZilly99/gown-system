# Gunicorn configuration for UniGown Pro
# Optimized for low CPU / limited resources

import multiprocessing
import os

# Bind to all interfaces
bind = "0.0.0.0:8000"

# Worker configuration - use gthread for better I/O handling on low CPU
# Formula: 2-4 workers for low CPU, more threads per worker
workers = int(os.environ.get('GUNICORN_WORKERS', 2))
threads = int(os.environ.get('GUNICORN_THREADS', 4))

# Worker class - gthread is best for I/O bound apps on limited CPU
worker_class = 'gthread'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Worker timeout - 30 seconds is plenty for simple queries
timeout = 30
graceful_timeout = 30

# Keep-alive for connection reuse
keepalive = 2

# Max requests per worker - helps with memory leaks
max_requests = 1000
max_requests_jitter = 50

# Preload app for faster worker startup and shared memory
preload_app = True

# Worker lifecycle hooks for database connection management
def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    pass

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    # Close database connections in child process
    pass

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    pass

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    pass

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    pass

def pre_exec(server):
    """Called just before a new master process is forked."""
    pass

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug("%s %s" % (req.method, req.path))

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    pass

def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass
