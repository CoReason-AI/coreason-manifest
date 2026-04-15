# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import contextlib
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import HttpUrl, ValidationError

from coreason_manifest.spec.ontology import (
    BoundedJSONRPCIntent,
    BrowserDOMState,
    HTTPTransportProfile,
    MCPCapabilityWhitelistPolicy,
    MCPServerManifest,
    SemanticFirewallPolicy,
    StdioTransportProfile,
    VerifiableCredentialPresentationReceipt,
)


@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    st.recursive(
        st.none()
        | st.booleans()
        | st.floats(allow_nan=False, allow_infinity=False)
        | st.integers()
        | st.text(max_size=10000),
        lambda children: st.lists(children) | st.dictionaries(st.text(max_size=10000), children),
        max_leaves=100,
    )
)
def test_fuzz_jsonrpc_params(params_payload: Any) -> None:
    try:
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", id="1", params=params_payload)
    except ValidationError:
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")


@given(st.from_regex(r"^https?://[a-zA-Z0-9.-]+(:\d+)?/.*$", fullmatch=True))
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_fuzz_browser_dom_valid_urls(url: str) -> None:
    try:
        BrowserDOMState(
            current_url=url,
            viewport_size=(1024, 768),
            dom_hash="0" * 64,
            accessibility_tree_hash="0" * 64,
        )
    except ValidationError:
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")


@given(
    st.dictionaries(
        st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), min_size=1),
        st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), min_size=1),
    )
)
@settings(deadline=None)
def test_fuzz_http_transport_profile_valid(headers: dict[str, str]) -> None:
    with contextlib.suppress(ValidationError):
        HTTPTransportProfile(uri=HttpUrl("http://example.com"), headers=headers)


# 4. SemanticFirewallPolicy
@given(st.lists(st.text(max_size=2000), max_size=100))
def test_fuzz_semantic_firewall_policy_forbidden_intents(intents: list[str]) -> None:
    with contextlib.suppress(ValidationError):
        SemanticFirewallPolicy(max_input_tokens=1000, forbidden_intents=intents, action_on_violation="drop")


# 5. MCPServerManifest
@given(st.from_regex(r"^did:coreason:[a-zA-Z0-9.-]+$", fullmatch=True))
def test_fuzz_mcp_server_manifest_valid_did(did_str: str) -> None:
    attest = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc", issuer_did=did_str, cryptographic_proof_blob="test", authorization_claims={}
    )
    with contextlib.suppress(ValidationError):
        MCPServerManifest(
            server_cid="test",
            transport=StdioTransportProfile(command="ls"),
            capability_whitelist=MCPCapabilityWhitelistPolicy(
                authorized_capability_array=["test"], allowed_resources=["test"], allowed_prompts=["test"]
            ),
            attestation_receipt=attest,
            binary_hash="0" * 64,
        )


@given(st.from_regex(r"^did:(?!coreason:)[a-zA-Z0-9.-]+:[a-zA-Z0-9.-]+$", fullmatch=True))
def test_fuzz_mcp_server_manifest_invalid_did(did_str: str) -> None:
    try:
        attest = VerifiableCredentialPresentationReceipt(
            presentation_format="jwt_vc", issuer_did=did_str, cryptographic_proof_blob="test", authorization_claims={}
        )
    except ValidationError:
        return

    with pytest.raises(ValidationError, match="UNAUTHORIZED MCP MOUNT"):
        MCPServerManifest(
            server_cid="test",
            transport=StdioTransportProfile(command="ls"),
            capability_whitelist=MCPCapabilityWhitelistPolicy(
                authorized_capability_array=["test"], allowed_resources=["test"], allowed_prompts=["test"]
            ),
            attestation_receipt=attest,
            binary_hash="0" * 64,
        )
