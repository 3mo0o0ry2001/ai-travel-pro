import json
import re
from dataclasses import replace
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app import create_app
from database import Store
from models import SearchQuery, today_uae
from settings import Settings
from worker import run_cycle


@pytest.fixture
def settings(tmp_path):
    return Settings(
        environment="test",
        provider="demo",
        database_path=tmp_path / "travel.db",
        secret="test-only-secret-32-characters-long",
    )


@pytest.fixture
def store(settings):
    database = Store(settings.database_path)
    database.initialize()
    return database


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        session = test_client.get("/api/session").json()
        test_client.headers["X-CSRF-Token"] = session["csrf"]
        yield test_client


@pytest.fixture
def query():
    return SearchQuery(origin="DXB", destination="CAI", departure=today_uae() + timedelta(days=14))


def register_and_login(client, email="traveller@example.com"):
    credentials = {"email": email, "password": "correct-horse-battery-2026"}
    assert client.post("/api/auth/register", json=credentials).status_code == 202
    assert client.post("/api/auth/login", json=credentials).status_code == 200
    return credentials


def verify_email(client, settings):
    run_cycle(settings, "test-worker")
    messages = [
        json.loads(line)
        for line in (settings.database_path.parent / "dev-mail.jsonl").read_text().splitlines()
    ]
    link = next(message["body"] for message in reversed(messages) if "?verify=" in message["body"])
    token = re.search(r"verify=([\w-]+)", link)[1]
    assert client.post("/api/auth/verify", json={"token": token}).status_code == 200
    return token


@pytest.fixture
def signed_in(client):
    register_and_login(client)
    return client


@pytest.fixture
def verified(signed_in, settings):
    verify_email(signed_in, settings)
    return signed_in


@pytest.fixture
def live_settings(settings):
    return replace(settings, provider="live", serp_api_key="test-provider-secret")
