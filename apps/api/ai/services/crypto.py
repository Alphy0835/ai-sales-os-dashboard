import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet | None:
    key = getattr(settings, "AI_CREDENTIALS_KEY", "") or ""
    if not key:
        return None
    if len(key) != 44:
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest).decode("ascii")
    return Fernet(key.encode("ascii") if isinstance(key, str) else key)


def encrypt_secret(value: str) -> str:
    if not value:
        return ""
    f = _fernet()
    if f is None:
        return value
    return f.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    if not value:
        return ""
    f = _fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return ""
