# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestV2,
    SwitchStep,
)
from coreason_manifest.utils.loader import load_agent_from_ref
from coreason_manifest.utils.mock import generate_mock_output
from coreason_manifest.utils.viz import generate_mermaid_graph


def main() -> None:
    parser = argparse.ArgumentParser(prog="coreason", description="CoReason Manifest CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect an agent definition")
    inspect_parser.add_argument("ref", help="Reference to the agent (path/to/file.py:var)")
    inspect_parser.add_argument("--json", action="store_true", help="Output JSON (default)")

    # Viz
    viz_parser = subparsers.add_parser("viz", help="Visualize an agent workflow")
    viz_parser.add_argument("ref", help="Reference to the agent")
    viz_parser.add_argument("--json", action="store_true", help="Output JSON wrapper around mermaid")

    # Run
    run_parser = subparsers.add_parser("run", help="Simulate an agent execution")
    run_parser.add_argument("ref", help="Reference to the agent")
    run_parser.add_argument("--inputs", default="{}", help="JSON string inputs")
    run_parser.add_argument("--mock", action="store_true", help="Use mock outputs")

    # The prompt says "All commands must support a --json flag".
    # For 'run', it's redundant as we output NDJSON events, but we support it for compliance.
    run_parser.add_argument("--json", action="store_true", help="Output JSON events")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate a static agent definition file")
    validate_parser.add_argument("file", help="Path to the .yaml or .json file")

    args = parser.parse_args()

    if args.command == "validate":
        handle_validate(args.file)
        return

    try:
        agent = load_agent_from_ref(args.ref)
    except Exception as e:
        # Logs/debugs must go to stderr
        sys.stderr.write(f"Error loading agent: {e}\n")
        sys.exit(1)

    if args.command == "inspect":
        # Always output JSON for inspect
        print(agent.model_dump_json(indent=2, by_alias=True, exclude_none=True))

    elif args.command == "viz":
        mermaid = generate_mermaid_graph(agent)
        if args.json:
            print(json.dumps({"mermaid": mermaid}))
        else:
            print(mermaid)

    elif args.command == "run":
        try:
            json.loads(args.inputs)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error parsing inputs: {e}\n")
            sys.exit(1)

        _run_simulation(agent, args.mock)


def handle_validate(file_path: str) -> None:
    """
    Validates a static agent definition file (JSON or YAML) against the AgentDefinition schema.
    """
    path = Path(file_path)
    if not path.exists():
        sys.stderr.write(f"❌ Error: File not found: {file_path}\n")
        sys.exit(1)

    data: Any = None
    if path.suffix.lower() == ".json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"❌ Error: Invalid JSON: {e}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"❌ Error reading file: {e}\n")
            sys.exit(1)
    elif path.suffix.lower() in [".yaml", ".yml"]:
        try:
            import yaml
        except ImportError:
            sys.stderr.write("❌ Error: PyYAML is not installed. Please install it to validate YAML files.\n")
            sys.exit(1)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            sys.stderr.write(f"❌ Error: Invalid YAML: {e}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"❌ Error reading file: {e}\n")
            sys.exit(1)
    else:
        sys.stderr.write(f"❌ Error: Unsupported file extension: {path.suffix}\n")
        sys.exit(1)

    try:
        agent = AgentDefinition.model_validate(data)
        # Version is not present in AgentDefinition schema, so we default to 'Unknown'
        version = getattr(agent, "version", "Unknown")
        print(f"✅ Valid Agent: {agent.name} (v{version})")
    except ValidationError as e:
        print("❌ Validation Failed:")
        for err in e.errors():
            # loc is a tuple of (string | int)
            loc = " -> ".join(str(l) for l in err["loc"])
            print(f"  • {loc}: {err['msg']}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def _run_simulation(agent: ManifestV2, mock: bool) -> None:
    """
    Runs a simulation of the agent workflow.
    Iterates through all steps defined in the workflow (not graph traversal)
    as per instructions to ensure full coverage during inspection.
    """
    for step_id, step in agent.workflow.steps.items():
        capability = "Unknown"

        if isinstance(step, AgentStep):
            capability = step.agent
        elif isinstance(step, LogicStep):
            capability = "Logic"
        elif isinstance(step, CouncilStep):
            capability = "Council"
        elif isinstance(step, SwitchStep):
            capability = "Switch"

        # Emit step_start
        print(json.dumps({"type": "step_start", "step_id": step_id, "capability": capability}))
        sys.stdout.flush()

        result = None
        if mock and isinstance(step, AgentStep):
            # Resolve definition
            defn = agent.definitions.get(step.agent)
            if isinstance(defn, AgentDefinition):
                try:
                    result = generate_mock_output(defn)
                except Exception as e:
                    sys.stderr.write(f"Error generating mock for {step.agent}: {e}\n")
            else:
                sys.stderr.write(f"Definition for {step.agent} not found or not an Agent.\n")

        # Emit step_output
        print(json.dumps({"type": "step_output", "step_id": step_id, "output": result}))
        sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    main()
