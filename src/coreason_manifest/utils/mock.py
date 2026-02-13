import hashlib
import json
import random
from datetime import UTC, datetime
from typing import Any

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import HumanNode, Node, PlannerNode
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState


class MockFactory:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def _generate_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def _generate_schema_data(self, schema: dict[str, Any] | None) -> Any:
        if not schema:
            return {"mock_key": "mock_value"}

        # Simple schema support
        type_ = schema.get("type", "string")
        if type_ == "string":
            return "lorem ipsum"
        if type_ == "integer":
            return self.rng.randint(1, 100)
        if type_ == "number":
            return self.rng.random()
        if type_ == "boolean":
            return self.rng.choice([True, False])
        if type_ == "object":
            props = schema.get("properties", {})
            return {k: self._generate_schema_data(v) for k, v in props.items()}
        if type_ == "array":
            return [self._generate_schema_data(schema.get("items"))]
        return "mock_data"

    def simulate_trace(self, flow: GraphFlow | LinearFlow, max_steps: int = 20) -> list[NodeExecution]:
        trace: list[NodeExecution] = []
        execution_map: dict[str, NodeExecution] = {}  # node_id -> last execution

        if isinstance(flow, LinearFlow):
            nodes = flow.sequence
            prev_hashes: list[str] = []
            for node in nodes:
                exec_record = self._execute_node(node, execution_map, prev_hashes)
                trace.append(exec_record)
                execution_map[node.id] = exec_record
                # Next node depends on this one
                prev_hashes = [exec_record.execution_hash] if exec_record.execution_hash else []

        elif isinstance(flow, GraphFlow):
            # Find start nodes (indegree 0)
            graph = flow.graph
            all_targets = {e.target for e in graph.edges}
            start_nodes = [n for n_id, n in graph.nodes.items() if n_id not in all_targets]

            if not start_nodes:
                # Cycle or no nodes? Pick first
                if graph.nodes:
                    start_nodes = [next(iter(graph.nodes.values()))]
                else:
                    return []

            # Simple random walk
            current_node: Node | None = self.rng.choice(start_nodes)
            steps = 0

            # For the very first node, no previous hash
            prev_hashes = []

            while current_node and steps < max_steps:
                exec_record = self._execute_node(current_node, execution_map, prev_hashes)
                trace.append(exec_record)
                execution_map[current_node.id] = exec_record
                steps += 1

                # Update prev_hashes for next iteration
                prev_hashes = [exec_record.execution_hash] if exec_record.execution_hash else []

                # Find next node
                outgoing_edges = [e for e in graph.edges if e.source == current_node.id]
                if not outgoing_edges:
                    break

                # Pick one edge randomly
                chosen_edge = self.rng.choice(outgoing_edges)
                current_node = graph.nodes.get(chosen_edge.target)

        return trace

    def _execute_node(
        self,
        node: Node,
        _execution_map: dict[str, NodeExecution],
        prev_hashes: list[str] | None = None,
    ) -> NodeExecution:
        # Generate inputs/outputs
        inputs = {"mock_input": "data"}
        outputs: Any = {}

        if isinstance(node, PlannerNode):
            outputs = self._generate_schema_data(node.output_schema)
        elif isinstance(node, HumanNode):
            outputs = (
                self._generate_schema_data(node.input_schema)
                if node.input_schema
                else {"approved": True}
            )
        else:
            outputs = {"result": "mock_output"}

        # Create execution record
        timestamp = datetime.now(UTC)
        duration = self.rng.uniform(10, 500)

        # Calculate hash
        data_to_hash = f"{node.id}{json.dumps(inputs, sort_keys=True)}{json.dumps(outputs, sort_keys=True)}"
        exec_hash = self._generate_hash(data_to_hash)

        return NodeExecution(
            node_id=node.id,
            state=NodeState.COMPLETED,
            inputs=inputs,
            outputs=outputs,
            timestamp=timestamp,
            duration_ms=duration,
            execution_hash=exec_hash,
            previous_hashes=prev_hashes or [],
            attributes={"mock": True}
        )
