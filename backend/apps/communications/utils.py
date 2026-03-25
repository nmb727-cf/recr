import base64
import hashlib
import hmac
import json

from cryptography.fernet import Fernet
from django.conf import settings


def _derive_key() -> bytes:
    explicit = getattr(settings, 'COMM_EMAIL_ENCRYPTION_KEY', '')
    if explicit:
        return explicit.encode()

    seed = getattr(settings, 'SECRET_KEY', 'talentos-email-secret').encode()
    digest = hashlib.sha256(seed).digest()
    return base64.urlsafe_b64encode(digest)


def get_cipher() -> Fernet:
    return Fernet(_derive_key())


def encrypt_string(text: str) -> str:
    if not text:
        return ''
    return get_cipher().encrypt(text.encode()).decode()


def decrypt_string(encrypted_text: str) -> str:
    if not encrypted_text:
        return ''
    try:
        return get_cipher().decrypt(encrypted_text.encode()).decode()
    except Exception:
        return ''


def encrypt_json(data: dict) -> str:
    if not data:
        return ''
    return encrypt_string(json.dumps(data))


def decrypt_json(encrypted_data: str) -> dict:
    if not encrypted_data:
        return {}
    raw = decrypt_string(encrypted_data)
    try:
        return json.loads(raw)
    except Exception:
        return {}


def redact_secret(value: str) -> str:
    if not value:
        return ''
    if len(value) <= 6:
        return '***'
    return f'{value[:3]}***{value[-3:]}'


def verify_webhook_signature(payload: bytes, supplied: str, secret: str) -> bool:
    if not supplied or not secret:
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)
