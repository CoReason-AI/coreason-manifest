import pytest
from hypothesis import given, settings
from hypothesis_jsonschema import from_schema
from pydantic import ValidationError

from coreason_manifest.spec.ontology import TokenBurnReceipt

schema = TokenBurnReceipt.model_json_schema()


@settings(max_examples=10)
@given(from_schema(schema))
def test_fuzz_token_burn(payload):
    try:
        TokenBurnReceipt.model_validate(payload)
    except ValidationError:
        # Invalid fuzzed payloads are expected; this is an acceptable outcome.
        return
    except Exception as exc:
        pytest.fail(f"Unexpected exception type during validation: {exc!r}")
