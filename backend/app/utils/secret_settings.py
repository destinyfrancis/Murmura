"""Helpers for encrypted-at-rest runtime settings."""

from __future__ import annotations

ENCRYPTED_VALUE_PREFIX = "enc:v1:"
_SECRET_PREFIXES = ("api_key_",)


def is_secret_setting(key: str) -> bool:
    """Return True when a runtime setting should be encrypted at rest."""
    return key.startswith(_SECRET_PREFIXES)


def is_encrypted_setting_value(value: str) -> bool:
    """Return True when *value* uses the runtime settings encryption envelope."""
    return value.startswith(ENCRYPTED_VALUE_PREFIX)


def encrypt_setting_value(key: str, value: str) -> str:
    """Encrypt sensitive settings before writing them to SQLite."""
    if not is_secret_setting(key) or not value or is_encrypted_setting_value(value):
        return value

    from backend.app.utils.encryption import encrypt_value  # noqa: PLC0415

    return f"{ENCRYPTED_VALUE_PREFIX}{encrypt_value(value)}"


def decrypt_setting_value(key: str, value: str) -> str:
    """Decrypt sensitive settings loaded from SQLite.

    Plaintext values are returned unchanged so legacy databases can still boot;
    the DB migration path re-encrypts them when ``DATA_ENCRYPTION_KEY`` exists.
    """
    if not is_secret_setting(key) or not is_encrypted_setting_value(value):
        return value

    from backend.app.utils.encryption import decrypt_value  # noqa: PLC0415

    return decrypt_value(value.removeprefix(ENCRYPTED_VALUE_PREFIX))
