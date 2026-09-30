import pytest
from types import SimpleNamespace

pytest.importorskip("presidio_analyzer")

from privacy import (
    BLOCKED_REQUEST,
    PrivacyEngine,
    blocked_content_for_key,
    contains_non_text_model_content,
    select_non_overlapping_results,
    walk_strings,
)


def test_walk_strings_preserves_structure():
    value = {"a": ["john@example.com", {"b": "John"}], "n": 4}
    out = walk_strings(value, lambda s: f"<{s}>")
    assert out == {"a": ["<john@example.com>", {"b": "<John>"}], "n": 4}


def test_detects_image_payload():
    payload = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}}]
    assert contains_non_text_model_content(payload)


def test_plain_text_payload_not_flagged_as_non_text():
    payload = [{"role": "user", "content": "hello"}]
    assert not contains_non_text_model_content(payload)


def test_blocked_messages_shape():
    assert blocked_content_for_key("messages") == [
        {"role": "user", "content": BLOCKED_REQUEST}
    ]


def test_secret_filter_removes_authorization_header():
    text = "Authorization: Bearer secret-token\nHello"
    out = PrivacyEngine.remove_high_confidence_secrets(text)
    assert "secret-token" not in out
    assert "[SECRET_REMOVED]" in out


def test_overlapping_results_prefer_confidence_then_longer_span():
    results = [
        SimpleNamespace(start=0, end=5, score=0.70),
        SimpleNamespace(start=0, end=11, score=0.70),
        SimpleNamespace(start=20, end=24, score=0.99),
        SimpleNamespace(start=21, end=25, score=0.50),
    ]
    selected = select_non_overlapping_results(results)
    assert [(item.start, item.end) for item in selected] == [(0, 11), (20, 24)]
