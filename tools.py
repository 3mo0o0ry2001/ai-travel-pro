"""Flight data boundary. A provider failure is never an empty search result."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from database import Store

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


def onward_url(query):
    phrase = (
        f"Flights from {query.origin} to {query.destination} on {query.departure} for {query.adults} adults"
    )
    return "https://www.google.com/travel/flights?" + urlencode({"q": phrase, "curr": "AED"})


def normalize_offer(offer):
    segments = offer["flights"]
    if not segments:
        raise ValueError("Flight has no segments")
    price, duration = float(offer["price"]), int(offer["total_duration"])
    if not 0 < price < 1000000 or duration <= 0:
        raise ValueError("Invalid flight price or duration")
    normalized = [
        {
            "airline": segment["airline"],
            "flight_number": segment.get("flight_number", ""),
            "origin": segment["departure_airport"]["id"],
            "destination": segment["arrival_airport"]["id"],
            "departure": segment["departure_airport"]["time"],
            "arrival": segment["arrival_airport"]["time"],
        }
        for segment in segments
    ]
    fingerprint = json.dumps(normalized, sort_keys=True)
    return {
        "id": hashlib.sha256(fingerprint.encode()).hexdigest()[:20],
        "price": price,
        "currency": "AED",
        "duration": duration,
        "stops": len(segments) - 1,
        "segments": normalized,
    }


def provider_parameters(query, api_key):
    return {
        "engine": "google_flights",
        "type": 2,
        "departure_id": query.origin,
        "arrival_id": query.destination,
        "outbound_date": query.departure.isoformat(),
        "currency": "AED",
        "adults": query.adults,
        "stops": 1 if query.direct else 0,
        "travel_class": {"economy": 1, "premium": 2, "business": 3, "first": 4}[query.cabin],
        "include_airlines": query.airline or None,
        "max_price": query.budget,
        "api_key": api_key,
    }


def fetch_live(query, settings):
    if not settings.serp_api_key:
        raise ProviderError("Live flight search is not configured. Contact the site operator.")
    try:
        with httpx.Client(timeout=httpx.Timeout(20, connect=5), follow_redirects=False) as client:
            response = client.get(
                "https://serpapi.com/search.json", params=provider_parameters(query, settings.serp_api_key)
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Flight provider failed: %s", type(exc).__name__)
        raise ProviderError("Flight search is temporarily unavailable. Please try again later.") from None
    if not isinstance(payload, dict) or payload.get("error"):
        raise ProviderError("The flight provider could not complete this search. Please try again later.")
    return parse_offers(payload)


def parse_offers(payload):
    offers = []
    best, other = payload.get("best_flights", []), payload.get("other_flights", [])
    if not isinstance(best, list) or not isinstance(other, list):
        raise ProviderError("The flight provider returned an invalid response.")
    raw_offers = best + other
    for offer in raw_offers:
        try:
            offers.append(normalize_offer(offer))
        except (KeyError, TypeError, ValueError, OverflowError):
            logger.warning("Flight provider returned a malformed offer")
    if raw_offers and not offers:
        raise ProviderError("The flight provider returned an invalid response. Please try again later.")
    return offers


def demo_offers(query):
    airlines = [
        ("Emirates", "EK", 1240, 235),
        ("EgyptAir", "MS", 980, 250),
        ("Qatar Airways", "QR", 1420, 355),
    ]
    return [
        {
            "id": f"demo-{code}",
            "price": price * query.adults,
            "currency": "AED",
            "duration": duration,
            "stops": 0,
            "segments": [
                {
                    "airline": name,
                    "flight_number": f"{code}927",
                    "origin": query.origin,
                    "destination": query.destination,
                    "departure": f"{query.departure} 09:20",
                    "arrival": f"{query.departure} 12:15",
                }
            ],
        }
        for name, code, price, duration in airlines
    ]


def search_flights(query, settings):
    store = Store(settings.database_path)
    cache_key = settings.provider + ":" + query.cache_key()
    cached = store.cached(cache_key)
    if cached is not None:
        return cached | {"cached": True}
    if settings.provider == "demo":
        offers = demo_offers(query)
    else:
        store.limit("provider:" + datetime.now(UTC).date().isoformat(), settings.daily_provider_limit, 86400)
        offers = fetch_live(query, settings)
    filtered = [
        offer
        for offer in offers
        if (not query.direct or offer["stops"] == 0)
        and (query.budget is None or offer["price"] <= query.budget)
        and (
            not query.airline
            or all(
                segment["flight_number"].replace(" ", "").startswith(query.airline)
                for segment in offer["segments"]
            )
        )
    ]
    unique = {offer["id"]: offer for offer in sorted(filtered, key=lambda flight: -flight["price"])}
    payload = {
        "flights": sorted(unique.values(), key=lambda flight: flight["price"])[:20],
        "searched_at": datetime.now(UTC).isoformat(),
        "cached": False,
        "demo": settings.provider == "demo",
        "onward_url": onward_url(query),
        "query": query.model_dump(mode="json"),
    }
    store.cache(cache_key, payload)
    return payload
