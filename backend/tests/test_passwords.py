"""Unit tests for bcrypt password hashing. No API or User persistence."""

from __future__ import annotations

import pytest

from app.auth.exceptions import InvalidPasswordError
from app.auth.passwords import hash_password, verify_password


def test_hash_password_generates_a_hash():
    hashed = hash_password("correct-horse-battery")
    assert isinstance(hashed, str)
    assert hashed.startswith("$2")
    assert "correct-horse-battery" not in hashed


def test_correct_password_verifies():
    hashed = hash_password("s3cret-value")
    assert verify_password("s3cret-value", hashed) is True


def test_incorrect_password_fails():
    hashed = hash_password("s3cret-value")
    assert verify_password("wrong-value", hashed) is False


def test_same_password_is_not_a_fixed_hash():
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second
    assert verify_password("same-password", first)
    assert verify_password("same-password", second)


def test_empty_password_is_rejected():
    with pytest.raises(InvalidPasswordError, match="required"):
        hash_password("")
    assert verify_password("", hash_password("ok")) is False


def test_non_string_password_is_rejected():
    with pytest.raises(InvalidPasswordError):
        hash_password(None)  # type: ignore[arg-type]
    assert verify_password("ok", None) is False  # type: ignore[arg-type]


def test_oversized_password_is_rejected():
    with pytest.raises(InvalidPasswordError, match="maximum"):
        hash_password("x" * 80)


def test_malformed_hash_does_not_verify():
    assert verify_password("anything", "not-a-bcrypt-hash") is False
