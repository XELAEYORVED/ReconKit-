"""Symmetric encryption for API keys stored in the database.

Derives a Fernet key from the application secret so stored API keys are not
kept in plaintext. Not a substitute for a real secrets manager, but prevents
casual disclosure if the DB file leaks.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


def _fernet() -> Fernet:
    secret = get_settings().secret_key.encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
