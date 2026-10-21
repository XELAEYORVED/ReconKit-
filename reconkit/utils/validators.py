"""Input validation and target-type detection.

ReconKit accepts four kinds of target: domain, IP (v4/v6), email, username.
These helpers validate inputs and auto-detect the type so modules and the
engine can select appropriate behaviour.
"""

from __future__ import annotations

import ipaddress
import re

from ..models import TargetType

# A pragmatic domain label pattern (RFC 1035-ish, allows IDN punycode xn--).
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
)
_EMAIL_RE = re.compile(r"^[^@\s]+@([^@\s]+\.[^@\s]+)$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,38}$")


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip())
        return True
    except ValueError:
        return False


def is_domain(value: str) -> bool:
    value = value.strip().rstrip(".")
    if is_ip(value):
        return False
    return bool(_DOMAIN_RE.match(value))


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def is_username(value: str) -> bool:
    return bool(_USERNAME_RE.match(value.strip()))


def email_domain(value: str) -> str | None:
    m = _EMAIL_RE.match(value.strip())
    return m.group(1).lower() if m else None


def normalize(value: str) -> str:
    return value.strip().lower().rstrip(".")


def detect_target_type(value: str) -> TargetType:
    """Best-effort auto-detection of a target's type."""
    v = value.strip()
    if is_email(v):
        return TargetType.EMAIL
    if is_ip(v):
        return TargetType.IP
    if is_domain(v):
        return TargetType.DOMAIN
    if is_username(v):
        return TargetType.USERNAME
    return TargetType.UNKNOWN


def validate(value: str, expected: TargetType | None = None) -> TargetType:
    """Validate a target, optionally forcing an expected type.

    Raises ValueError if the target is invalid for the (expected) type.
    """
    if not value or not value.strip():
        raise ValueError("Empty target")
    detected = detect_target_type(value)
    if expected is not None:
        if expected == TargetType.USERNAME and is_username(value):
            return TargetType.USERNAME
        if detected != expected:
            raise ValueError(f"Target '{value}' is not a valid {expected.value}")
        return expected
    if detected == TargetType.UNKNOWN:
        raise ValueError(f"Could not determine target type for '{value}'")
    return detected
