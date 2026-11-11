from datetime import timedelta
from unittest.mock import patch

import httpx
import pytest
from pydantic import ValidationError

from database import LimitExceeded
from models import SearchQuery, today_uae
from tools import ProviderError, fetch_live, parse_offers, search_flights


def raw_offer(price=1000, code="MS", stops=0):
    segment = {
        "airline": "Example Air",
        "flight_number": f"{code} 123",
        "departure_airport": {"id": "DXB", "time": "2026-11-10 10:00"},
        "arrival_airport": {"id": "CAI", "time": "2026-11-10 13:00"},
    }
    return {"price": price, "total_duration": 240, "flights": [segment.copy() for _ in range(stops + 1)]}


@pytest.mark.parametrize(
    "change",
    [
        {"departure": (today_uae() - timedelta(days=1)).isoformat()},
        {"departure": (today_uae() + timedelta(days=331)).isoformat()},
        {"destination": "DXB"},
        {"budget": 0},
        {"origin": "Dubai"},
        {"adults": 7},
    ],
)
def test_invalid_trip_cannot_reach_provider(query, change):
    with pytest.raises(ValidationError):
        SearchQuery.model_validate(query.model_dump(mode="json") | change)


@pytest.mark.parametrize(
    "payload",
    [{"error": "Invalid API key"}, {"best_flights": None}, {"other_flights": [raw_offer(price=-1)]}],
)
def test_provider_errors_are_not_reported_as_no_flights(query, live_settings, payload):
    response = httpx.Response(
        200, json=payload, request=httpx.Request("GET", "https://serpapi.com/search.json")
    )
    with patch.object(httpx.Client, "get", return_value=response), pytest.raises(ProviderError):
        fetch_live(query, live_settings)


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_failures_are_safe_and_do_not_expose_api_key(query, live_settings, status):
    response = httpx.Response(
        status,
        json={"error": "secret"},
        request=httpx.Request("GET", "https://serpapi.com/?api_key=test-provider-secret"),
    )
    with patch.object(httpx.Client, "get", return_value=response), pytest.raises(ProviderError) as failure:
        fetch_live(query, live_settings)
    assert "test-provider-secret" not in str(failure.value)


def test_network_timeout_is_a_service_failure(query, live_settings):
    with (
        patch.object(httpx.Client, "get", side_effect=httpx.ReadTimeout("provider stalled")),
        pytest.raises(ProviderError),
    ):
        fetch_live(query, live_settings)


def test_direct_filter_uses_provider_nonstop_value_and_filters_results(query, live_settings, store):
    request_parameters = []

    def provider_response(self, url, **kwargs):
        request_parameters.append(kwargs["params"])
        return httpx.Response(
            200,
            json={"best_flights": [raw_offer(1100, "MS", 0), raw_offer(800, "QR", 1)]},
            request=httpx.Request("GET", url),
        )

    query = SearchQuery.model_validate(query.model_dump() | {"direct": True})
    with patch.object(httpx.Client, "get", provider_response):
        response = search_flights(query, live_settings)
    assert request_parameters[0]["stops"] == 1  # Regression: old UI used 0, which permits all stops.
    assert [flight["price"] for flight in response["flights"]] == [1100]


def test_search_combines_groups_deduplicates_and_applies_budget_and_airline(query, live_settings, store):
    query = SearchQuery.model_validate(query.model_dump() | {"budget": 1200, "airline": "MS"})
    payload = {
        "best_flights": [raw_offer(1100), raw_offer(1100)],
        "other_flights": [raw_offer(1000, "QR"), raw_offer(1500)],
    }
    response = httpx.Response(
        200, json=payload, request=httpx.Request("GET", "https://serpapi.com/search.json")
    )
    with patch.object(httpx.Client, "get", return_value=response):
        flights = search_flights(query, live_settings)["flights"]
    assert len(flights) == 1
    assert flights[0]["price"] == 1100
    assert flights[0]["segments"][0]["flight_number"] == "MS 123"


def test_identical_search_reuses_cache_without_another_provider_charge(query, live_settings, store):
    response = httpx.Response(
        200,
        json={"best_flights": [raw_offer()]},
        request=httpx.Request("GET", "https://serpapi.com/search.json"),
    )
    with patch.object(httpx.Client, "get", return_value=response):
        first = search_flights(query, live_settings)
    with patch.object(httpx.Client, "get", side_effect=AssertionError("Unexpected paid request")):
        second = search_flights(query, live_settings)
    assert second["flights"] == first["flights"] and second["cached"]


def test_global_provider_budget_stops_paid_requests(query, live_settings, store):
    from dataclasses import replace

    settings = replace(live_settings, daily_provider_limit=1)
    response = httpx.Response(200, json={}, request=httpx.Request("GET", "https://serpapi.com/search.json"))
    with patch.object(httpx.Client, "get", return_value=response):
        search_flights(query, settings)
        changed = SearchQuery.model_validate(query.model_dump() | {"origin": "AUH"})
        with pytest.raises(LimitExceeded):
            search_flights(changed, settings)


def test_unauthenticated_search_cannot_spend_provider_credits(client, query):
    assert client.post("/api/search", json=query.model_dump(mode="json")).status_code == 401


def test_demo_search_is_explicit_and_does_not_offer_booking(signed_in, query):
    response = signed_in.post("/api/search", json=query.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["demo"]
    assert response.json()["flights"]
    assert "booking_url" not in response.json()


def test_valid_empty_provider_result_stays_empty():
    assert parse_offers({}) == []
