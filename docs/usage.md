# Usage

`coreason-manifest` can be used in two modes: as a Python **Library** (CLI/Local) or as a **Compliance Microservice** (Server Mode).

## 1. Library Usage (CLI / Local)

This mode is used by the `adk` CLI and local development workflows. It performs full validation, including:

1.  **Schema Validation:** Checks against `agent.schema.json`.
2.  **Policy Enforcement:** Runs OPA policies (`compliance.rego`).
3.  **Integrity Check:** Hashes the source code directory and compares it to the `integrity_hash` in the manifest.

### Example

```python
from coreason_manifest import ManifestEngine, ManifestConfig, PolicyViolationError, IntegrityCompromisedError

# 1. Initialize configuration
# Ensure you point to the correct policy file location
config = ManifestConfig(policy_path="./policies/compliance.rego")
engine = ManifestEngine(config)

# 2. Load & Validate Agent Manifest
try:
    # This runs Schema Validation, Policy Enforcement, and Integrity Checks
    agent_def = engine.load_and_validate(
        manifest_path="./agents/my_agent/agent.yaml",
        source_dir="./agents/my_agent/src"
    )
    print(f"Agent {agent_def.metadata.name} (v{agent_def.metadata.version}) is valid.")

except PolicyViolationError as e:
    print(f"Compliance Failure: {e.violations}")

except IntegrityCompromisedError:
    print("CRITICAL: Code has been tampered with or does not match the manifest hash.")
```

## 2. Generating Manifests from Code

You can generate the `AgentInterface` part of the manifest by inspecting your Python agent function. This automatically handles system-injected parameters like `UserContext`, ensuring they are hidden from the public API schema.

```python
from coreason_manifest.loader import ManifestLoader
from coreason_identity import UserContext

def my_agent_function(query: str, user_context: UserContext) -> str:
    """A sample agent function requiring auth."""
    return f"Hello {user_context.user_id}, you asked: {query}"

# Generate Interface
interface = ManifestLoader.inspect_function(my_agent_function)

# 'query' is in inputs, 'user_context' is marked as injected
print(interface.model_dump_json(indent=2))
```

## 3. Server Mode (Compliance Microservice)

The **Compliance Microservice** (Service C) runs `coreason-manifest` as a FastAPI server. It is designed for centralized validation by services like `coreason-foundry` and `coreason-publisher`.

**Key Differences:**
*   Accepts the Agent Manifest as a JSON body (via HTTP POST).
*   **Skips Integrity Check:** Because the server does not have access to the client's local source code, it cannot verify the `integrity_hash`. It only validates the structure, schema, and policy compliance of the manifest itself.

### Running the Server

#### Using Docker (Recommended)

The Docker image comes pre-configured with OPA and the latest policies.

```bash
docker run -p 8000:8000 coreason/compliance-service:v0.4.0
```

#### Running Locally

Ensure `opa` is installed and in your PATH.

```bash
# Install server dependencies
poetry install

# Run the server
uvicorn coreason_manifest.server:app --host 0.0.0.0 --port 8000
```

### API Endpoints

#### `POST /validate`

Validates an Agent Manifest.

**Request:**
*   **Method:** `POST`
*   **Content-Type:** `application/json`
*   **Body:** The full Agent Manifest JSON object.

**Response (Success - 200 OK):**

```json
{
  "valid": true,
  "agent_id": "12345678-1234-5678-1234-567812345678",
  "version": "1.0.0",
  "policy_violations": []
}
```

**Response (Failure - 422 Unprocessable Entity):**

```json
{
  "valid": false,
  "policy_violations": [
    "Step description is too short.",
    "Compliance Violation: Library 'pandas' is not in the Trusted Bill of Materials (TBOM)."
  ]
}
```

#### `GET /health`

Checks the service status and active policy version.

**Response:**

```json
{
  "status": "active",
  "policy_version": "a1b2c3d4"
}
```
