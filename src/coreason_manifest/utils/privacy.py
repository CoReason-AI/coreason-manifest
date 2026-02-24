import hashlib
import hmac
import re
import warnings
from typing import Any, ClassVar


class PrivacySentinel:
    """
    A configurable data sanitizer that redacts sensitive information (PII/Secrets)
    from data structures before logging.
    """

    # SOTA: Pre-compiled regex patterns for high-throughput telemetry
    _EMAIL_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    _CREDIT_CARD_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    _SSN_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    _WORD_BOUNDARY_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"[^a-z0-9]")

    # Terms that must appear as distinct words (separated by _) to trigger redaction
    SENSITIVE_WORDS: ClassVar[set[str]] = {"password", "token", "auth", "secret", "credential", "passcode"}

    # Terms that trigger redaction if they appear anywhere in the key
    # We normalize "-" to "_" before checking these.
    SENSITIVE_SUBSTRINGS: ClassVar[set[str]] = {
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "private_key",
        "secret_key",
    }

    def __init__(
        self,
        redact_pii: bool = True,
        redact_secrets: bool = True,
        hashing_salt: str = "",
        custom_sensitive_keys: set[str] | None = None,
    ):
        self.redact_pii = redact_pii
        self.redact_secrets = redact_secrets
        self.hashing_salt = hashing_salt

        # Merge default sensitive words with custom ones
        self.sensitive_words = self.SENSITIVE_WORDS.copy()
        if custom_sensitive_keys:
            self.sensitive_words.update(custom_sensitive_keys)

    def sanitize(self, data: Any) -> Any:
        """
        Recursively sanitizes the input data.
        """
        # Ensure Pydantic objects are converted to dicts before evaluation
        if hasattr(data, "model_dump") and callable(data.model_dump):
            data = data.model_dump()
        elif hasattr(data, "dict") and callable(data.dict):  # Fallback for older models
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=DeprecationWarning)
                data = data.dict()

        if isinstance(data, dict):
            return {k: self._sanitize_kv(k, v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.sanitize(item) for item in data]
        if isinstance(data, str):
            return self._sanitize_string(data)
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

            # Check for specific substrings (using class default)
            if any(term in normalized_key for term in self.SENSITIVE_SUBSTRINGS):
                return self._redact(str(value))

            # Check exact match for custom keys
            if normalized_key in self.sensitive_words:
                return self._redact(str(value))

            # Check for sensitive words (using instance merged set)
            parts = self._WORD_BOUNDARY_PATTERN.split(lower_key)
            if any(part in self.sensitive_words for part in parts):
                return self._redact(str(value))

        # 2. Recurse or check value
        return self.sanitize(value)

    def _sanitize_string(self, text: str) -> str:
        """Checks a string value for PII and precision-redacts only the matched data."""
        if not self.redact_pii:
            return text

        # Apply precision substitutions
        text = self._EMAIL_PATTERN.sub(lambda m: self._redact(m.group(0)), text)
        text = self._CREDIT_CARD_PATTERN.sub(lambda m: self._redact(m.group(0)), text)
        return self._SSN_PATTERN.sub(lambda m: self._redact(m.group(0)), text)

    def _redact(self, value: str) -> str:
        """
        Returns a structured redaction string: <REDACTED:SECRET:{hash_prefix}>
        """
        # Use HMAC-SHA256 which is mathematically resistant to length-extension and collision
        salt_bytes = self.hashing_salt.encode("utf-8")
        value_bytes = value.encode("utf-8")
        full_hash = hmac.new(salt_bytes, value_bytes, hashlib.sha256).hexdigest()
        # Use first 8 chars of hash as prefix
        hash_prefix = full_hash[:8]
        return f"<REDACTED:SECRET:{hash_prefix}>"
