import json
import smtplib
import time
from datetime import timedelta
from unittest.mock import patch

from models import today_uae
from worker import acquire_lease, run_cycle


def test_unverified_email_cannot_receive_price_alerts(signed_in, query):
    response = signed_in.post(
        "/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1500}
    )
    assert response.status_code == 403
    assert signed_in.get("/api/alerts").json()["alerts"] == []


def test_worker_queues_and_delivers_matching_fare_once(verified, settings, store, query):
    assert (
        verified.post(
            "/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1100}
        ).status_code
        == 201
    )
    run_cycle(settings, "test-worker")
    with store.connect() as conn:
        alert = conn.execute("SELECT * FROM alerts").fetchone()
        assert alert["last_price"] == 980
        assert alert["next_check"] > time.time()
        assert (
            conn.execute(
                "SELECT count(*) FROM outbox WHERE subject LIKE '%Price alert%' AND sent_at IS NOT NULL"
            ).fetchone()[0]
            == 1
        )
        conn.execute("UPDATE alerts SET next_check=0")
    run_cycle(settings, "test-worker")
    messages = [
        json.loads(line)
        for line in (settings.database_path.parent / "dev-mail.jsonl").read_text().splitlines()
    ]
    assert len([message for message in messages if "Price alert" in message["subject"]]) == 1


def test_failed_email_is_retryable_and_never_marked_delivered(verified, settings, store, query):
    verified.post("/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1100})
    from dataclasses import replace

    smtp_settings = replace(settings, smtp_host="mail.example.com", mail_from="noreply@example.com")
    with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("service offline")):
        run_cycle(smtp_settings, "test-worker")
    with store.connect() as conn:
        message = conn.execute("SELECT * FROM outbox WHERE subject LIKE '%Price alert%'").fetchone()
        assert message["sent_at"] is None and message["attempts"] == 1
        assert message["next_attempt"] > time.time()


def test_expired_trip_is_deactivated_without_search(verified, settings, store, query):
    verified.post("/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1100})
    expired = query.model_dump(mode="json") | {"departure": (today_uae() - timedelta(days=1)).isoformat()}
    with store.connect() as conn:
        conn.execute("UPDATE alerts SET query=?", (json.dumps(expired),))
    run_cycle(settings, "test-worker")
    assert verified.get("/api/alerts").json()["alerts"][0]["active"] == 0


def test_worker_lease_prevents_two_workers_sending_same_batch(store):
    assert acquire_lease(store, "worker-one")
    assert not acquire_lease(store, "worker-two")
    with store.connect() as conn:
        conn.execute("UPDATE leases SET expires_at=0")
    assert acquire_lease(store, "worker-two")


def test_alert_limit_is_enforced_per_account(verified, query):
    for price in (800, 900, 1000):
        assert (
            verified.post(
                "/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": price}
            ).status_code
            == 201
        )
    assert (
        verified.post(
            "/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1100}
        ).status_code
        == 429
    )
