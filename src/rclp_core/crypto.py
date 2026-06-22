from __future__ import annotations

import base64
import binascii
import json
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)
from pydantic import BaseModel


def canonical_json(payload: Any) -> bytes:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json", exclude={"signature"})
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data.encode("ascii"))


class DemoKeyPair:
    """Non-production Ed25519 keypair helper for protocol demos."""

    def __init__(self, private_key: Ed25519PrivateKey | None = None):
        self.private_key = private_key or Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    @property
    def public_key_b64(self) -> str:
        raw = self.public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        return b64(raw)

    @property
    def private_key_pem(self) -> bytes:
        return self.private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())

    def sign(self, payload: Any) -> str:
        return b64(self.private_key.sign(canonical_json(payload)))

    def verify(self, payload: Any, signature: str) -> bool:
        try:
            self.public_key.verify(unb64(signature), canonical_json(payload))
            return True
        except (binascii.Error, InvalidSignature, ValueError):
            return False


def public_key_from_b64(public_key_b64: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(unb64(public_key_b64))


def verify_with_public_key_b64(payload: Any, signature: str, public_key_b64: str) -> bool:
    try:
        public_key_from_b64(public_key_b64).verify(unb64(signature), canonical_json(payload))
        return True
    except (binascii.Error, InvalidSignature, ValueError):
        return False
