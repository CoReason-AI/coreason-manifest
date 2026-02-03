# Runtime Deployment Configuration

## Overview

The **Runtime Deployment Configuration** implements the "Zero-Surprise Deployment" contract. It allows agent developers to explicitly declare the infrastructure requirements (secrets, hardware resources, scaling strategies) necessary for their agent to run reliably.

## Rationale: Zero-Surprise Deployments

Previously, agent dependencies like API keys or specific hardware requirements were often hidden in code or `.env` files, leading to runtime crashes ("Works on my machine, fails in Prod").

By making these requirements explicit in the Manifest, the Orchestration Platform (e.g., K8s, Lambda, MACO) can:
1.  **Pre-flight Validate**: Refuse to start the agent if required secrets or resources are missing.
2.  **Auto-Provision**: Automatically allocate the requested CPU/Memory.
3.  **Secure**: Integrate with secret managers (Vault, AWS Secrets Manager) based on `provider_hint`s.

## Configuration Schema

The `DeploymentConfig` model is integrated into the root `AgentDefinition` under the `deployment` field.

### 1. Environment Variables & Secrets (`SecretReference`)

Defines the external values the agent needs.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `key` | `str` | **Required** | The name of the environment variable (e.g., `OPENAI_API_KEY`). |
| `description` | `str` | **Required** | Human-readable explanation of why this secret is needed. |
| `required` | `bool` | `True` | Whether the agent can start without this variable. |
| `provider_hint` | `str` | `None` | Hint for the secret provider (e.g., `aws-secrets-manager`, `vault`). |

### 2. Resource Limits (`ResourceLimits`)

Defines the hardware constraints.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `cpu_cores` | `float` | `None` | CPU limit (e.g., `0.5` or `2.0`). |
| `memory_mb` | `int` | `None` | RAM limit in Megabytes. |
| `timeout_seconds` | `int` | `60` | Execution time limit. |

### 3. Deployment Strategy (`DeploymentConfig`)

The top-level configuration.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `env_vars` | `List[SecretReference]` | **Required** | List of required secrets/vars. |
| `resources` | `ResourceLimits` | `None` | Hardware constraints. |
| `scaling_strategy` | `Literal` | `serverless` | Strategy: `serverless` (scale-to-zero) or `dedicated` (always on). |
| `concurrency_limit` | `int` | `None` | Max simultaneous requests per instance. |

## Example

```yaml
deployment:
  scaling_strategy: "serverless"
  concurrency_limit: 10

  resources:
    cpu_cores: 1.0
    memory_mb: 2048
    timeout_seconds: 120

  env_vars:
    - key: "OPENAI_API_KEY"
      description: "Required for the main LLM inference."
      required: true
      provider_hint: "vault"

    - key: "DATABASE_URL"
      description: "Connection string for the vector store."
      required: true

    - key: "DEBUG_MODE"
      description: "Enable verbose logging."
      required: false
      provider_hint: "env"
```

## Benefits

*   **infrastructure-Aware**: The manifest is now a complete blueprint for execution, not just logic.
*   **Validation**: Orchestrators can block deployment if requirements (like expensive GPU availability) cannot be met.
*   **Security**: Secrets are referenced by key, never hardcoded values.
