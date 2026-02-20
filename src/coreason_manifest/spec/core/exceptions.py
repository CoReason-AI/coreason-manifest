import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from coreason_manifest.spec.interop.compliance import ComplianceReport, RemediationAction
from coreason_manifest.utils.string_utils import levenshtein_distance


def map_pydantic_type_to_python(pydantic_err_type: str) -> str:
    """Translates internal Pydantic error signatures to human/LLM readable types."""
    mapping = {
        "string_type": "str",
        "dict_type": "dict",
        "list_type": "list",
        "bool_type": "bool",
        "int_type": "int",
        "float_type": "float",
        "missing": "Required Field",
        "value_error.missing": "Required Field"
    }
    # Fallback to the raw string if not mapped, removing generic prefixes
    return mapping.get(pydantic_err_type, pydantic_err_type.replace("type_error.", ""))


class DiagnosisReport(BaseModel):
    """
    SOTA: Structured diagnosis of a validation error.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    json_path: str = Field(..., description="JSON pointer to the error location (e.g. #/nodes/0/timeout)")
    invalid_value: Any = Field(..., description="The value that caused the error.")
    expected_type: str = Field(..., description="Description of the expected type/schema.")
    suggested_fix: str | None = Field(None, description="Auto-generated fix suggestion.")


class DomainValidationError(ValueError):
    """
    A domain-specific validation error that includes structured diagnostics.
    """

    def __init__(
        self,
        message: str,
        report: ComplianceReport | None = None,
        remediation: RemediationAction | None = None,
        diagnosis: DiagnosisReport | None = None,
    ):
        super().__init__(message)
        self.report = report
        self.remediation = remediation
        self.diagnosis = diagnosis

    def __str__(self) -> str:
        base_msg = super().__str__()
        extras = []
        if self.remediation:
            # Directive 5: Serialize remediation payload so it survives Pydantic exception masking
            payload = json.dumps(self.remediation.model_dump())
            extras.append(f"[Remediation: {self.remediation.description}] [Payload: {payload}]")

        if self.diagnosis:
            extras.append(f"[Diagnosis: {self.diagnosis.model_dump_json()}]")

        if extras:
            return f"{base_msg} {' '.join(extras)}"
        return base_msg

    def to_prompt(self) -> str:
        """
        Generates a few-shot prompt for an LLM to fix the error.
        """
        prompt = f"""## Error Diagnosis
The parser encountered an error at `{self.diagnosis.json_path if self.diagnosis else "unknown location"}`.

**Error Message:** {super().__str__()}

"""
        if self.diagnosis:
            prompt += f"""**Invalid Value:** `{self.diagnosis.invalid_value}`
**Expected Type:** {self.diagnosis.expected_type}
"""
            if self.diagnosis.suggested_fix:
                prompt += f"**Suggestion:** {self.diagnosis.suggested_fix}\n"

        prompt += "\n## Instruction\nPlease correct the JSON structure based on the diagnosis above."
        return prompt

    @classmethod
    def from_pydantic(
        cls, err: ValidationError, root_model: type[BaseModel] | None = None
    ) -> "DomainValidationError":
        """
        Wraps a Pydantic ValidationError into a DomainValidationError with diagnosis.
        Attempts to suggest fixes for typos if root_model is provided.
        """
        e = err.errors()[0]

        # Construct JSON path
        loc_parts = [str(x) for x in e.get("loc", [])]
        json_path = "#/" + "/".join(loc_parts)

        msg = e.get("msg", "Validation error")
        typ = e.get("type", "unknown")
        invalid_val = e.get("input", "unknown")

        # Translate type
        human_readable_type = map_pydantic_type_to_python(typ)

        suggested_fix = None

        if typ == "missing":
            # Handle missing field typo detection
            missing_field = str(e.get("loc", [])[-1])
            if isinstance(invalid_val, dict):
                existing_keys = invalid_val.keys()
                best_match = None
                best_dist = float("inf")
                for k in existing_keys:
                    dist = levenshtein_distance(missing_field, k)
                    if dist < best_dist:
                        best_dist = dist
                        best_match = k

                if best_match and best_dist <= 3:
                    suggested_fix = f"Field '{missing_field}' is missing. Found similar key '{best_match}'. Did you mean to rename it?"

        elif typ == "extra_forbidden" and root_model:
            try:
                # Traverse JSON Schema to find valid keys
                schema = root_model.model_json_schema()
                defs = schema.get("$defs", {})

                current = schema
                path = e.get("loc", [])[:-1]  # path to parent of error

                for part in path:
                    # Resolve Ref
                    if "$ref" in current:
                        ref_name = current["$ref"].split("/")[-1]
                        current = defs.get(ref_name, {})

                    if isinstance(part, str):
                        props = current.get("properties", {})
                        if part in props:
                            current = props[part]
                        else:
                            # Could not traverse further
                            current = None
                            break
                    elif isinstance(part, int):
                        items = current.get("items", {})
                        if items:
                            current = items
                        else:
                            current = None
                            break

                if current:
                    if "$ref" in current:
                        ref_name = current["$ref"].split("/")[-1]
                        current = defs.get(ref_name, {})

                    valid_keys = list(current.get("properties", {}).keys())
                    invalid_key = str(e.get("loc", [])[-1])

                    best_match = None
                    best_dist = float("inf")

                    for k in valid_keys:
                        dist = levenshtein_distance(invalid_key, k)
                        if dist < best_dist:
                            best_dist = dist
                            best_match = k

                    # Heuristic threshold: <= 3 edits
                    if best_match and best_dist <= 3:
                        suggested_fix = f"Did you mean '{best_match}'?"

            except Exception:
                # Fallback if traversal fails complexity
                pass

        diagnosis = DiagnosisReport(
            json_path=json_path,
            invalid_value=invalid_val,
            expected_type=human_readable_type,
            suggested_fix=suggested_fix
        )

        return cls(f"Validation failed: {msg}", diagnosis=diagnosis)
