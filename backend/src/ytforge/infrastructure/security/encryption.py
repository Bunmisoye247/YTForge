from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ytforge.infrastructure.config.settings import get_settings

_NONCE_BYTES = 12
_KEY_BYTES = 32
_CURRENT_KEY_VERSION = 1


@dataclass(frozen=True, slots=True)
class EncryptedSecret:
    """The two ciphertexts + nonce persisted for an envelope-encrypted
    value (ARCHITECTURE.md §8) — maps 1:1 onto `channels`' `oauth_refresh_
    token_ciphertext`/`oauth_refresh_token_nonce`/`data_key_ciphertext`/
    `encryption_key_version` columns."""

    ciphertext: bytes
    nonce: bytes
    data_key_ciphertext: bytes
    key_version: int


class EnvelopeEncryptor:
    """Envelope encryption: each secret gets its own random data key (DEK)
    that encrypts the plaintext; the DEK itself is encrypted by an
    external master key (KEK, `security.encryption_master_key`) that never
    touches the database. Only the two ciphertexts + a nonce are ever
    persisted — compromising the DB alone reveals nothing without the KEK.
    `key_version` exists for future KEK rotation (only version 1 exists
    today; a rotation would look up the right KEK by version at decrypt
    time)."""

    def __init__(self, master_key_b64: str) -> None:
        master_key = base64.b64decode(master_key_b64)
        if len(master_key) != _KEY_BYTES:
            raise ValueError(f"encryption master key must decode to {_KEY_BYTES} bytes, got {len(master_key)}")
        self._kek = AESGCM(master_key)

    def encrypt(self, plaintext: str) -> EncryptedSecret:
        data_key = AESGCM.generate_key(bit_length=_KEY_BYTES * 8)
        dek = AESGCM(data_key)

        nonce = os.urandom(_NONCE_BYTES)
        ciphertext = dek.encrypt(nonce, plaintext.encode("utf-8"), None)

        dek_nonce = os.urandom(_NONCE_BYTES)
        data_key_ciphertext = dek_nonce + self._kek.encrypt(dek_nonce, data_key, None)

        return EncryptedSecret(
            ciphertext=ciphertext,
            nonce=nonce,
            data_key_ciphertext=data_key_ciphertext,
            key_version=_CURRENT_KEY_VERSION,
        )

    def decrypt(self, secret: EncryptedSecret) -> str:
        if secret.key_version != _CURRENT_KEY_VERSION:
            raise ValueError(f"unsupported encryption key version {secret.key_version}")
        dek_nonce, dek_ciphertext = secret.data_key_ciphertext[:_NONCE_BYTES], secret.data_key_ciphertext[_NONCE_BYTES:]
        data_key = self._kek.decrypt(dek_nonce, dek_ciphertext, None)
        dek = AESGCM(data_key)
        plaintext = dek.decrypt(secret.nonce, secret.ciphertext, None)
        return plaintext.decode("utf-8")


@lru_cache
def get_envelope_encryptor() -> EnvelopeEncryptor:
    """Cached the same way `infrastructure.db.session.get_engine()` is —
    lets `SqlAlchemyChannelRepository` reach a correctly-configured
    encryptor without every `SqlAlchemyUnitOfWork` call site needing a new
    constructor parameter threaded through it."""
    return EnvelopeEncryptor(get_settings().security.encryption_master_key.get_secret_value())
