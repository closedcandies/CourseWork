"""Модульные тесты: генерация кодов и проверка входных данных (без БД)."""
import pytest
from pydantic import ValidationError

from app.codes import ALPHABET, CODE_LENGTH, is_valid_alias, new_code
from app.schemas import MAX_URL_LENGTH, LinkCreate


def test_code_format():
    code = new_code()
    assert len(code) == CODE_LENGTH
    assert set(code) <= set(ALPHABET)


def test_codes_are_random():
    codes = {new_code() for _ in range(10_000)}
    assert len(codes) == 10_000  # при 62^6 вариантах совпадения практически исключены


@pytest.mark.parametrize("alias, ok", [
    pytest.param("my-link", True, id="ok-dash"),
    pytest.param("abc", True, id="ok-min-length"),
    pytest.param("A_b-9", True, id="ok-mixed"),
    pytest.param("ab", False, id="too-short"),
    pytest.param("x" * 33, False, id="too-long"),
    pytest.param("ссылка", False, id="cyrillic"),
    pytest.param("with space", False, id="space"),
    pytest.param("api", False, id="reserved"),
    pytest.param("Assets", False, id="reserved-case"),
])
def test_alias_validation(alias, ok):
    assert is_valid_alias(alias) is ok


def test_link_create_valid():
    link = LinkCreate(url="https://example.com/path?q=1", alias="docs")
    assert str(link.url) == "https://example.com/path?q=1"


@pytest.mark.parametrize("payload", [
    pytest.param({"url": "ftp://example.com"}, id="not-http"),
    pytest.param({"url": "not a url"}, id="not-url"),
    pytest.param({"url": "https://example.com/" + "a" * MAX_URL_LENGTH}, id="too-long"),
    pytest.param({"url": "https://example.com", "alias": "api"}, id="reserved-alias"),
    pytest.param({"url": "https://example.com", "alias": "a b"}, id="bad-alias"),
])
def test_link_create_invalid(payload):
    with pytest.raises(ValidationError):
        LinkCreate(**payload)
