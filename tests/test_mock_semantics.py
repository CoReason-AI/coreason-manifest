from coreason_manifest.utils.mock import MockFactory


def test_mock_semantics_enum() -> None:
    factory = MockFactory(seed=42)
    # 1. Simple enum
    schema = {"enum": ["A", "B", "C"]}
    result = factory._generate_schema_data(schema)
    assert result in ["A", "B", "C"]


def test_mock_semantics_implicit_type() -> None:
    factory = MockFactory(seed=42)

    # 2. Implicit object
    schema_obj = {"properties": {"foo": {"type": "string"}}}
    result_obj = factory._generate_schema_data(schema_obj)
    assert isinstance(result_obj, dict)
    assert "foo" in result_obj
    assert result_obj["foo"] == "lorem ipsum"

    # 3. Implicit array
    schema_arr = {"items": {"type": "integer"}}
    result_arr = factory._generate_schema_data(schema_arr)
    assert isinstance(result_arr, list)
    if result_arr:
        assert isinstance(result_arr[0], int)

    # 4. Implicit string (fallback)
    schema_str = {"description": "just description"}
    result_str = factory._generate_schema_data(schema_str)
    assert result_str == "lorem ipsum"


def test_mock_semantics_ref_enum() -> None:
    # Test enum alongside $ref (enum takes precedence if present?
    # Wait, logic says inside $ref block enum check is added)
    # But wait, standard JSON Schema says $ref replaces everything.
    # However, my implementation added enum check INSIDE $ref block?
    # No, I added it inside `if "$ref" in schema and resolver:` block.
    # This implies that if a schema has both $ref and enum, enum is used and $ref is ignored/short-circuited?
    # Let's verify the code.

    # In code:
    # if "$ref" in schema and resolver:
    #     if "enum" in schema ...: return choice
    #     # else resolve ref

    # So if enum is present alongside $ref, it uses enum.
    # Note: Technically $ref ignores siblings in older specs, but modern spec allows siblings.
    # If the intention is that the node constraint overrides the ref, then this is correct.

    from unittest.mock import MagicMock

    factory = MockFactory(seed=42)
    resolver = MagicMock()

    schema = {"$ref": "#/defs/Foo", "enum": ["OVERRIDE"]}
    result = factory._generate_schema_data(schema, resolver=resolver)
    assert result == "OVERRIDE"
    # Ensure lookup NOT called
    resolver.lookup.assert_not_called()
