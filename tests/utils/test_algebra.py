# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from pydantic import AnyUrl

from coreason_manifest.utils.algebra import _validate_ssrf_safety


def test_validate_ssrf_safety() -> None:
    # Valid global URLs
    assert _validate_ssrf_safety(AnyUrl("https://example.com"))
    assert _validate_ssrf_safety(AnyUrl("http://8.8.8.8"))

    # Invalid private/local URLs
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://127.0.0.1/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://169.254.169.254/latest/meta-data/"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://10.0.0.1/"))

    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://localhost/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://localhost.localdomain/api"))

    # Bypass formats for 127.0.0.1
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://127.1/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://2130706433/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://0x7f000001/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://0177.0.0.1/api"))


def test_schema_sealing_no_vault() -> None:
    from coreason_manifest.utils.algebra import compute_schema_seal, verify_schema_seal

    # Test sealing and verification when Vault is not configured.
    schema = {"title": "Test Schema", "properties": {"id": {"type": "string"}}}

    # Sealing should return the SHA-256 hash string because Vault is not configured.
    seal = compute_schema_seal(schema)
    assert isinstance(seal, str)
    assert len(seal) == 64  # SHA-256 hex digest length

    # Verification with matching string seal should succeed.
    assert verify_schema_seal(schema, seal) is True

    # Verification with mismatched string seal should raise ValueError.
    with pytest.raises(ValueError, match="Schema seal mismatch"):
        verify_schema_seal(schema, "wrong_hash" * 8)

    # Verification with a dict seal but no Vault configured should raise ValueError.
    dict_seal = {"hash": seal, "signature": "some_signature"}
    with pytest.raises(ValueError, match="Vault is not configured for signature verification"):
        verify_schema_seal(schema, dict_seal)

    # Verification with a dict seal where hash doesn't match should raise ValueError (even without Vault)
    bad_dict_seal = {"hash": "wrong_hash", "signature": "some_signature"}
    with pytest.raises(ValueError, match="Schema seal hash mismatch"):
        verify_schema_seal(schema, bad_dict_seal)


def test_schema_sealing_with_vault() -> None:
    import contextlib
    import os

    from coreason_manifest.utils.algebra import compute_schema_seal, verify_schema_seal

    vault_addr = os.environ.get("VAULT_ADDR")
    vault_token = os.environ.get("VAULT_TOKEN")
    if not vault_addr or not vault_token:
        pytest.skip("VAULT_ADDR and VAULT_TOKEN not configured in environment, skipping Vault integration test.")

    import hvac
    import hvac.exceptions

    client = hvac.Client(url=vault_addr, token=vault_token)

    # Ensure the transit secrets engine is enabled at the default path
    # and the key "coreason-merkle-key" exists.
    with contextlib.suppress(hvac.exceptions.InvalidRequest):
        client.sys.enable_secrets_engine(backend_type="transit", path="transit")

    with contextlib.suppress(hvac.exceptions.InvalidRequest):
        client.secrets.transit.create_key(name="coreason-merkle-key")

    schema = {"title": "Test Vault Schema", "properties": {"id": {"type": "string"}}}

    # Compute seal (should return dict with hash and signature)
    seal = compute_schema_seal(schema)
    assert isinstance(seal, dict)
    assert "hash" in seal
    assert "signature" in seal

    # Verify seal should succeed
    assert verify_schema_seal(schema, seal) is True

    # Verify seal with wrong signature should fail
    bad_seal = seal.copy()
    bad_seal["signature"] = "vault:v1:some_invalid_signature_bytes_base64"
    with pytest.raises(ValueError, match="Vault Transit rejected the signature"):
        verify_schema_seal(schema, bad_seal)
