# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from coreason_manifest.spec.simulation import (
    SimulationStep,
    SimulationTrace,
    StepType,
)
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    HumanNode,
    RecipeDefinition,
    RecipeNode,
    RouterNode,
)


class GraphExecutor:
    """Reference Graph Executor for RecipeDefinition."""

    def __init__(self, recipe: RecipeDefinition, initial_state: dict[str, Any]):
        self.recipe = recipe
        self.context = initial_state.copy()

        # Initialize trace
        self.trace = SimulationTrace(
            agent_id=self.recipe.metadata.name, agent_version="v2", steps=[], metadata={"recipe_kind": self.recipe.kind}
        )
        self.max_steps = 50

    async def run(self) -> SimulationTrace:
        """Executes the graph traversal."""
        current_node_id: str | None = self.recipe.topology.entry_point
        steps_count = 0

        while current_node_id and steps_count < self.max_steps:
            node = self._get_node(current_node_id)
            if not node:
                raise ValueError(f"Node {current_node_id} not found in topology.")

            # Execute Node
            step = await self._execute_node(node)
            self.trace.steps.append(step)
            steps_count += 1

            # Resolve Next
            current_node_id = self._resolve_next(node.id, step)

        return self.trace

    def _get_node(self, node_id: str) -> RecipeNode | None:
        for node in self.recipe.topology.nodes:
            if node.id == node_id:
                return node
        return None

    async def _execute_node(self, node: RecipeNode) -> SimulationStep:
        step_type = StepType.INTERACTION
        inputs = {}
        action = None
        observation = None
        thought = None

        if isinstance(node, AgentNode):
            step_type = StepType.TOOL_EXECUTION
            # Map inputs: input_key (agent arg) -> source_key (blackboard)
            for input_key, source_key in node.inputs_map.items():
                if source_key in self.context:
                    inputs[input_key] = self.context[source_key]

            # Mock Execution
            print(f"Executing Agent [{node.agent_ref}]")
            # Create a dummy output.
            # In a real scenario, this would invoke the agent.
            output_data = {"output": f"Mocked output from {node.agent_ref}"}
            observation = output_data

            # Update Blackboard
            self.context.update(output_data)

        elif isinstance(node, HumanNode):
            step_type = StepType.INTERACTION
            print(f"Waiting for Human: {node.prompt}")
            try:
                # Use built-in input for CLI interaction
                # We use a flush to ensure prompt is visible
                print(f"{node.prompt} > ", end="", flush=True)
                user_response = input()
            except (EOFError, OSError):
                # Handle cases where input is closed or piped
                user_response = "Mocked Input"
                print("Mocked Input")  # Echo for clarity in logs

            observation = {"response": user_response}
            self.context.update(observation)

        elif isinstance(node, RouterNode):
            step_type = StepType.REASONING
            # Read input key
            input_val = self.context.get(node.input_key)
            inputs = {str(node.input_key): input_val}

            # Determine route (for observation purposes)
            target = node.default_route
            if input_val is not None and str(input_val) in node.routes:
                target = node.routes[str(input_val)]

            # Mypy gets confused by Any | None in dict value vs declaration
            observation = {"decision": target, "value": input_val}  # type: ignore[dict-item]
            thought = f"Router decision based on {node.input_key}={input_val}: Go to {target}"

        return SimulationStep(
            node_id=node.id,
            type=step_type,
            inputs=inputs,
            thought=thought,
            action=action,
            observation=observation,
            snapshot=self.context.copy(),
        )

    def _resolve_next(self, current_node_id: str, last_step: SimulationStep | None = None) -> str | None:
        node = self._get_node(current_node_id)
        if not node:
            return None

        # Router Logic
        if isinstance(node, RouterNode):
            # Use the decision from the step observation if available, otherwise recompute
            if last_step and last_step.observation and "decision" in last_step.observation:
                decision = last_step.observation["decision"]
                if isinstance(decision, str):
                    return decision
                return str(decision)

            # Recompute if needed (fallback)
            input_val = self.context.get(node.input_key)
            if input_val is not None and str(input_val) in node.routes:
                return node.routes[str(input_val)]
            return node.default_route

        # Standard Logic: Look for outgoing edge
        for edge in self.recipe.topology.edges:
            if edge.source == current_node_id:
                return edge.target

        return None
