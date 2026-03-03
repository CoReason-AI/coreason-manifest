import pytest
from typing import Any, cast
from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext

from coreason_manifest.core.compute.epistemic import ClinicalProposition, ReifiedEntity, ProvenanceSpan
from coreason_manifest.core.state.ledger import EpistemicLedger
from coreason_manifest.ports.mcp import create_mcp_server

class MockRequestContext:
    def __init__(self, meta_kwargs: dict[str, Any]):
        self.meta = meta_kwargs

class MockContext(Context[Any, Any, Any]):
    def __init__(self, request_context: MockRequestContext):
        self._request_context = cast(RequestContext[Any, Any, Any], request_context)

    @property
    def request_context(self) -> RequestContext[Any, Any, Any]:
        assert self._request_context is not None
        return self._request_context

def create_mock_proposition() -> ClinicalProposition:
    def dummy_validator(gid: str) -> bool:
        return True

    ctx = {"ontology_validator": dummy_validator, "document_hash_validator": dummy_validator}

    subject = ReifiedEntity.model_validate({"entity_string": "sub1", "global_id": "Patient"}, context=ctx)
    obj = ReifiedEntity.model_validate({"entity_string": "obj1", "global_id": "Condition"}, context=ctx)
    provenance = ProvenanceSpan.model_validate({"source_document_hash": "doc1", "page_number": 1, "bounding_box": (0.0, 0.0, 1.0, 1.0), "raw_text_crop": "doc1"}, context=ctx)

    return ClinicalProposition.model_validate({
        "subject": subject.model_dump(),
        "relation": "has",
        "object": obj.model_dump(),
        "provenance": provenance.model_dump()
    }, context=ctx)

@pytest.mark.asyncio
async def test_append_clinical_proposition_success() -> None:
    ledger = EpistemicLedger()
    mcp_server = create_mcp_server(ledger)

    proposition = create_mock_proposition()

    agent_sig = {
        "model_weights_hash": "hash123",
        "prompt_commit_hash": "commit123",
        "temperature": 0.7,
        "seed": 42,
        "inference_engine": "vLLM"
    }

    hardware_fingerprint = {
        "architecture": "Hopper",
        "compute_precision": "fp16",
        "vram_allocated": 16000
    }

    req_ctx = MockRequestContext({
        "x-agent-signature": agent_sig,
        "x-hardware-fingerprint": hardware_fingerprint
    })
    ctx = MockContext(request_context=req_ctx)

    tool = mcp_server._tool_manager.get_tool("append_clinical_proposition")

    assert tool is not None
    result = await tool.fn(proposition=proposition, ctx=ctx)
    assert "Successfully appended event" in result

@pytest.mark.asyncio
async def test_append_clinical_proposition_missing_headers() -> None:
    ledger = EpistemicLedger()
    mcp_server = create_mcp_server(ledger)

    proposition = create_mock_proposition()

    req_ctx = MockRequestContext({})
    ctx = MockContext(request_context=req_ctx)

    tool = mcp_server._tool_manager.get_tool("append_clinical_proposition")

    assert tool is not None

    with pytest.raises(ValueError, match="x-agent-signature header is missing or invalid"):
        await tool.fn(proposition=proposition, ctx=ctx)
