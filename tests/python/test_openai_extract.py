import json

import pytest

from pipeline.openai_extract import (
    OpenAIExtractionError,
    build_extraction_payload,
    extract_candidates,
    parse_response_json,
    require_openai_api_key,
)
from pipeline.oracle_discovery import OraclePage


class FakeResponse:
    def __init__(self, payload, status_error=None):
        self._payload = payload
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        return self._payload


def _valid_candidate_payload():
    return {
        "product": "oracle-database",
        "versions": [
            {
                "index": {"label": "Oracle Database 27ai"},
                "record": {
                    "product": "oracle-database",
                    "version": "27ai",
                    "release_label": "Oracle Database 27ai",
                    "record_type": "release",
                    "released": "2027-01-01",
                    "sections": {
                        "certification": [],
                        "whats_new": [
                            {
                                "title": "Feature",
                                "description": "A sourced feature.",
                                "source_url": "https://docs.oracle.com/database/feature",
                            }
                        ],
                        "behavior_changes": [],
                        "deprecated": [],
                        "desupported": [],
                    },
                },
            }
        ],
    }


def test_require_openai_api_key_fails_when_missing():
    with pytest.raises(OpenAIExtractionError, match="OPENAI_API_KEY"):
        require_openai_api_key({})


def test_require_openai_api_key_returns_key():
    assert require_openai_api_key({"OPENAI_API_KEY": "sk-test"}) == "sk-test"


def test_build_extraction_payload_uses_structured_outputs_schema():
    pages = [OraclePage("https://docs.oracle.com/a", "<html>Oracle Database 27ai</html>")]

    payload = build_extraction_payload(
        product_id="oracle-database",
        product_label="Oracle Database",
        existing_versions=["26ai"],
        pages=pages,
        model="gpt-5",
    )

    assert payload["model"] == "gpt-5"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert payload["text"]["format"]["name"] == "oracle_release_delta_candidates"
    assert payload["text"]["format"]["schema"]["additionalProperties"] is False
    assert "Oracle-owned" in payload["instructions"]
    assert "https://docs.oracle.com/a" in payload["input"]


def test_parse_response_json_reads_output_text():
    payload = _valid_candidate_payload()
    response = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": json.dumps(payload)}
                ],
            }
        ]
    }

    assert parse_response_json(response) == payload


def test_parse_response_json_rejects_refusal():
    response = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "refusal", "refusal": "No"}
                ],
            }
        ]
    }

    with pytest.raises(OpenAIExtractionError, match="refused"):
        parse_response_json(response)


def test_extract_candidates_posts_to_responses_api():
    calls = []

    def post(url, headers, json, timeout):
        calls.append((url, headers, json, timeout))
        return FakeResponse({
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": '{"product":"oracle-database","versions":[]}'}
                    ],
                }
            ]
        })

    result = extract_candidates(
        api_key="sk-test",
        product_id="oracle-database",
        product_label="Oracle Database",
        existing_versions=["26ai"],
        pages=[OraclePage("https://docs.oracle.com/a", "<html></html>")],
        post=post,
        model="gpt-5",
    )

    assert result == {"product": "oracle-database", "versions": []}
    assert calls[0][0] == "https://api.openai.com/v1/responses"
    assert calls[0][1]["Authorization"] == "Bearer sk-test"
    assert calls[0][2]["model"] == "gpt-5"
    assert calls[0][3] == 60
