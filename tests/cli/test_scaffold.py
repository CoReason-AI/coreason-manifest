import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from coreason_manifest.cli.main import app
from coreason_manifest.cli.test_bootstrapper import camel_to_snake

runner = CliRunner()


def test_camel_to_snake() -> None:
    assert camel_to_snake("VectorSearch") == "vector_search"
    assert camel_to_snake("camelCase") == "camel_case"


def test_class_inject_transformer_resolve_type() -> None:
    # resolve_type is defined as a nested function inside `mcp`, we can test it by running `mcp` with a mocked input.
    # Alternatively we can extract it if needed, but for now we skip testing it directly.
    pass


@patch("coreason_manifest.cli.test_bootstrapper.generate_test")
@patch("pathlib.Path.write_text")
@patch("pathlib.Path.read_text")
@patch("pathlib.Path.exists")
@patch("builtins.open")
def test_scaffold_mcp_success(
    mock_open: MagicMock,
    mock_exists: MagicMock,
    mock_read_text: MagicMock,
    mock_write_text: MagicMock,
    mock_generate_test: MagicMock,
) -> None:
    mock_exists.return_value = True

    # Mock schema
    mock_schema = {
        "$defs": {
            "TestCapability": {
                "properties": {
                    "some_field": {"type": "string", "description": "A field description"},
                    "some_int": {"type": "integer"},
                    "some_num": {"type": "number"},
                    "some_bool": {"type": "boolean"},
                    "some_null": {"type": "null"},
                    "some_array": {"type": "array", "items": {"type": "string"}},
                    "some_obj": {"type": "object", "additionalProperties": {"type": "integer"}},
                    "some_ref": {"$ref": "#/$defs/OtherModel"},
                    "some_union": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "some_union_single": {"anyOf": [{"type": "string"}]},
                    "some_union_empty": {"anyOf": []},
                    "some_any": {},
                    "some_obj_default": {"type": "object"},
                }
            }
        }
    }

    mock_file = MagicMock()
    mock_file.read.return_value = json.dumps(mock_schema)
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock original ontology.py content
    mock_read_text.return_value = """
class CoreasonBaseState:
    pass

CoreasonBaseState.model_rebuild()
"""

    result = runner.invoke(app, ["scaffold", "mcp", "TestCapability", "A test capability"])
    assert result.exit_code == 0
    assert "Successfully scaffolded TestCapability in ontology.py" in result.stdout
    assert "NOTICE: The generated schema extensions are governed by the Prosperity Public License" in result.stdout

    mock_write_text.assert_called_once()
    mock_generate_test.assert_called_once()
    args, _ = mock_generate_test.call_args
    assert args[0] == "TestCapability"
    fields = args[1]
    names = [f["name"] for f in fields]
    assert "some_field" in names
    assert "some_int" in names
    assert "some_num" in names
    assert "some_bool" in names
    assert "some_null" in names
    assert "some_array" in names
    assert "some_obj" in names
    assert "some_ref" in names
    assert "some_union" in names
    assert "some_union_single" in names
    assert "some_union_empty" in names
    assert "some_any" in names


@patch("pathlib.Path.exists")
def test_scaffold_mcp_missing_ontology(mock_exists: MagicMock) -> None:
    # Simulate missing ontology.py
    mock_exists.side_effect = [False, False]

    result = runner.invoke(app, ["scaffold", "mcp", "TestCapability", "A test capability"])
    assert result.exit_code == 1


@patch("pathlib.Path.write_text")
def test_test_bootstrapper(mock_write_text: MagicMock) -> None:
    from coreason_manifest.cli.test_bootstrapper import generate_test

    fields = [
        {"name": "some_int", "type": "int", "minimum": 0, "maximum": 10},
        {"name": "some_float", "type": "float", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
    ]

    generate_test("TestCapability", fields)

    mock_write_text.assert_called_once()
    content = mock_write_text.call_args[0][0]

    assert "def test_mcp_test_capability_fuzzing(instance: dict[str, Any]) -> None:" in content
    assert "assert obj.some_int is None or obj.some_int >= 0" in content
    assert "assert obj.some_int is None or obj.some_int <= 10" in content
    assert "assert obj.some_float is None or obj.some_float > 0.0" in content
    assert "assert obj.some_float is None or obj.some_float < 1.0" in content
