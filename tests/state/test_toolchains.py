import pytest
from pydantic import ValidationError

from coreason_manifest.state.toolchains import (
    CognitiveLoadTrimmer,
    JITToolSynthesisConfig,
    SemanticToolchain,
)


def test_cognitive_load_trimmer_valid() -> None:
    """Test successful instantiation of CognitiveLoadTrimmer."""
    trimmer = CognitiveLoadTrimmer(
        max_tool_tokens=2048,
        auto_provision_subagent=True,
        context_compression_ratio=0.75,
    )
    assert trimmer.max_tool_tokens == 2048
    assert trimmer.auto_provision_subagent is True
    assert trimmer.context_compression_ratio == 0.75


def test_cognitive_load_trimmer_invalid_bounds() -> None:
    """Test that context_compression_ratio validates its bounds."""
    with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
        CognitiveLoadTrimmer(
            max_tool_tokens=1024,
            auto_provision_subagent=False,
            context_compression_ratio=-0.1,  # Below 0.0
        )

    with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
        CognitiveLoadTrimmer(
            max_tool_tokens=1024,
            auto_provision_subagent=False,
            context_compression_ratio=1.1,  # Above 1.0
        )


def test_cognitive_load_trimmer_invalid_tokens() -> None:
    """Test that max_tool_tokens must be strictly positive."""
    with pytest.raises(ValidationError, match=r"Input should be greater than 0"):
        CognitiveLoadTrimmer(
            max_tool_tokens=0,
            auto_provision_subagent=False,
            context_compression_ratio=0.5,
        )
    with pytest.raises(ValidationError, match=r"Input should be greater than 0"):
        CognitiveLoadTrimmer(
            max_tool_tokens=-10,
            auto_provision_subagent=False,
            context_compression_ratio=0.5,
        )


def test_jit_tool_synthesis_config_valid() -> None:
    """Test successful instantiation of JITToolSynthesisConfig."""
    config = JITToolSynthesisConfig(
        generation_model_uri="model://sota/2026",
        wasm_sandbox_profile="strict",
        verification_assertion="assert tool.execute() is not None",
        max_synthesis_time_ms=5000,
    )
    assert config.generation_model_uri == "model://sota/2026"
    assert config.wasm_sandbox_profile == "strict"
    assert config.verification_assertion == "assert tool.execute() is not None"
    assert config.max_synthesis_time_ms == 5000


def test_jit_tool_synthesis_config_invalid_profile() -> None:
    """Test that wasm_sandbox_profile must be a valid Literal."""
    with pytest.raises(ValidationError, match=r"Input should be 'strict', 'network-enabled' or 'fs-read-only'"):
        JITToolSynthesisConfig(
            generation_model_uri="model://sota/2026",
            wasm_sandbox_profile="invalid_profile",  # type: ignore[arg-type]
            verification_assertion="assert tool.execute() is not None",
            max_synthesis_time_ms=5000,
        )


def test_jit_tool_synthesis_config_invalid_time() -> None:
    """Test that max_synthesis_time_ms must be strictly positive."""
    with pytest.raises(ValidationError, match=r"Input should be greater than 0"):
        JITToolSynthesisConfig(
            generation_model_uri="model://sota/2026",
            wasm_sandbox_profile="strict",
            verification_assertion="assert tool.execute() is not None",
            max_synthesis_time_ms=0,
        )


def test_semantic_toolchain_valid_without_fallback() -> None:
    """Test successful instantiation of SemanticToolchain without fallback."""
    toolchain = SemanticToolchain(
        macro_intent_hash="0xabcd1234",
        discovered_tool_uris=["tool://math/add", "tool://math/subtract"],
        similarity_threshold=0.85,
        load_strategy="lazy_eval",
    )
    assert toolchain.macro_intent_hash == "0xabcd1234"
    assert toolchain.discovered_tool_uris == ["tool://math/add", "tool://math/subtract"]
    assert toolchain.similarity_threshold == 0.85
    assert toolchain.load_strategy == "lazy_eval"
    assert toolchain.jit_synthesis_fallback is None


def test_semantic_toolchain_valid_with_fallback() -> None:
    """Test successful instantiation of a complex SemanticToolchain with a JIT fallback."""
    fallback = JITToolSynthesisConfig(
        generation_model_uri="model://sota/2026",
        wasm_sandbox_profile="network-enabled",
        verification_assertion="return True",
        max_synthesis_time_ms=10000,
    )

    toolchain = SemanticToolchain(
        macro_intent_hash="0xdeadbeef",
        discovered_tool_uris=[],
        similarity_threshold=0.9,
        load_strategy="eager_mount",
        jit_synthesis_fallback=fallback,
    )
    assert toolchain.similarity_threshold == 0.9
    assert toolchain.load_strategy == "eager_mount"
    assert toolchain.jit_synthesis_fallback is not None
    assert toolchain.jit_synthesis_fallback.generation_model_uri == "model://sota/2026"


def test_semantic_toolchain_invalid_bounds() -> None:
    """Test that similarity_threshold validates its bounds."""
    with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
        SemanticToolchain(
            macro_intent_hash="0x1111",
            discovered_tool_uris=[],
            similarity_threshold=-0.5,  # Below 0.0
            load_strategy="ephemeral",
        )

    with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
        SemanticToolchain(
            macro_intent_hash="0x1111",
            discovered_tool_uris=[],
            similarity_threshold=1.01,  # Above 1.0
            load_strategy="ephemeral",
        )


def test_semantic_toolchain_invalid_strategy() -> None:
    """Test that load_strategy must be a valid Literal."""
    with pytest.raises(ValidationError, match=r"Input should be 'lazy_eval', 'eager_mount' or 'ephemeral'"):
        SemanticToolchain(
            macro_intent_hash="0x1111",
            discovered_tool_uris=[],
            similarity_threshold=0.5,
            load_strategy="invalid_strategy",  # type: ignore[arg-type]
        )
