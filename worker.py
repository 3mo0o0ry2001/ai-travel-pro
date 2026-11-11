"""One worker per SQLite volume. Durable queue, bounded retries and a renewable lease."""

import argparse
import logging
import secrets
import signal
import smtplib
import time

from pydantic import ValidationError

from database import LimitExceeded, Store
from mailer import send_email
from models import SearchQuery
from settings import Settings
from tools import ProviderError, search_flights

logger = logging.getLogger("waypoint.worker")


def acquire_lease(store, owner):
    with store.connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS leases (name TEXT PRIMARY KEY, owner TEXT, expires_at INTEGER)"
        )
        conn.execute("BEGIN IMMEDIATE")
        lease = conn.execute("SELECT * FROM leases WHERE name='worker'").fetchone()
        if lease and lease["expires_at"] > time.time() and lease["owner"] != owner:
            return False
        conn.execute("INSERT OR REPLACE INTO leases VALUES ('worker',?,?)", (owner, int(time.time()) + 120))
    return True


def check_alert(alert, settings):
    store = Store(settings.database_path)
    now = int(time.time())
    try:
        query = SearchQuery.model_validate_json(alert["query"])
    except ValidationError:
        with store.connect() as conn:
            conn.execute(
                "UPDATE alerts SET active=0,last_error='Trip has expired or is invalid' WHERE id=?",
                (alert["id"],),
            )
        return
    try:
        flights = search_flights(query, settings)["flights"]
    except (ProviderError, LimitExceeded) as exc:
        with store.connect() as conn:
            conn.execute(
                "UPDATE alerts SET next_check=?,last_error=? WHERE id=?", (now + 3600, str(exc), alert["id"])
            )
        logger.warning("Alert check failed id=%s type=%s", alert["id"], type(exc).__name__)
        return
    cheapest = min((flight["price"] for flight in flights), default=None)
    with store.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT * FROM alerts WHERE id=? AND active=1", (alert["id"],)).fetchone()
        if not current:
            return
        if (
            cheapest is not None
            and cheapest <= alert["target_price"]
            and (current["last_price"] is None or cheapest < current["last_price"])
        ):
            subject = f"{'[DEMO] ' if settings.provider == 'demo' else ''}Price alert: {query.origin} to {query.destination}"
            body = (
                f"A fare of AED {cheapest:,.0f} for {query.adults} adult(s) was found for {query.departure}.\n"
                f"Open {settings.base_url}/ to search again. Prices can change; this is not a reservation.\n"
                "Manage or delete this alert in your Waypoint account."
            )
            dedupe = f"alert:{alert['id']}:{cheapest}:{now // settings.alert_interval}"
            conn.execute(
                "INSERT OR IGNORE INTO outbox(user_id,subject,body,dedupe,next_attempt) VALUES (?,?,?,?,?)",
                (alert["user_id"], subject, body, dedupe, now),
            )
        conn.execute(
            "UPDATE alerts SET next_check=?,last_price=?,last_checked=?,last_error=NULL WHERE id=?",
            (now + settings.alert_interval, cheapest, now, alert["id"]),
        )


def deliver_outbox(settings, owner):
    store = Store(settings.database_path)
    with store.connect() as conn:
        messages = conn.execute(
            "SELECT o.*,u.email FROM outbox o JOIN users u ON u.id=o.user_id "
            "WHERE sent_at IS NULL AND attempts<5 AND next_attempt<=? LIMIT 20",
            (int(time.time()),),
        ).fetchall()
    for message in messages:
        if not acquire_lease(store, owner):
            return
        store.heartbeat()
        try:
            send_email(dict(message), settings)
        except (smtplib.SMTPException, OSError) as exc:
            with store.connect() as conn:
                conn.execute(
                    "UPDATE outbox SET attempts=attempts+1,next_attempt=?,last_error=? WHERE id=?",
                    (
                        int(time.time()) + min(3600, 60 * 2 ** message["attempts"]),
                        type(exc).__name__,
                        message["id"],
                    ),
                )
            logger.warning("Mail delivery failed id=%s type=%s", message["id"], type(exc).__name__)
        else:
            with store.connect() as conn:
                conn.execute(
                    "UPDATE outbox SET sent_at=?,last_error=NULL WHERE id=?",
                    (int(time.time()), message["id"]),
                )


def run_cycle(settings, owner):
    store = Store(settings.database_path)
    if not acquire_lease(store, owner):
        logger.warning("Another worker owns the lease")
        return
    store.heartbeat()
    store.cleanup()
    for alert in store.due_alerts():
        if not acquire_lease(store, owner):
            return
        store.heartbeat()
        check_alert(alert, settings)
    deliver_outbox(settings, owner)
    store.heartbeat()


def main():
    parser = argparse.ArgumentParser(description="Waypoint price-alert and email worker")
    parser.add_argument("--once", action="store_true", help="Run a single batch")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = Settings.from_env()
    store = Store(settings.database_path)
    store.initialize()
    owner = secrets.token_hex(16)
    stopped = False

    def stop(signum, frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        while not stopped:
            run_cycle(settings, owner)
            if args.once:
                break
            for _ in range(15):
                if stopped:
                    break
                time.sleep(1)
    finally:
        with store.connect() as conn:
            conn.execute("DELETE FROM leases WHERE name='worker' AND owner=?", (owner,))


if __name__ == "__main__":
    main()
