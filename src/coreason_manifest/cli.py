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

    # Hash
    hash_parser = subparsers.add_parser("hash", help="Calculate the canonical hash of an agent definition")
    hash_parser.add_argument("ref", help="Reference to the agent (e.g. examples/agent.py:agent)")
    hash_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

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

    elif args.command == "hash":
        if not hasattr(agent, "compute_hash"):
            sys.stderr.write("Error: Agent definition does not support canonical hashing.\n")
            sys.exit(1)

        raw_hash = agent.compute_hash()
        # Ensure proper format
        final_hash = f"sha256:{raw_hash}"

        if args.json:
            print(json.dumps({"hash": final_hash, "algorithm": "sha256"}))
        else:
            print(final_hash)


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
