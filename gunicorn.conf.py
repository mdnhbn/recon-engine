"""Keep the web app responsive while network lookups are in flight."""
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "5000")
workers = 1
worker_class = "gthread"
threads = 4
timeout = 120
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
