from pydantic import TypeAdapter

from coreason_manifest.spec.core.engines import (
    AttentionReasoning,
    BufferReasoning,
    EnsembleReasoning,
    ModelCriteria,
    ReasoningConfig,
)


def test_attention_reasoning_instantiation() -> None:
    # Test defaults
    attn = AttentionReasoning(model="gpt-4")
    assert attn.type == "attention"
    # Default is now "rephrase" for safety
    assert attn.attention_mode == "rephrase"
    assert attn.focus_model is None
    # BaseReasoning default
    assert attn.guided_decoding == "none"

    # Test with custom fields
    criteria = ModelCriteria(strategy="lowest_latency")
    attn = AttentionReasoning(
        model="gpt-4",
        attention_mode="extract",
        focus_model=criteria,
        guided_decoding="regex",
    )
    assert attn.attention_mode == "extract"
    assert isinstance(attn.focus_model, ModelCriteria)
    assert attn.focus_model.strategy == "lowest_latency"
    assert attn.guided_decoding == "regex"


def test_buffer_reasoning_instantiation() -> None:
    # Test defaults
    buf = BufferReasoning(model="gpt-4", template_collection="my_templates")
    assert buf.type == "buffer"
    assert buf.max_templates == 3
    assert buf.similarity_threshold == 0.75
    assert buf.template_collection == "my_templates"
    assert buf.learning_strategy == "read_only"

    # Test with custom fields
    buf = BufferReasoning(
        model="gpt-4",
        max_templates=10,
        similarity_threshold=0.9,
        template_collection="advanced_templates",
        learning_strategy="append_new",
    )
    assert buf.max_templates == 10
    assert buf.similarity_threshold == 0.9
    assert buf.template_collection == "advanced_templates"
    assert buf.learning_strategy == "append_new"


def test_reasoning_config_union_s2a_bot() -> None:
    # Use TypeAdapter to test parsing into the Union
    adapter: TypeAdapter[ReasoningConfig] = TypeAdapter(ReasoningConfig)

    # 1. AttentionReasoning
    data_attn = {
        "type": "attention",
        "model": "gpt-4",
        "attention_mode": "rephrase",
    }
    attn = adapter.validate_python(data_attn)
    assert isinstance(attn, AttentionReasoning)
    assert attn.attention_mode == "rephrase"

    # 2. BufferReasoning
    data_buf = {
        "type": "buffer",
        "model": "gpt-4",
        "template_collection": "vectors",
    }
    buf = adapter.validate_python(data_buf)
    assert isinstance(buf, BufferReasoning)
    assert buf.template_collection == "vectors"


def test_ensemble_reasoning_instantiation_in_union() -> None:
    # Test EnsembleReasoning instantiation and parsing via Union
    ens = EnsembleReasoning(model="gpt-4", aggregation="strongest_judge")
    assert ens.type == "ensemble"
    assert ens.aggregation == "strongest_judge"
    # Cascading Defaults check
    assert ens.agreement_threshold == 0.85
    assert ens.disagreement_threshold == 0.60
    assert ens.verification_mode == "ambiguous_only"
    assert ens.fast_comparison_mode == "embedding"

    # Ensure our Union parses it correctly
    adapter: TypeAdapter[ReasoningConfig] = TypeAdapter(ReasoningConfig)
    data = {"type": "ensemble", "model": "gpt-4"}
    parsed = adapter.validate_python(data)
    assert isinstance(parsed, EnsembleReasoning)
    assert parsed.type == "ensemble"
