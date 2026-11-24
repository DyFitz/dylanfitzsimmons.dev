import os
from pathlib import Path

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))

# Keep worker heartbeat files in memory rather than on the container's disk.
worker_tmp_dir = "/dev/shm" if Path("/dev/shm").is_dir() else None

# Log to stdout and stderr.
accesslog = "-"
errorlog = "-"
