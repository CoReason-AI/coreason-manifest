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
import textwrap
from pathlib import Path

from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    LogicStep,
    ManifestV2,
    SwitchStep,
)
from coreason_manifest.spec.v2.recipe import RecipeDefinition
from coreason_manifest.runtime.executor import GraphExecutor
from coreason_manifest.utils.loader import load_agent_from_ref
from coreason_manifest.utils.mock import generate_mock_output
from coreason_manifest.utils.viz import generate_mermaid_graph


def handle_init(args: argparse.Namespace) -> None:
    target_dir = Path(args.name)

    # 1. Checks
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"❌ Error: Directory '{args.name}' is not empty.")
        sys.exit(1)

    # 2. Creation
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / ".vscode").mkdir(exist_ok=True)

    # 3. File Generation

    # agent.py
    agent_py_content = textwrap.dedent("""
        from pydantic import BaseModel, Field
        from coreason_manifest.builder import AgentBuilder, TypedCapability, CapabilityType
        from coreason_manifest.spec.v2.resources import ModelProfile, RateCard, PricingUnit, Currency

        # 1. Define Data Contracts
        class GreetInput(BaseModel):
            name: str = Field(..., description="Name of the person to greet.")

        class GreetOutput(BaseModel):
            message: str = Field(..., description="A friendly greeting message.")

        # 2. Define Capability
        greet_cap = TypedCapability(
            name="greet_user",
            description="Greets the user with a friendly message.",
            input_model=GreetInput,
            output_model=GreetOutput,
            type=CapabilityType.ATOMIC
        )

        # 3. Build Agent
        builder = AgentBuilder(name="GreeterAgent")
        builder.with_system_prompt("You are a helpful assistant.")
        builder.with_model("gpt-4o")
        builder.with_tool("hello_world_tool")
        builder.with_capability(greet_cap)

        # 4. Generate Manifest
        agent = builder.build()

        # 5. Add FinOps RateCard (Best Practice)
        # Extract definition
        agent_def = agent.definitions["GreeterAgent"]
        # Create resources
        resources = ModelProfile(
            provider="openai",
            model_id="gpt-4o",
            pricing=RateCard(
                unit=PricingUnit.TOKEN_1K,
                currency=Currency.USD,
                input_cost=0.03,
                output_cost=0.06
            )
        )
        # Update definition (Models are immutable)
        updated_def = agent_def.model_copy(update={"resources": resources})
        # Update manifest
        agent.definitions["GreeterAgent"] = updated_def

        if __name__ == "__main__":
            print(agent.model_dump_json(indent=2, by_alias=True, exclude_none=True))
    """).strip()

    # README.md
    readme_content = textwrap.dedent(f"""
        # {args.name}

        ## Setup

        1. Open this folder in VS Code.
        2. Open `agent.py`.

        ## Running

        - Press F5 to run the agent in mock mode.
        - Or use the CLI:
          ```bash
          coreason run agent.py:agent --mock --inputs '{{"name": "World"}}'
          ```

        ## Visualization

        - Use the "Viz" launch configuration in VS Code.
        - Or use the CLI:
          ```bash
          coreason viz agent.py:agent
          ```
    """).strip()

    # .gitignore
    gitignore_content = textwrap.dedent("""
        __pycache__/
        .env
    """).strip()

    # .vscode/launch.json
    launch_json_content = textwrap.dedent("""
        {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "CoReason: Run Agent (Mock)",
                    "type": "python",
                    "request": "launch",
                    "module": "coreason_manifest.cli",
                    "args": [
                        "run",
                        "${file}:agent",
                        "--mock",
                        "--inputs", "{\\"name\\": \\"World\\"}"
                    ],
                    "console": "integratedTerminal"
                },
                {
                    "name": "CoReason: Visualize Graph",
                    "type": "python",
                    "request": "launch",
                    "module": "coreason_manifest.cli",
                    "args": [
                        "viz",
                        "${file}:agent"
                    ],
                    "console": "integratedTerminal"
                }
            ]
        }
    """).strip()

    # Write files
    (target_dir / "agent.py").write_text(agent_py_content)
    (target_dir / "README.md").write_text(readme_content)
    (target_dir / ".gitignore").write_text(gitignore_content)
    (target_dir / ".vscode" / "launch.json").write_text(launch_json_content)

    # 4. Success Message
    print(f"✅ Created new agent project in './{args.name}'")
    print("")
    print("👉 Next steps:")
    print(f"   1. cd {args.name}")
    print("   2. code .  (Open in VS Code)")
    print("   3. Open 'agent.py' and press F5 to run!")


def handle_validate(args: argparse.Namespace) -> None:
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ Error: File '{args.file}' not found.")
        sys.exit(1)

    yaml_module = None
    try:
        import yaml

        yaml_module = yaml
    except ImportError:
        pass

    if file_path.suffix.lower() in [".yaml", ".yml"] and yaml_module is None:
        print("❌ Error: PyYAML is not installed. Please install it to validate YAML files.")
        print("  pip install PyYAML")
        sys.exit(1)

    try:
        content = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() in [".yaml", ".yml"]:
            # We already checked yaml_module is not None if extension is yaml
            data = yaml_module.safe_load(content)  # type: ignore
        elif file_path.suffix.lower() == ".json":
            data = json.loads(content)
        else:
            print(f"❌ Error: Unsupported file extension '{file_path.suffix}'. Use .json, .yaml, or .yml.")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Malformed JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        if yaml_module and isinstance(e, yaml_module.YAMLError):
            print(f"❌ Error: Malformed YAML file: {e}")
            sys.exit(1)
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

    try:
        name = "Unknown"
        version = "Unknown"
        agent_obj: ManifestV2 | AgentDefinition

        if isinstance(data, dict) and "apiVersion" in data:
            agent_obj = ManifestV2.model_validate(data)
            name = agent_obj.metadata.name
            # Try to get version from metadata (it allows extra fields)
            # We use getattr because it's dynamic
            version = getattr(agent_obj.metadata, "version", "Unknown")
        else:
            agent_obj = AgentDefinition.model_validate(data)
            name = agent_obj.name
            version = "Unknown"

        if args.json:
            # Output full JSON representation
            print(agent_obj.model_dump_json(indent=2))
        else:
            print(f"✅ Valid Agent: {name} (v{version})")

    except ValidationError as e:
        print("❌ Validation Failed:")
        for err in e.errors():
            loc = " -> ".join(str(part) for part in err["loc"])
            msg = err["msg"]
            print(f"  • {loc}: {msg}")
        sys.exit(1)


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

    # Init
    init_parser = subparsers.add_parser("init", help="Initialize a new CoReason agent project")
    init_parser.add_argument("name", help="Name of the agent/directory (e.g., my_first_agent)")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate a static agent definition file")
    validate_parser.add_argument("file", help="Path to the .yaml or .json file")
    validate_parser.add_argument("--json", action="store_true", help="Output validation result as JSON")

    args = parser.parse_args()

    if args.command == "init":
        handle_init(args)
        return

    if args.command == "validate":
        handle_validate(args)
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
            inputs = json.loads(args.inputs)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error parsing inputs: {e}\n")
            sys.exit(1)

        if isinstance(agent, RecipeDefinition):
            import asyncio

            # Instantiate executor
            executor = GraphExecutor(agent, inputs)

            # Run simulation
            try:
                trace = asyncio.run(executor.run())

                # Print result
                print(json.dumps({
                    "trace_id": str(trace.trace_id),
                    "final_state": executor.context,
                    "steps_count": len(trace.steps)
                }, indent=2, default=str))
            except Exception as e:
                sys.stderr.write(f"Error running graph executor: {e}\n")
                sys.exit(1)
        else:
            _run_simulation(agent, args.mock)


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
