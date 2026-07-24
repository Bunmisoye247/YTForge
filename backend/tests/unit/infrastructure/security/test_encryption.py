from __future__ import annotations

import base64

import pytest

from ytforge.infrastructure.security.encryption import EnvelopeEncryptor

_MASTER_KEY = base64.b64encode(b"0" * 32).decode()


def test_encrypt_then_decrypt_round_trips() -> None:
    encryptor = EnvelopeEncryptor(_MASTER_KEY)

    secret = encryptor.encrypt("my-refresh-token")

    assert encryptor.decrypt(secret) == "my-refresh-token"


def test_ciphertext_does_not_contain_plaintext() -> None:
    encryptor = EnvelopeEncryptor(_MASTER_KEY)

    secret = encryptor.encrypt("super-secret-value")

    assert b"super-secret-value" not in secret.ciphertext
    assert b"super-secret-value" not in secret.data_key_ciphertext


def test_each_encryption_uses_a_fresh_data_key() -> None:
    encryptor = EnvelopeEncryptor(_MASTER_KEY)

    first = encryptor.encrypt("same-plaintext")
    second = encryptor.encrypt("same-plaintext")

    assert first.data_key_ciphertext != second.data_key_ciphertext
    assert first.ciphertext != second.ciphertext


def test_wrong_master_key_fails_to_decrypt() -> None:
    encryptor = EnvelopeEncryptor(_MASTER_KEY)
    secret = encryptor.encrypt("my-refresh-token")

    other_key = base64.b64encode(b"1" * 32).decode()
    other_encryptor = EnvelopeEncryptor(other_key)

    with pytest.raises(Exception):  # noqa: B017 - cryptography raises its own InvalidTag
        other_encryptor.decrypt(secret)


def test_master_key_must_be_32_bytes() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        EnvelopeEncryptor(base64.b64encode(b"too-short").decode())
