from __future__ import annotations

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    algorithm, iterations_str, salt, digest_hex = hashed.split("$")
    if algorithm != _ALGORITHM:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations_str)
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


class Pbkdf2PasswordHasher:
    """Adapts the module-level functions above to the application-layer
    `PasswordHasher` port."""

    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, password: str, hashed: str) -> bool:
        return verify_password(password, hashed)
