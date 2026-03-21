import os
import sys
import json
import yaml
from pathlib import Path

def migrate_schema(schema: dict) -> dict:
    new_schema = {
        "type": "object",
        "properties": {
            "trace_context": {
                "type": "object",
                "properties": {
                    "trace_id": {"type": "string"},
                    "span_id": {"type": "string"},
                    "parent_span_id": {"type": "string"},
                    "causal_clock": {"type": "integer"}
                },
                "required": ["trace_id", "span_id", "causal_clock"]
            },
            "state_vector": {
                "type": "object",
                "properties": {
                    "read_only_context": {"type": "object"},
                    "mutable_memory": {"type": "object"},
                    "is_delta": {"type": "boolean"}
                },
                "required": ["read_only_context", "is_delta"]
            },
            "payload": schema
        },
        "required": ["trace_context", "state_vector", "payload"]
    }
    return new_schema

def migrate_tool(tool: dict) -> dict:
    if "input_schema" in tool:
        props = tool["input_schema"].get("properties", {})
        if "trace_context" not in props:
            tool["input_schema"] = migrate_schema(tool["input_schema"])

    if "output_schema" in tool:
        props = tool["output_schema"].get("properties", {})
        if "trace_context" not in props:
            tool["output_schema"] = migrate_schema(tool["output_schema"])
    return tool

def process_file(filepath: str):
    if "node_modules" in filepath or "venv" in filepath or ".git" in filepath:
        return

    with open(filepath, 'r') as f:
        content = f.read()

    try:
        data = json.loads(content)
        is_yaml = False
    except Exception:
        try:
            data = yaml.safe_load(content)
            is_yaml = True
        except Exception:
            # print(f"Skipping {filepath}: not valid JSON or YAML")
            return

    modified = False

    if isinstance(data, dict):
        if "native_tools" in data and isinstance(data["native_tools"], list):
            for i, tool in enumerate(data["native_tools"]):
                if "input_schema" in tool:
                    props = tool["input_schema"].get("properties", {})
                    if "trace_context" not in props:
                        data["native_tools"][i] = migrate_tool(tool)
                        modified = True

        # Check if file is just a single tool manifest
        elif "input_schema" in data:
            props = data["input_schema"].get("properties", {})
            if "trace_context" not in props:
                data = migrate_tool(data)
                modified = True

    if modified:
        with open(filepath, 'w') as f:
            if is_yaml:
                yaml.dump(data, f, sort_keys=False)
            else:
                json.dump(data, f, indent=2)
        print(f"Migrated {filepath}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_v1_to_v2.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]

    for ext in ('*.json', '*.yaml', '*.yml'):
        for path in Path(directory).rglob(ext):
            process_file(str(path))

if __name__ == "__main__":
    main()
