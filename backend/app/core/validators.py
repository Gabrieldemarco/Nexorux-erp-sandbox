import re
from typing import Optional


def validate_uruguayan_rut(v: str) -> str:
    """Accept person CI (7-8 digits + check) or company RUT (11-12 digits)."""
    cleaned = re.sub(r"[.\-\s]", "", v or "").upper()
    if re.fullmatch(r"[0-9]{11,12}", cleaned):
        return cleaned
    if re.fullmatch(r"[0-9]{7,8}[0-9K]", cleaned):
        return cleaned
    raise ValueError("Invalid RUT format for Uruguay")


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(v: str) -> str:
    if not _EMAIL_RE.match(v):
        raise ValueError("Invalid email format")
    return v.lower()


_PHONE_RE = re.compile(r"^\+?[0-9\s\-]{7,20}$")


def validate_phone(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return v
    if not _PHONE_RE.match(v):
        raise ValueError("Invalid phone format")
    return v


__all__ = [
    "validate_uruguayan_rut",
    "validate_email",
    "validate_phone",
]
