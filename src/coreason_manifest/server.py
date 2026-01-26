# Prosperity-3.0
"""FastAPI Server for the Compliance Microservice (Service M).

This module exposes the validation logic as a RESTful API.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from coreason_manifest.errors import (
    ManifestSyntaxError,
    PolicyViolationError,
)
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.policy import PolicyEnforcer
from coreason_manifest.validator import SchemaValidator


app = FastAPI(title="Coreason Compliance Service", version="1.0.0")

# --- Models ---

class ManifestValidationRequest(BaseModel):
    """Request body for manifest validation."""
    manifest: Dict[str, Any] = Field(..., description="The Agent Manifest JSON content.")

class ManifestValidationResponse(BaseModel):
    """Response body for manifest validation."""
    valid: bool = Field(..., description="Whether the manifest is valid and compliant.")
    tbom_id: Optional[str] = Field(None, description="The SHA256 integrity hash (TBOM ID) if valid.")
    errors: Optional[List[str]] = Field(None, description="List of validation errors or policy violations.")

# --- Dependencies ---

def get_policy_path() -> Path:
    """Determine the path to the policy file."""
    # Check env var first
    if "POLICY_PATH" in os.environ:
        return Path(os.environ["POLICY_PATH"])

    # Check relative to this file
    current_file = Path(__file__)
    # src/coreason_manifest/server.py -> src/coreason_manifest/policies/compliance.rego
    candidate = current_file.parent / "policies" / "compliance.rego"
    if candidate.exists():
        return candidate

    # Fallback for Docker /app/policies structure
    candidate = Path("/app/policies/compliance.rego")
    if candidate.exists():
        return candidate

    raise FileNotFoundError("Could not find compliance.rego policy file.")

schema_validator = SchemaValidator()

# We initialize PolicyEnforcer lazily or here.
policy_enforcer: Optional[PolicyEnforcer] = None
try:
    policy_path = get_policy_path()
    policy_enforcer = PolicyEnforcer(policy_path=policy_path, opa_path="opa")
except Exception as e:
    # Log warning but allow server to start (useful for tests/dev where opa might be missing)
    print(f"Warning: PolicyEnforcer failed to initialize: {e}")

# --- Endpoints ---

@app.post("/validate/manifest", response_model=ManifestValidationResponse)
async def validate_manifest(request: ManifestValidationRequest) -> ManifestValidationResponse:
    """Validate an Agent Manifest."""
    manifest = request.manifest
    errors: List[str] = []

    # 1. Schema Validation (Syntactic)
    try:
        schema_validator.validate(manifest)
    except ManifestSyntaxError as e:
        errors.append(f"Schema Error: {str(e)}")
        # Schema failure is fatal for further processing
        return ManifestValidationResponse(valid=False, errors=errors)

    # 2. Model Conversion (Semantic/Normalization)
    agent_def = None
    try:
        agent_def = ManifestLoader.load_from_dict(manifest)
    except ManifestSyntaxError as e:
        errors.append(f"Model Error: {str(e)}")
        return ManifestValidationResponse(valid=False, errors=errors)

    # 3. Policy Enforcement (Governance)
    if policy_enforcer:
        try:
            # PolicyEnforcer expects dict, we can pass the raw manifest or the normalized one.
            # Using normalized one (model dump) is safer as it includes defaults and correct types.
            normalized_data = agent_def.model_dump(mode="json")
            policy_enforcer.evaluate(normalized_data)
        except PolicyViolationError as e:
            errors.extend([f"Policy Violation: {v}" for v in e.violations])
        except Exception as e:
            # Runtime error in OPA
            errors.append(f"Policy Check Error: {str(e)}")
    else:
        # If policy enforcer is not available (e.g. no OPA), we assume failure for security.
        # However, for local dev without OPA, this blocks testing.
        # But in "Compliance Microservice", policy check is mandatory.
        errors.append("Policy Enforcement unavailable (OPA not found or configured).")

    if errors:
        return ManifestValidationResponse(valid=False, errors=errors)

    return ManifestValidationResponse(
        valid=True,
        tbom_id=agent_def.integrity_hash
    )

@app.get("/schema/latest")
async def get_schema() -> Dict[str, Any]:
    """Get the current Agent Manifest JSON Schema."""
    return schema_validator.schema
