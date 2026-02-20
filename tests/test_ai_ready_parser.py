import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.exceptions import DomainValidationError
from coreason_manifest.spec.core.manifest import Manifest
from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow

def test_auto_heal_markdown() -> None:
    """
    Test that markdown JSON is automatically healed.
    """
    raw_json = """
    {
        "kind": "LinearFlow",
        "metadata": {
            "name": "test",
            "version": "1.0",
            "description": "test",
            "tags": []
        },
        "sequence": []
    }
    """

    manifest_input = f"""
    Here is the manifest:
    ```json
    {{
        "manifest_version": "v1",
        "flow": {raw_json}
    }}
    ```
    """

    # Test auto-heal
    # Pass auto_heal in context (or rely on Loader usually, but here we test model directly)
    # Since we updated Manifest.model_validate to look at context
    manifest = Manifest.model_validate(manifest_input, context={"auto_heal": True})
    assert isinstance(manifest.flow, LinearFlow)
    assert manifest.flow.kind == "LinearFlow"
    assert manifest.recovery_receipt is not None
    # Flexible assertion on mutation message
    mutations = str(manifest.recovery_receipt.mutations)
    assert "Stripped markdown code blocks" in mutations

def test_diagnosis_report_missing_field() -> None:
    """
    Test that validation error produces a DiagnosisReport and Prompt.
    """
    input_data = {
        "manifest_version": "v1",
        "flow": {
            "kind": "LinearFlow",
            "metadata": {
                # Missing name
                "version": "1.0",
                "description": "test",
                "tags": []
            },
            "sequence": []
        }
    }

    with pytest.raises(ValidationError) as excinfo:
        Manifest.model_validate(input_data)

    # Manually wrap the error as we would in a parser entrypoint
    domain_err = DomainValidationError.from_pydantic(excinfo.value, root_model=Manifest)

    assert domain_err.diagnosis is not None
    print(f"Diagnosis Path: {domain_err.diagnosis.json_path}")

    prompt = domain_err.to_prompt()
    print(f"Generated Prompt:\n{prompt}")

    assert "## Error Diagnosis" in prompt
    assert "## Instruction" in prompt
    assert "metadata" in domain_err.diagnosis.json_path or "name" in domain_err.diagnosis.json_path

def test_diagnosis_report_typo() -> None:
    """
    Test that typo in key triggers Levenshtein suggestion.
    """
    input_data = {
        "manifest_version": "v1",
        "flow": {
            "kind": "LinearFlow",
            "metadata": {
                "nmae": "test", # Typo for 'name'
                "version": "1.0",
                "description": "test",
                "tags": []
            },
            "sequence": []
        }
    }

    with pytest.raises(ValidationError) as excinfo:
        Manifest.model_validate(input_data)

    domain_err = DomainValidationError.from_pydantic(excinfo.value, root_model=Manifest)

    assert domain_err.diagnosis is not None
    path = domain_err.diagnosis.json_path

    fix = domain_err.diagnosis.suggested_fix
    print(f"Path: {path}, Fix: {fix}")

    assert fix is not None
    # Should suggest 'nmae' if missing 'name' or suggest 'name' if extra 'nmae'
    assert "nmae" in fix or "name" in fix

def test_auto_heal_trailing_commas() -> None:
    # Construct invalid JSON with trailing comma
    invalid_json = """
    {
        "manifest_version": "v1",
        "flow": {
            "kind": "LinearFlow",
            "metadata": {
                "name": "test",
                "version": "1.0",
                "description": "test",
                "tags": [],
            },
            "sequence": [],
        }
    }
    """
    manifest = Manifest.model_validate(invalid_json, context={"auto_heal": True})
    assert isinstance(manifest.flow, LinearFlow)
    assert manifest.flow.kind == "LinearFlow"
    assert manifest.recovery_receipt is not None
    assert "Stripped trailing commas" in str(manifest.recovery_receipt.mutations)

def test_auto_heal_booleans() -> None:
    raw_json = """
    {
        "kind": "GraphFlow",
        "metadata": {
            "name": "test",
            "version": "1.0",
            "description": "test",
            "tags": []
        },
        "interface": {
            "inputs": {"json_schema": {}},
            "outputs": {"json_schema": {}}
        },
        "blackboard": {
            "variables": {},
            "persistence": "true"
        },
        "graph": {
            "nodes": {"start": {"id": "start", "type": "placeholder", "metadata": {}, "required_capabilities": []}},
            "edges": [],
            "entry_point": "start"
        }
    }
    """

    manifest_input = f"""
    {{
        "manifest_version": "v1",
        "flow": {raw_json}
    }}
    """

    manifest = Manifest.model_validate(manifest_input, context={"auto_heal": True})
    assert isinstance(manifest.flow, GraphFlow)
    assert manifest.flow.blackboard is not None
    assert manifest.flow.blackboard.persistence is True
    assert manifest.recovery_receipt is not None
    assert "Coerced stringified booleans" in str(manifest.recovery_receipt.mutations)
