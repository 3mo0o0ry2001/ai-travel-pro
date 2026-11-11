from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app import create_app
from settings import Settings


@pytest.fixture
def production(settings):
    return replace(
        settings,
        environment="production",
        provider="live",
        base_url="https://travel.example.com",
        serp_api_key="configured-test-key",
        smtp_host="smtp.example.com",
        mail_from="noreply@example.com",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"provider": "demo"},
        {"secret": "short"},
        {"serp_api_key": ""},
        {"base_url": "http://travel.example.com"},
        {"smtp_host": ""},
    ],
)
def test_unsafe_production_configuration_refuses_startup(production, change):
    with pytest.raises(ValueError):
        replace(production, **change).validate()


def test_production_cookies_headers_and_host_boundary(production):
    with TestClient(create_app(production), base_url=production.base_url) as client:
        response = client.get("/api/session")
        cookie = response.headers["set-cookie"]
        assert "__Host-waypoint_csrf=" in cookie and "Secure" in cookie and "HttpOnly" in cookie
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
        assert response.headers["Cache-Control"] == "no-store"
        assert "max-age=" in response.headers["Strict-Transport-Security"]
        assert client.get("/", headers={"Host": "evil.example.com"}).status_code == 400


def test_missing_production_secret_is_not_generated_silently(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SECRET", "")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_readiness_reports_missing_worker_and_email(client):
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert not response.json()["checks"]["worker"]
    assert not response.json()["checks"]["mail"]
