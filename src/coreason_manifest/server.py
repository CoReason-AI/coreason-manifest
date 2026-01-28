from contextlib import asynccontextmanager
from importlib import resources
from pathlib import Path
from typing import AsyncIterator, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from coreason_manifest.engine import ManifestConfig, ManifestEngineAsync
from coreason_manifest.errors import ManifestSyntaxError, PolicyViolationError


# Response Model
class ValidationResponse(BaseModel):
    valid: bool
    agent_id: Optional[str] = None
    version: Optional[str] = None
    policy_violations: List[str] = Field(default_factory=list)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Locate policies
    policy_path: Optional[Path] = None
    tbom_path: Optional[Path] = None

    # 1. Check local directory (Docker runtime with COPY or relative dev path)
    # In Docker we will COPY to /app/policies/ or ./policies/ relative to WORKDIR
    # We'll check common locations.
    possible_dirs = [
        Path("policies"),
        Path("/app/policies"),
        Path("src/coreason_manifest/policies"),  # Dev from root
    ]

    for d in possible_dirs:
        if (d / "compliance.rego").exists():
            policy_path = d / "compliance.rego"
            if (d / "tbom.json").exists():
                tbom_path = d / "tbom.json"
            break

    # 2. Fallback to package resources
    resource_context = None
    if not policy_path:
        try:
            # Check if it exists as a resource
            ref = resources.files("coreason_manifest.policies").joinpath("compliance.rego")
            if ref.is_file():
                resource_context = resources.as_file(ref)
                policy_path = resource_context.__enter__()
                # Check for TBOM in same dir if possible, or ignore for fallback
        except Exception:
            pass

    # If still not found, fail.
    if not policy_path:
        raise RuntimeError("Could not locate compliance.rego policy file.")

    config = ManifestConfig(
        policy_path=policy_path,
        tbom_path=tbom_path,
        opa_path="opa",  # Assumes OPA is in PATH (installed via Dockerfile)
    )

    engine = ManifestEngineAsync(config)

    try:
        async with engine:
            app.state.engine = engine
            yield
    finally:
        if resource_context:
            resource_context.__exit__(None, None, None)


app = FastAPI(lifespan=lifespan)


@app.post("/validate", response_model=ValidationResponse)  # type: ignore[misc]
async def validate_manifest(request: Request) -> Union[ValidationResponse, JSONResponse]:
    engine: ManifestEngineAsync = app.state.engine

    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None

    try:
        agent_def = await engine.validate_manifest_dict(raw_body)
        return ValidationResponse(
            valid=True,
            agent_id=str(agent_def.metadata.id),
            version=agent_def.metadata.version,
            policy_violations=[],
        )
    except ManifestSyntaxError as e:
        # Return 422 with the error
        resp = ValidationResponse(valid=False, policy_violations=[f"Syntax Error: {str(e)}"])
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=resp.model_dump())
    except PolicyViolationError as e:
        resp = ValidationResponse(valid=False, policy_violations=e.violations)
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=resp.model_dump())


@app.get("/health")  # type: ignore[misc]
async def health_check() -> dict[str, str]:
    engine: ManifestEngineAsync = app.state.engine
    policy_version = "unknown"
    try:
        import hashlib

        # policy_path is guaranteed to exist by lifespan check
        policy_path = Path(engine.config.policy_path)
        if policy_path.exists():
            with open(policy_path, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()[:8]
            policy_version = digest
    except Exception:
        pass

    return {"status": "active", "policy_version": policy_version}
