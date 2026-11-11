import os
import sqlite3
import time

with sqlite3.connect(os.environ.get("DATABASE_PATH", "data/travel.db"), timeout=3) as conn:
    heartbeat = conn.execute("SELECT value FROM runtime WHERE key='worker'").fetchone()
    raise SystemExit(0 if heartbeat and heartbeat[0] > time.time() - 180 else 1)
