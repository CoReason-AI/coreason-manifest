# MACO Recipe Specification

The `RecipeManifest` acts as the **Executable Specification** for the MACO (Multi-Agent Coreason Orchestration) engine. It serves as the shared contract between the `coreason-maco` runtime (Engine) and the `coreason-maco-builder` (Visual Editor).

## Purpose

The Recipe Manifest defines:
1.  **Interface Contract**: The strict inputs and outputs of the workflow, allowing it to be treated as a black-box function.
2.  **Shared Memory**: The schema for the state that persists across steps.
3.  **Topology**: The directed graph of execution steps (`Nodes`) and transition logic (`Edges`).
4.  **Design-Time Data**: Metadata required for the Builder UI (e.g., coordinates) that is ignored by the runtime.

## Schema Reference

The root object is `RecipeManifest`, which inherits from `CoReasonBaseModel` (strictly validated, frozen by default).

### RecipeManifest

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier for the recipe. |
| `version` | `VersionStr` | Semantic version (e.g., `1.0.0`). |
| `name` | `str` | Human-readable name. |
| `description` | `str` | Detailed description of the workflow logic. |
| `interface` | `RecipeInterface` | Defines the Input/Output contract. |
| `state` | `StateDefinition` | Defines the internal memory schema and persistence settings. |
| `parameters` | `Dict[str, Any]` | Build-time configuration constants (e.g. model tiers, thresholds). |
| `topology` | `GraphTopology` | The execution graph (nodes and edges). |
| `integrity_hash` | `Optional[str]` | SHA256 hash of the canonical topology. Enforced by Builder, verified by Runtime. |
| `metadata` | `Dict[str, Any]` | Design-time data (UI coordinates, draft status, user info). |

### RecipeInterface

| Field | Type | Description |
| :--- | :--- | :--- |
| `inputs` | `Dict[str, Any]` | JSON Schema defining valid entry arguments. |
| `outputs` | `Dict[str, Any]` | JSON Schema defining the guaranteed structure of the final result. |

### StateDefinition

Defines the "Memory" of the agent or workflow.

| Field | Type | Description |
| :--- | :--- | :--- |
| `schema` | `Dict[str, Any]` | JSON Schema of the keys available in the shared memory. (Note: use `schema_` argument in Python constructor). |
| `persistence` | `Literal["ephemeral", "persistent"]` | Configuration for state durability. |

### GraphTopology

The core execution logic.

| Field | Type | Description |
| :--- | :--- | :--- |
| `nodes` | `List[Node]` | List of polymorphic nodes. |
| `edges` | `List[Edge]` | List of edges connecting the nodes. |
| `state_schema` | `Optional[StateDefinition]` | Redundant definition of state for the graph context. |

**Validation**: The topology enforces **referential integrity**. Every `source_node_id` and `target_node_id` in edges must correspond to an `id` in the `nodes` list.

## Nodes

Nodes are polymorphic objects distinguished by their `type` field.

### Common Fields (All Nodes)
- `id` (`str`): Unique identifier.
- `metadata` (`Dict[str, Any]`): Operational context (cost tracking, SLAs).
- `visual` (`VisualMetadata`): UI data (label, x/y coordinates, icon).
- `council_config` (`Optional[CouncilConfig]`): Configuration for architectural triangulation (voting).

### Node Types

#### 1. AgentNode (`type="agent"`)
Executes an Atomic Agent from the registry.
- `agent_name`: Name of the agent to invoke.
- `system_prompt`: (Optional) Override system prompt.
- `overrides`: (Optional) Runtime overrides (temperature, etc.).

#### 2. HumanNode (`type="human"`)
Pauses execution and waits for external signal.
- `timeout_seconds`: (Optional) Max wait time.

#### 3. LogicNode (`type="logic"`)
Executes pure Python code (sandboxed).
- `code`: The Python script to execute.

#### 4. RecipeNode (`type="recipe"`)
Executes a sub-workflow (nested recipe).
- `recipe_id`: ID of the child recipe.
- `input_mapping`: Maps parent state keys to child inputs.
- `output_mapping`: Maps child outputs to parent state.

#### 5. MapNode (`type="map"`)
Parallel execution (Map-Reduce).
- `items_path`: Dot-notation path to a list in the state.
- `processor_node_id`: ID of the node/subgraph to run for each item.
- `concurrency_limit`: Max parallel threads.

## Edges

Edges define the control flow.

### Standard Edge
A direct transition.
- `source_node_id`: Start node.
- `target_node_id`: End node.
- `condition`: (Optional) Python expression that must evaluate to True.

### ConditionalEdge (Dynamic Routing)
Routes to one of multiple targets based on logic.
- `source_node_id`: Start node.
- `router_logic`: A reference to a python function (e.g., `"my_module.router"`) or a `RouterExpression` object. **Note**: Raw code strings (lambdas) are not allowed for security reasons.
- `mapping`: Dictionary mapping the router's return value (e.g., `"approved"`) to a target Node ID.

## Example

The following example demonstrates how to programmatically construct a valid `RecipeManifest` using the Python SDK.

### Python Construction

```python
from coreason_manifest import (
    RecipeManifest, GraphTopology, AgentNode, Edge
)
from coreason_manifest.recipes import RecipeInterface
from coreason_manifest.definitions.topology import (
    HumanNode, ConditionalEdge, StateDefinition
)
import json

def main():
    # 1. Define Nodes
    agent_node = AgentNode(
        id="step_1_research",
        type="agent",
        agent_name="ResearchAgent",
        visual={"label": "Research Phase", "x_y_coordinates": [100.0, 200.0]},
        overrides={"temperature": 0.2}
    )

    human_node = HumanNode(
        id="step_2_approve",
        type="human",
        timeout_seconds=3600,
        visual={"label": "Manager Approval", "x_y_coordinates": [300.0, 200.0]},
        metadata={"cost_center": "marketing"}
    )

    # Target nodes for branching (must exist in topology)
    publish_node = AgentNode(
        id="step_3_publish",
        type="agent",
        agent_name="PublisherAgent",
        visual={"label": "Publish Content"}
    )

    revise_node = AgentNode(
        id="step_1_revise",
        type="agent",
        agent_name="EditorAgent",
        visual={"label": "Revise Content"}
    )

    # 2. Define Dynamic Routing
    # Note: router_logic must be a reference to a function (e.g. "module.function")
    # or a structured RouterExpression. It cannot be raw python code string.
    router = ConditionalEdge(
        source_node_id="step_2_approve",
        router_logic="workflows.utils.approval_router",
        mapping={
            "approved": "step_3_publish",
            "rejected": "step_1_revise"
        }
    )

    # 3. Define Interface (Inputs/Outputs)
    interface = RecipeInterface(
        inputs={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The research topic"}
            },
            "required": ["topic"]
        },
        outputs={
            "type": "object",
            "properties": {
                "final_report": {"type": "string"}
            }
        }
    )

    # 4. Define State (Memory)
    # Note: Use 'schema_' kwarg or 'schema' alias if populating by dict.
    # In python constructor, we use the field name 'schema_'.
    state_def = StateDefinition(
        schema_={
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "research_notes": {"type": "array"},
                "draft": {"type": "string"},
                "approved": {"type": "boolean"},
                "final_report": {"type": "string"}
            }
        },
        persistence="ephemeral"
    )

    # 5. Create Manifest
    recipe = RecipeManifest(
        id="research_approval_workflow",
        version="1.0.0",
        name="Research & Approval Workflow",
        description="A mixed-initiative workflow for researching and publishing content.",
        interface=interface,
        state=state_def,
        parameters={"model_tier": "gpt-4"},
        topology=GraphTopology(
            nodes=[agent_node, human_node, publish_node, revise_node],
            edges=[
                Edge(source_node_id="step_1_research", target_node_id="step_2_approve"),
                router,
                # Edges to loop back or finish
                Edge(source_node_id="step_1_revise", target_node_id="step_2_approve"),
            ],
            state_schema=state_def
        ),
        metadata={
            "created_by": "user_123",
            "last_modified": "2023-10-27T10:00:00Z"
        }
    )

    # Dump to JSON
    # by_alias=True is crucial for fields like 'schema_' -> 'schema'
    json_output = recipe.model_dump_json(indent=2, by_alias=True)
    print(json_output)

if __name__ == "__main__":
    main()
```

### JSON Representation

The resulting JSON matches the wire format exchanged between Builder and Engine.

```json
{
  "id": "research_approval_workflow",
  "version": "1.0.0",
  "name": "Research & Approval Workflow",
  "description": "A mixed-initiative workflow for researching and publishing content.",
  "interface": {
    "inputs": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string",
          "description": "The research topic"
        }
      },
      "required": [
        "topic"
      ]
    },
    "outputs": {
      "type": "object",
      "properties": {
        "final_report": {
          "type": "string"
        }
      }
    }
  },
  "state": {
    "schema": {
      "type": "object",
      "properties": {
        "topic": {
          "type": "string"
        },
        "research_notes": {
          "type": "array"
        },
        "draft": {
          "type": "string"
        },
        "approved": {
          "type": "boolean"
        },
        "final_report": {
          "type": "string"
        }
      }
    },
    "persistence": "ephemeral"
  },
  "parameters": {
    "model_tier": "gpt-4"
  },
  "topology": {
    "nodes": [
      {
        "id": "step_1_research",
        "type": "agent",
        "agent_name": "ResearchAgent",
        "visual": {
          "label": "Research Phase",
          "x_y_coordinates": [100.0, 200.0]
        },
        "overrides": {
          "temperature": 0.2
        }
      },
      {
        "id": "step_2_approve",
        "type": "human",
        "timeout_seconds": 3600,
        "visual": {
          "label": "Manager Approval",
          "x_y_coordinates": [300.0, 200.0]
        },
        "metadata": {
          "cost_center": "marketing"
        }
      },
      {
        "id": "step_3_publish",
        "type": "agent",
        "agent_name": "PublisherAgent",
        "visual": {
          "label": "Publish Content"
        }
      },
      {
        "id": "step_1_revise",
        "type": "agent",
        "agent_name": "EditorAgent",
        "visual": {
          "label": "Revise Content"
        }
      }
    ],
    "edges": [
      {
        "source_node_id": "step_1_research",
        "target_node_id": "step_2_approve"
      },
      {
        "source_node_id": "step_2_approve",
        "router_logic": "workflows.utils.approval_router",
        "mapping": {
          "approved": "step_3_publish",
          "rejected": "step_1_revise"
        }
      },
      {
        "source_node_id": "step_1_revise",
        "target_node_id": "step_2_approve"
      }
    ],
    "state_schema": {
      "schema": {
        "type": "object",
        "properties": {
          "topic": {
            "type": "string"
          },
          "research_notes": {
            "type": "array"
          },
          "draft": {
            "type": "string"
          },
          "approved": {
            "type": "boolean"
          },
          "final_report": {
            "type": "string"
          }
        }
      },
      "persistence": "ephemeral"
    }
  },
  "integrity_hash": null,
  "metadata": {
    "created_by": "user_123",
    "last_modified": "2023-10-27T10:00:00Z"
  }
}
```
