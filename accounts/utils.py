import re
import secrets


PHONE_RE = re.compile(r"\D+")


def normalize_phone(raw):
    """Convert any input into +998XXXXXXXXX format. Returns None if invalid."""
    if not raw:
        return None
    digits = PHONE_RE.sub("", str(raw))
    if not digits:
        return None
    # Strip leading 00 / +
    if digits.startswith("00"):
        digits = digits[2:]
    # If it starts with 8 and is 9 digits long → assume local without country code
    if len(digits) == 9 and digits[0] in "789":
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    if len(digits) >= 10:
        return "+" + digits
    return None


def generate_otp_code():
    """Six-digit numeric code, zero-padded."""
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_link_token(length=24):
    return secrets.token_urlsafe(length)
