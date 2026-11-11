import json
import sqlite3
from contextlib import closing
from unittest.mock import patch

import httpx2
import pytest

from main import interpret_trip
from scripts.backup import backup
from tools import ProviderError


def ai_response(extraction=None, refusal=None):
    return httpx2.Response(
        200,
        json={
            "id": "chat-test",
            "object": "chat.completion",
            "created": 1,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(extraction) if extraction else None,
                        "refusal": refusal,
                    },
                }
            ],
        },
        request=httpx2.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )


def test_ai_extracts_valid_fields_without_executing_a_search(settings, query):
    from dataclasses import replace

    settings = replace(settings, openai_api_key="test-not-a-real-key")
    extraction = query.model_dump(mode="json") | {"clarification": None}
    with patch.object(httpx2.Client, "send", return_value=ai_response(extraction)):
        response = interpret_trip("Dubai to Cairo on the specified date", settings)
    assert response["query"] == query.model_dump(mode="json")
    assert response["clarification"] is None
    assert not settings.database_path.exists()


@pytest.mark.parametrize(
    "change",
    [
        {"departure": None, "clarification": "Which date?"},
        {"departure": "2020-01-01"},
        {"origin": "not-an-airport"},
    ],
)
def test_ai_missing_or_invalid_trip_requires_user_clarification(settings, query, change):
    from dataclasses import replace

    settings = replace(settings, openai_api_key="test-not-a-real-key")
    extraction = query.model_dump(mode="json") | {"clarification": None} | change
    with patch.object(httpx2.Client, "send", return_value=ai_response(extraction)):
        response = interpret_trip("A trip with incomplete details", settings)
    assert response["query"] is None and response["clarification"]


def test_ai_refusal_asks_for_manual_form(settings):
    from dataclasses import replace

    settings = replace(settings, openai_api_key="test-not-a-real-key")
    with patch.object(httpx2.Client, "send", return_value=ai_response(refusal="Cannot comply")):
        response = interpret_trip("A request the model refuses", settings)
    assert response["query"] is None


def test_ai_missing_configuration_preserves_manual_search(settings):
    with pytest.raises(ProviderError, match="search form"):
        interpret_trip("Dubai to Cairo", settings)


def test_backup_restores_user_data_and_does_not_overwrite(store, tmp_path):
    store.create_user("backup@example.com", "test-hash")
    output = tmp_path / "backup.db"
    backup(store.path, output)
    with closing(sqlite3.connect(output)) as conn:
        assert conn.execute("SELECT email FROM users").fetchone()[0] == "backup@example.com"
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(ValueError):
        backup(store.path, output)
