"""Tests for target validation and type detection."""

import pytest

from reconkit.models import TargetType
from reconkit.utils import validators


@pytest.mark.parametrize(
    "value,expected",
    [
        ("example.com", TargetType.DOMAIN),
        ("sub.example.co.uk", TargetType.DOMAIN),
        ("8.8.8.8", TargetType.IP),
        ("2001:4860:4860::8888", TargetType.IP),
        ("user@example.com", TargetType.EMAIL),
        ("johndoe", TargetType.USERNAME),
    ],
)
def test_detect_target_type(value, expected):
    assert validators.detect_target_type(value) == expected


def test_email_domain():
    assert validators.email_domain("a.b@mail.example.com") == "mail.example.com"


def test_ip_is_not_domain():
    assert validators.is_domain("8.8.8.8") is False
    assert validators.is_ip("8.8.8.8") is True


def test_validate_rejects_mismatch():
    with pytest.raises(ValueError):
        validators.validate("8.8.8.8", TargetType.DOMAIN)


def test_validate_empty():
    with pytest.raises(ValueError):
        validators.validate("")
