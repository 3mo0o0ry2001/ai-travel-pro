import json
import re
import time

import pytest
from conftest import register_and_login, verify_email
from fastapi.testclient import TestClient

from app import create_app
from worker import run_cycle


def test_registration_stores_hashes_and_verification_token_is_single_use(client, settings, store):
    credentials = register_and_login(client)
    user = store.user_by_email(credentials["email"])
    assert credentials["password"] not in user["password_hash"]
    token = verify_email(client, settings)
    assert client.get("/api/session").json()["user"]["verified"] == 1
    assert client.post("/api/auth/verify", json={"token": token}).status_code == 400
    with store.connect() as conn:
        assert conn.execute("SELECT count(*) FROM tokens").fetchone()[0] == 0


def test_duplicate_registration_and_unknown_reset_do_not_disclose_account(client):
    credentials = register_and_login(client)
    duplicate = client.post("/api/auth/register", json=credentials)
    new = client.post("/api/auth/register", json=credentials | {"email": "other@example.com"})
    assert duplicate.json() == new.json()
    known = client.post("/api/auth/forgot", json={"email": credentials["email"]})
    unknown = client.post("/api/auth/forgot", json={"email": "missing@example.com"})
    assert known.json() == unknown.json()


def test_password_reset_revokes_sessions_and_rejects_old_password(signed_in, settings):
    signed_in.post("/api/auth/forgot", json={"email": "traveller@example.com"})
    run_cycle(settings, "test-worker")
    messages = [
        json.loads(line)
        for line in (settings.database_path.parent / "dev-mail.jsonl").read_text().splitlines()
    ]
    token = re.search(r"reset=([\w-]+)", messages[-1]["body"])[1]
    response = signed_in.post(
        "/api/auth/reset", json={"token": token, "password": "new-password-long-enough"}
    )
    assert response.status_code == 200
    assert signed_in.get("/api/alerts").status_code == 401
    assert (
        signed_in.post(
            "/api/auth/login",
            json={"email": "traveller@example.com", "password": "correct-horse-battery-2026"},
        ).status_code
        == 401
    )
    assert (
        signed_in.post(
            "/api/auth/login", json={"email": "traveller@example.com", "password": "new-password-long-enough"}
        ).status_code
        == 200
    )
    assert (
        signed_in.post(
            "/api/auth/reset", json={"token": token, "password": "another-long-password"}
        ).status_code
        == 400
    )


def test_expired_verification_does_not_verify_user(signed_in, settings, store):
    run_cycle(settings, "test-worker")
    token = re.search(r"verify=([\w-]+)", (settings.database_path.parent / "dev-mail.jsonl").read_text())[1]
    with store.connect() as conn:
        conn.execute("UPDATE tokens SET expires_at=?", (int(time.time()) - 1,))
    assert signed_in.post("/api/auth/verify", json={"token": token}).status_code == 400
    assert not signed_in.get("/api/session").json()["user"]["verified"]


def test_csrf_and_cross_origin_requests_cannot_create_accounts(client):
    credentials = {"email": "blocked@example.com", "password": "a-valid-long-password"}
    assert (
        client.post("/api/auth/register", json=credentials, headers={"X-CSRF-Token": ""}).status_code == 403
    )
    assert (
        client.post(
            "/api/auth/register", json=credentials, headers={"Origin": "https://attacker.example"}
        ).status_code
        == 403
    )
    assert client.post("/api/auth/register", content="x" * 16385).status_code == 413


def test_users_cannot_read_or_delete_another_users_alerts(verified, settings, query):
    assert (
        verified.post(
            "/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1000}
        ).status_code
        == 201
    )
    alert_id = verified.get("/api/alerts").json()["alerts"][0]["id"]
    with TestClient(create_app(settings)) as other:
        other.headers["X-CSRF-Token"] = other.get("/api/session").json()["csrf"]
        register_and_login(other, "someone@example.com")
        assert other.get("/api/alerts").json() == {"alerts": []}
        assert other.delete(f"/api/alerts/{alert_id}").status_code == 404
    assert len(verified.get("/api/alerts").json()["alerts"]) == 1


def test_account_deletion_removes_tokens_sessions_alerts_and_mail(verified, store, query):
    verified.post("/api/alerts", json={"query": query.model_dump(mode="json"), "target_price": 1200})
    assert verified.delete("/api/account").status_code == 200
    assert verified.get("/api/alerts").status_code == 401
    with store.connect() as conn:
        for table in ("users", "sessions", "tokens", "alerts", "outbox"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_login_abuse_is_limited_without_leaking_credentials(client):
    credentials = {"email": "missing@example.com", "password": "a-valid-long-password"}
    for _ in range(10):
        assert client.post("/api/auth/login", json=credentials).status_code == 401
    response = client.post("/api/auth/login", json=credentials)
    assert response.status_code == 429
    assert credentials["password"] not in response.text


def test_invalid_credentials_do_not_echo_password_in_error(client):
    response = client.post("/api/auth/register", json={"email": "invalid", "password": "short-secret"})
    assert response.status_code == 422
    assert "short-secret" not in response.text


@pytest.mark.parametrize("password", ["a" * 11, "a" * 129, "😀" * 6])
def test_registration_rejects_password_outside_policy_without_creating_account(client, store, password):
    response = client.post("/api/auth/register", json={"email": "boundary@example.com", "password": password})
    assert response.status_code == 422
    assert store.user_by_email("boundary@example.com") is None
    assert password not in response.text


@pytest.mark.parametrize("password", ["a" * 12, "a" * 128, "رحلة" * 3])
def test_password_policy_boundaries_allow_signup_and_login(client, password):
    credentials = {"email": "boundary@example.com", "password": password}
    assert client.post("/api/auth/register", json=credentials).status_code == 202
    assert client.post("/api/auth/login", json=credentials).status_code == 200
    assert client.get("/api/session").json()["user"]["email"] == credentials["email"]
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/session").json()["user"] is None
