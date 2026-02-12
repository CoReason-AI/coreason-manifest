import hashlib
import re
from typing import Any

class PrivacySentinel:
    """
    A configurable data sanitizer that redacts sensitive information (PII/Secrets)
    from data structures before logging.
    """

    # Basic regex patterns for PII detection
    EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    # Simple Credit Card regex (13-19 digits, possibly with separators)
    CREDIT_CARD_REGEX = r"\b(?:\d[ -]*?){13,16}\b"
    # US SSN regex (AAA-GG-SSSS)
    SSN_REGEX = r"\b\d{3}-\d{2}-\d{4}\b"

    # Terms that must appear as distinct words (separated by _) to trigger redaction
    SENSITIVE_WORDS = {"password", "token", "auth", "secret", "credential", "passcode"}

    # Terms that trigger redaction if they appear anywhere in the key
    # We normalize "-" to "_" before checking these.
    SENSITIVE_SUBSTRINGS = {"api_key", "apikey", "access_token", "refresh_token", "private_key", "secret_key"}

    def __init__(self, redact_pii: bool = True, redact_secrets: bool = True, hashing_salt: str = ""):
        self.redact_pii = redact_pii
        self.redact_secrets = redact_secrets
        self.hashing_salt = hashing_salt

    def sanitize(self, data: Any) -> Any:
        """
        Recursively sanitizes the input data.
        """
        if isinstance(data, dict):
            return {k: self._sanitize_kv(k, v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_kv(self, key: str, value: Any) -> Any:
        """
        Sanitizes a key-value pair.
        Checks the key for secret terms first.
        """
        # 1. Secret Detection based on Key Name
        if self.redact_secrets and isinstance(key, str):
            lower_key = key.lower()
            normalized_key = lower_key.replace("-", "_")

            # Check for specific substrings
            if any(term in normalized_key for term in self.SENSITIVE_SUBSTRINGS):
                 return self._redact(str(value))

            # Check for sensitive words (split by non-alphanumeric)
            parts = re.split(r'[^a-z0-9]', lower_key)
            if any(part in self.SENSITIVE_WORDS for part in parts):
                return self._redact(str(value))

        # 2. Recurse or check value
        return self.sanitize(value)

    def _sanitize_string(self, text: str) -> str:
        """
        Checks a string value for PII.
        """
        if not self.redact_pii:
            return text

        if re.search(self.EMAIL_REGEX, text) or \
           re.search(self.CREDIT_CARD_REGEX, text) or \
           re.search(self.SSN_REGEX, text):
            return self._redact(text)

        return text

    def _redact(self, value: str) -> str:
        """
        Returns a structured redaction string: <REDACTED:SECRET:{hash_prefix}>
        """
        # compute SHA256(value + salt)
        combined = value + self.hashing_salt
        full_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        # Use first 8 chars of hash as prefix
        hash_prefix = full_hash[:8]
        return f"<REDACTED:SECRET:{hash_prefix}>"
