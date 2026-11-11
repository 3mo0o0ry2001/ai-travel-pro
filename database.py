import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from security import digest_token

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 verified INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS tokens (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 purpose TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS counters (
 bucket TEXT PRIMARY KEY, count INTEGER NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS cache (
 key TEXT PRIMARY KEY, payload TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS alerts (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 query TEXT NOT NULL, target_price INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1,
 next_check INTEGER NOT NULL, last_price INTEGER, last_checked INTEGER, last_error TEXT,
 UNIQUE(user_id, query, target_price));
CREATE INDEX IF NOT EXISTS alerts_due ON alerts(active, next_check);
CREATE INDEX IF NOT EXISTS alerts_owner ON alerts(user_id);
CREATE TABLE IF NOT EXISTS outbox (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 subject TEXT NOT NULL, body TEXT NOT NULL, dedupe TEXT UNIQUE NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt INTEGER NOT NULL,
 sent_at INTEGER, last_error TEXT);
CREATE TABLE IF NOT EXISTS runtime (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
"""


class LimitExceeded(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)
            if conn.execute("SELECT max(version) FROM schema_version").fetchone()[0] != 1:
                raise RuntimeError("Unsupported database schema")

    def user_by_email(self, email):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()

    def create_user(self, email, password_hash):
        with self.connect() as conn:
            return conn.execute(
                "INSERT INTO users(email,password_hash,created_at) VALUES (?,?,?)",
                (email.lower(), password_hash, int(time.time())),
            ).lastrowid

    def new_session(self, user_id):
        token = secrets.token_urlsafe(32)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sessions VALUES (?,?,?)",
                (digest_token(token), user_id, int(time.time()) + 86400),
            )
        return token

    def session_user(self, token):
        with self.connect() as conn:
            return conn.execute(
                "SELECT u.id,u.email,u.verified FROM users u JOIN sessions s ON s.user_id=u.id "
                "WHERE s.token_hash=? AND s.expires_at>?",
                (digest_token(token), int(time.time())),
            ).fetchone()

    def delete_session(self, token):
        with self.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (digest_token(token),))

    def delete_user(self, user_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))

    def issue_email(self, user_id, purpose, base_url):
        token = secrets.token_urlsafe(32)
        subject = "Verify your Waypoint email" if purpose == "verify" else "Reset your Waypoint password"
        body = f"{subject}\n\n{base_url}/?{purpose}={token}\n\nThis link expires in one hour. Ignore it if you did not request it."
        with self.connect() as conn:
            conn.execute("DELETE FROM tokens WHERE user_id=? AND purpose=?", (user_id, purpose))
            conn.execute(
                "INSERT INTO tokens VALUES (?,?,?,?)",
                (digest_token(token), user_id, purpose, int(time.time()) + 3600),
            )
            conn.execute(
                "INSERT INTO outbox(user_id,subject,body,dedupe,next_attempt) VALUES (?,?,?,?,?)",
                (user_id, subject, body, digest_token(token), int(time.time())),
            )

    def consume_token(self, token, purpose, password_hash=None):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            record = conn.execute(
                "SELECT * FROM tokens WHERE token_hash=? AND purpose=? AND expires_at>?",
                (digest_token(token), purpose, int(time.time())),
            ).fetchone()
            if not record:
                return False
            if purpose == "verify":
                conn.execute("UPDATE users SET verified=1 WHERE id=?", (record["user_id"],))
            else:
                conn.execute(
                    "UPDATE users SET password_hash=? WHERE id=?", (password_hash, record["user_id"])
                )
                conn.execute("DELETE FROM sessions WHERE user_id=?", (record["user_id"],))
            conn.execute("DELETE FROM tokens WHERE token_hash=?", (digest_token(token),))
        return True

    def limit(self, bucket, maximum, seconds):
        now = int(time.time())
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM counters WHERE expires_at<=?", (now,))
            record = conn.execute("SELECT count FROM counters WHERE bucket=?", (bucket,)).fetchone()
            if record and record[0] >= maximum:
                raise LimitExceeded("Request limit reached. Please try again later.")
            conn.execute(
                "INSERT INTO counters VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=count+1",
                (bucket, now + seconds),
            )

    def cached(self, key):
        with self.connect() as conn:
            record = conn.execute(
                "SELECT payload FROM cache WHERE key=? AND expires_at>?", (key, int(time.time()))
            ).fetchone()
            return json.loads(record[0]) if record else None

    def cache(self, key, payload):
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache VALUES (?,?,?)",
                (key, json.dumps(payload), int(time.time()) + 600),
            )

    def add_alert(self, user_id, alert):
        query = alert.query.model_dump_json()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            count = conn.execute(
                "SELECT count(*) FROM alerts WHERE user_id=? AND active=1", (user_id,)
            ).fetchone()[0]
            if count >= 3:
                raise LimitExceeded("You can keep up to three active alerts.")
            conn.execute(
                "INSERT INTO alerts(user_id,query,target_price,next_check) VALUES (?,?,?,?) "
                "ON CONFLICT(user_id,query,target_price) DO UPDATE SET active=1,next_check=excluded.next_check",
                (user_id, query, alert.target_price, int(time.time())),
            )

    def user_alerts(self, user_id):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE user_id=? ORDER BY id DESC", (user_id,)
            ).fetchall()
            return [dict(row) | {"query": json.loads(row["query"])} for row in rows]

    def remove_alert(self, user_id, alert_id):
        with self.connect() as conn:
            return conn.execute("DELETE FROM alerts WHERE id=? AND user_id=?", (alert_id, user_id)).rowcount

    def due_alerts(self):
        with self.connect() as conn:
            return conn.execute(
                "SELECT a.*,u.email FROM alerts a JOIN users u ON u.id=a.user_id "
                "WHERE a.active=1 AND u.verified=1 AND a.next_check<=? LIMIT 50",
                (int(time.time()),),
            ).fetchall()

    def heartbeat(self):
        with self.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO runtime VALUES ('worker',?)", (int(time.time()),))

    def worker_alive(self):
        with self.connect() as conn:
            record = conn.execute("SELECT value FROM runtime WHERE key='worker'").fetchone()
            return bool(record and record[0] > time.time() - 180)

    def cleanup(self):
        now = int(time.time())
        with self.connect() as conn:
            for table in ("sessions", "tokens", "counters", "cache"):
                conn.execute(f"DELETE FROM {table} WHERE expires_at<=?", (now,))
            conn.execute("DELETE FROM outbox WHERE sent_at<?", (now - 7 * 86400,))
