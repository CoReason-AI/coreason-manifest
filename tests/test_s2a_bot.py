from pydantic import TypeAdapter

from coreason_manifest.spec.core.engines import (
    AttentionReasoning,
    BufferReasoning,
    ModelCriteria,
    ReasoningConfig,
)


def test_attention_reasoning_instantiation() -> None:
    # Test defaults
    attn = AttentionReasoning(model="gpt-4")
    assert attn.type == "attention"
    assert attn.attention_mode == "extract"
    assert attn.focus_model is None

    # Test with custom fields
    criteria = ModelCriteria(strategy="lowest_latency")
    attn = AttentionReasoning(
        model="gpt-4",
        attention_mode="rephrase",
        focus_model=criteria,
    )
    assert attn.attention_mode == "rephrase"
    assert isinstance(attn.focus_model, ModelCriteria)
    assert attn.focus_model.strategy == "lowest_latency"


def test_buffer_reasoning_instantiation() -> None:
    # Test defaults
    buf = BufferReasoning(model="gpt-4", template_collection="my_templates")
    assert buf.type == "buffer"
    assert buf.max_templates == 3
    assert buf.similarity_threshold == 0.75
    assert buf.template_collection == "my_templates"

    # Test with custom fields
    buf = BufferReasoning(
        model="gpt-4",
        max_templates=10,
        similarity_threshold=0.9,
        template_collection="advanced_templates",
    )
    assert buf.max_templates == 10
    assert buf.similarity_threshold == 0.9
    assert buf.template_collection == "advanced_templates"


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
