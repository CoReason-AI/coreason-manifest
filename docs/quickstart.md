# Quick Start Guide

This guide will get you up and running with `coreason-manifest` in seconds. It focuses on the simplified `simple_agent` API, which allows you to define fully compliant agents with minimal boilerplate.

## Prerequisites

Ensure you have the package installed:

```bash
pip install coreason-manifest
```

## The "Hello World" Agent

The fastest way to define an agent is using the `simple_agent` shortcut. This creates a valid `ManifestV2` object with sensible defaults (single-step workflow, generic interface, standard role).

```python
from coreason_manifest import simple_agent, dump

# 1. Define the Agent
manifest = simple_agent(
    name="HelloAgent",
    prompt="You are a helpful assistant who speaks in haiku.",
    model="gpt-4o",
)

# 2. Export to YAML
yaml_output = dump(manifest)
print(yaml_output)
```

### Output

The above code generates a complete, compliant manifest:

```yaml
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: HelloAgent
  version: 0.1.0
interface:
  inputs:
    type: object
    additionalProperties: true
  outputs:
    type: object
    additionalProperties: true
definitions:
  HelloAgent:
    type: agent
    id: HelloAgent
    name: HelloAgent
    role: Assistant
    goal: Help the user
    backstory: You are a helpful assistant who speaks in haiku.
    model: gpt-4o
    tools: []
    # ... default capabilities ...
workflow:
  start: main
  steps:
    main:
      type: agent
      id: main
      agent: HelloAgent
```

## Adding Tools

You can easily attach tools by passing a list of Tool IDs or URIs.

```python
manifest = simple_agent(
    name="Researcher",
    prompt="Research the topic provided.",
    tools=["google-search", "wikipedia-api"]
)
```

## Customizing Role and Goal

If you need more specific metadata without writing the full boilerplate:

```python
manifest = simple_agent(
    name="SecurityBot",
    role="Security Auditor",
    goal="Identify vulnerabilities in code.",
    prompt="Scan the provided code snippet...",
    version="1.0.1"
)
```

## Next Steps

*   **[Usage Guide](usage.md)**: Learn how to manually construct complex manifests and workflows.
*   **[Builder SDK](builder_sdk.md)**: Use the fluent builder for more control over capabilities and schemas.
*   **[Core Documentation](index.md)**: Explore the full API reference.
