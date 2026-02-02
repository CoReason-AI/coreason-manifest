# Runtime Deployment Configuration

## Overview

The **Runtime Deployment Configuration** feature introduces a new "Deployment" layer to the Agent Manifest. This allows agent developers to specify *how* their agent should be hosted, scaled, and accessed directly within the manifest, replacing the need for external Infrastructure-as-Code (IaC) files like Terraform or Helm for basic deployment parameters.

## Rationale

Previously, the Agent Manifest defined *what* the agent is (metadata, capabilities) and *how it thinks* (runtime config, topology). However, it lacked information on *how to run it*. This separation meant that deploying an agent required two distinct artifacts: the manifest and a separate deployment script.

By including deployment configuration in the manifest, the Agent Definition becomes a self-contained **"deployable unit"**. The Execution Engine (MACO) or a Platform Orchestrator can read this manifest and automatically:
1.  Spin up the correct server container (e.g., FastAPI for HTTP, gRPC server).
2.  Configure network routes and ports.
3.  Apply autoscaling policies based on expected load.
4.  Inject necessary environment variables.

## Configuration Schema

The new `DeploymentConfig` model is integrated into the root `AgentDefinition` under the `deployment` field.

### Fields

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `protocol` | `Protocol` (Enum) | `http_sse` | The communication protocol (`http_sse`, `websocket`, `grpc`). |
| `port` | `int` | `8000` | The port the agent server binds to. |
| `route_prefix` | `str` | `/assist` | URL prefix for the agent endpoints. |
| `scaling_min_instances` | `int` | `0` | Minimum number of replicas (0 allows scale-to-zero). |
| `scaling_max_instances` | `int` | `1` | Maximum number of replicas. |
| `timeout_seconds` | `int` | `60` | Hard timeout for processing requests. |
| `env_vars` | `Dict[str, str]` | `{}` | Static environment variables to inject into the container. |

### Example

```yaml
deployment:
  protocol: "http_sse"
  port: 8080
  route_prefix: "/api/v1/agent"
  scaling_min_instances: 1
  scaling_max_instances: 5
  timeout_seconds: 30
  env_vars:
    LOG_LEVEL: "INFO"
```

## Benefits

*   **Portability**: The agent carries its own deployment constraints. You can move the manifest between environments (Dev, Stage, Prod) or different cloud providers, and the orchestrator respects the settings.
*   **Simplification**: Removes the need for developers to learn Kubernetes manifests or Helm charts for standard agent deployments.
*   **Automation**: Enables "Click to Deploy" functionality where the platform simply reads the manifest and provisions resources accordingly.
