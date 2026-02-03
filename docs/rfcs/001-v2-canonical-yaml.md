# RFC 001: Coreason Manifest V2 - Canonical YAML

## Status
* **Proposed**
* **Target Version:** 2.0.0

## Summary
This RFC proposes a "Human-Centric" Canonical YAML format for Coreason Manifests, replacing the current "Machine-First" structure. The goal is to provide a unified source of truth for both the Runtime Engine and the Visual Builder.

## Motivation
Current V1 manifests use nested Pydantic models that are verbose and difficult to author by hand. The new format aims to be:
*   **Concise:** Easy to read and write.
*   **Topology-First:** Uses a linked-list style `next` pointer for simple flows, while supporting explicit edges for complex graphs.
*   **Tool-Agnostic:** Separates UI metadata (`x-design`) from runtime logic.

## Specification

### Root Structure
The root object follows a Kubernetes-style header.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "My Workflow"
  x-design:
    x: 0
    y: 0
definitions:
  # Reusable components
  my-agent:
    ...
workflow:
  start: "step-1"
  steps:
    step-1: ...
```

### Steps & Topology
Steps are defined in a flat dictionary under `workflow.steps`.
Topological connections are defined implicitly via the `next` field, or explicitly via `SwitchStep` cases.

#### Implicit Flow (Linked List)
Most steps support a `next` field pointing to the ID of the next step.

```yaml
step-1:
  type: "agent"
  agent: "researcher"
  next: "step-2"
```

#### Branching (Switch)
The `SwitchStep` replaces `next` with `cases` and `default`.

```yaml
step-2:
  type: "switch"
  cases:
    "result.score > 0.8": "publish"
    "result.score <= 0.8": "revise"
  default: "revise"
```

### UI Metadata (`x-design`)
Visual layout information is encapsulated in `x-design` (aliased from `design_metadata` in Python). This ensures separation of concerns.

```yaml
step-1:
  type: "agent"
  x-design:
    x: 100
    y: 200
    color: "blue"
    icon: "robot"
```

### Component Types

1.  **AgentStep (`type: agent`)**: Executes an AI Agent.
2.  **LogicStep (`type: logic`)**: Executes Python code.
3.  **CouncilStep (`type: council`)**: Aggregates multiple voters.
4.  **SwitchStep (`type: switch`)**: Routes execution.

## Example

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Document Review"
  x-design:
    x: 0
    y: 0
workflow:
  start: "draft"
  steps:
    draft:
      id: "draft"
      type: "agent"
      agent: "writer-agent"
      next: "review"
      x-design:
        x: 100
        y: 100

    review:
      id: "review"
      type: "council"
      voters: ["critic-1", "critic-2"]
      strategy: "consensus"
      next: "decide"
      x-design:
        x: 300
        y: 100

    decide:
      id: "decide"
      type: "switch"
      cases:
        "result == 'approved'": "publish"
      default: "draft"
      x-design:
        x: 500
        y: 100

    publish:
      id: "publish"
      type: "logic"
      code: "print('Published!')"
      x-design:
        x: 700
        y: 100
```

## Schema Generation
The JSON Schema is automatically generated from the Pydantic models in `src/coreason_manifest/v2/spec/definitions.py` using `scripts/generate_v2_schema.py`.
