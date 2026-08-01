from __future__ import annotations

import json

import pytest

from ytforge.interfaces.agents.support import parse_json_response


def test_parse_json_response_accepts_bare_json() -> None:
    assert parse_json_response('{"a": 1}') == {"a": 1}


def test_parse_json_response_strips_json_language_fence() -> None:
    content = '```json\n{"a": 1}\n```'
    assert parse_json_response(content) == {"a": 1}


def test_parse_json_response_strips_bare_fence() -> None:
    content = '```\n{"a": 1}\n```'
    assert parse_json_response(content) == {"a": 1}


def test_parse_json_response_tolerates_surrounding_whitespace() -> None:
    content = '  \n```json\n{"a": 1}\n```\n  '
    assert parse_json_response(content) == {"a": 1}


def test_parse_json_response_handles_multiline_bodies() -> None:
    content = '```json\n{\n  "a": 1,\n  "b": [1, 2, 3]\n}\n```'
    assert parse_json_response(content) == {"a": 1, "b": [1, 2, 3]}


def test_parse_json_response_raises_on_malformed_json() -> None:
    with pytest.raises(json.JSONDecodeError):
        parse_json_response("not json at all")
