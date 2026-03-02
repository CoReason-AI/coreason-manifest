import hashlib
import json
import logging
import random
import secrets
import time
from datetime import UTC, datetime
from typing import Any

from referencing import Registry, Resource
from referencing.exceptions import PointerToNowhere, Unresolvable
from referencing.jsonschema import DRAFT202012

from coreason_manifest.core.common.identity import DelegationContract, IdentityPassport, SystemContext, UserContext
from coreason_manifest.core.primitives.types import DataClassification
from coreason_manifest.core.telemetry.telemetry_schemas import NodeExecution, NodeState
from coreason_manifest.core.workflow.evals import ChaosConfig, EvalsManifest
from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes import HumanNode, Node, PlannerNode, SwarmNode

logger = logging.getLogger(__name__)


class MockFactory:
    def __init__(self, seed: int | None = None):
        if seed is not None:
            self.rng = random.Random(seed)  # noqa: S311
        else:
            self.rng = secrets.SystemRandom()

    def generate_mock_passport(
        self, classification: "DataClassification | None" = None, is_swarm_child: bool = False
    ) -> "IdentityPassport":
        """
        Synthesizes a mathematically valid Zero-Trust envelope.
        SOTA 2026 fields (Lineage, Edge Compute, CAEP) are scaffolded for parallel Epic execution.
        """

        if classification is None:
            classification = DataClassification.INTERNAL

        current_time = time.time()

        # SOTA 2026 Variables
        sota_parent_id = f"mock_parent_jti_{self.rng.randint(1000, 9999)}" if is_swarm_child else None
        sota_caep_uri = "https://mock-ssf.local.coreason.ai/stream"

        return IdentityPassport(
            passport_id=f"mock_jti_{self.rng.randint(1000, 9999)}",
            parent_passport_id=sota_parent_id,
            signature_algorithm="ML-DSA-65",
            user=UserContext(anonymized_user_id="mock_hmac_hash_12345", roles=["operator"]),
            system=SystemContext(agent_id="mock_agent", version="1.0.0"),
            delegation=DelegationContract(
                allowed_tools=["*"],
                caveats=[],
                max_budget_usd=10.0,
                issued_at=current_time - 100,
                expires_at=current_time + 3600,
                max_tokens=50_000,
                max_compute_time_ms=120_000,
                max_data_classification=classification,
                caep_stream_uri=sota_caep_uri,
            ),
            issuer_uri="https://mock.auth.coreason.ai",
            signature_hash="mock_sig_hash",
        )

    def _generate_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def _generate_schema_data(
        self,
        schema: dict[str, Any] | bool | None,
        visited: frozenset[int] | None = None,
        visited_refs: frozenset[str] | None = None,
        depth: int = 0,
        resolver: Any | None = None,
    ) -> Any:
        max_depth = 10

        if depth > max_depth:
            return ""

        # Hoist cycle detection to top to catch all recursions early
        if isinstance(schema, dict):
            schema_id = id(schema)
            if visited is None:
                visited = frozenset()

            if schema_id in visited:
                return ""

            visited = visited | {schema_id}

        # Handle JSON Schema boolean specifications
        if isinstance(schema, bool):
            return "mock_data" if schema else None

        if not schema:
            return {"mock_key": "mock_value"}

        # Ensure we only process dictionaries moving forward
        if not isinstance(schema, dict):
            return schema

        # Enforce exact values (Const and Enum) before any deeper evaluation
        if "const" in schema:
            return schema["const"]
        if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
            return self.rng.choice(schema["enum"])

        # Best-effort combinator support
        for combinator in ["allOf", "anyOf", "oneOf"]:
            if combinator in schema and isinstance(schema[combinator], list) and schema[combinator]:
                return self._generate_schema_data(schema[combinator][0], visited, visited_refs, depth, resolver)

        # Resolve $ref if present
        if "$ref" in schema and resolver:
            ref_uri = schema["$ref"]

            # Check for cycle in refs
            if visited_refs is not None and ref_uri in visited_refs:
                return ""

            try:
                resolved = resolver.lookup(ref_uri)
                contents = resolved.contents
                new_visited_refs = (visited_refs or frozenset()) | {ref_uri}
                return self._generate_schema_data(contents, visited, new_visited_refs, depth, resolved.resolver)
            except (Unresolvable, PointerToNowhere):
                logger.warning(f"Unresolvable reference: {ref_uri}")
                return "mock_ref_error"

        # Simple schema support
        type_ = schema.get("type")

        if isinstance(type_, list):
            # Pick the first non-null type, or default to string
            types = [t for t in type_ if t != "null"]
            type_ = types[0] if types else "string"
        elif not type_:
            # Implicit type inference based on structure
            if "properties" in schema:
                type_ = "object"
            elif "items" in schema or "prefixItems" in schema:
                type_ = "array"
            else:
                type_ = "string"

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
            data = {
                k: self._generate_schema_data(v, visited, visited_refs, depth + 1, resolver) for k, v in props.items()
            }
            # Prevent starvation if no properties defined but additionalProperties allowed
            if not data:
                additional = schema.get("additionalProperties", True)
                if additional is not False:
                    # If additional is a schema, use it; otherwise generic
                    val_schema = additional if isinstance(additional, dict) else None
                    data["mock_dynamic_key"] = self._generate_schema_data(
                        val_schema, visited, visited_refs, depth + 1, resolver
                    )
            return data
        if type_ == "array":
            items_schema = schema.get("prefixItems", schema.get("items"))
            if isinstance(items_schema, list):
                # Handle tuple validation (array of schemas)
                return [
                    self._generate_schema_data(item, visited, visited_refs, depth + 1, resolver)
                    for item in items_schema
                ]
            if items_schema is not None:
                # Handle standard array validation (single schema)
                return [self._generate_schema_data(items_schema, visited, visited_refs, depth + 1, resolver)]
            return []
        return "mock_data"

    def simulate_trace(
        self, flow: GraphFlow | LinearFlow, max_steps: int = 20, evals: EvalsManifest | None = None
    ) -> list[NodeExecution]:
        trace: list[NodeExecution] = []
        execution_map: dict[str, NodeExecution] = {}  # node_id -> last execution

        fuzzing_vars: set[str] = set()
        if evals and evals.fuzzing_targets:
            for ft in evals.fuzzing_targets:
                fuzzing_vars.update(ft.variables)

        # Create resolver from the full document
        full_doc = flow.model_dump(mode="json", by_alias=True)
        # We use empty string as base URI for the root document
        resource = Resource.from_contents(full_doc, default_specification=DRAFT202012)
        registry = Registry().with_resource("", resource)
        resolver = registry.resolver()

        if isinstance(flow, LinearFlow):
            chaos_config = None
            if evals and evals.test_cases and evals.test_cases[0].chaos_config:
                chaos_config = evals.test_cases[0].chaos_config

            nodes = flow.steps
            prev_hashes: list[str] = []
            for node in nodes:
                exec_records = self._execute_node(
                    node, execution_map, prev_hashes, resolver, fuzzing_vars, chaos_config
                )
                trace.extend(exec_records)
                last_record = exec_records[-1]
                execution_map[node.id] = last_record
                # Next node depends on this one
                prev_hashes = [last_record.execution_hash] if last_record.execution_hash else []

        elif isinstance(flow, GraphFlow):
            graph = flow.graph

            # SOTA 2026 Evals-as-Code execution overrides random walk with deterministic assertions
            if evals and evals.test_cases:
                # Execute based on the first test case for simplicity in the mock
                tc = evals.test_cases[0]
                chaos_config = tc.chaos_config if tc else None
                expected_path = tc.expected_traversal_path
                prev_hashes = []

                # Mock inputs injection (if applicable) would go to the first node's context
                for n_id in expected_path:
                    node = graph.nodes.get(n_id)
                    if not node:
                        logger.warning(f"Eval requested node {n_id} not in graph.")
                        break

                    exec_records = self._execute_node(
                        node, execution_map, prev_hashes, resolver, fuzzing_vars, chaos_config
                    )

                    # Override outputs with mock inputs if it's the start node
                    if tc.mock_inputs and len(trace) == 0 and exec_records:
                        exec_records[0].inputs.update(tc.mock_inputs)

                    trace.extend(exec_records)
                    last_record = exec_records[-1]
                    execution_map[node.id] = last_record
                    prev_hashes = [last_record.execution_hash] if last_record.execution_hash else []

                # We do not evaluate assertions here (done by evaluator), just trace creation.
            else:
                chaos_config = None
                # Find start nodes (indegree 0)
                all_targets = {e.to_node for e in graph.edges}
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
                    exec_records = self._execute_node(
                        current_node, execution_map, prev_hashes, resolver, fuzzing_vars, chaos_config
                    )
                    trace.extend(exec_records)
                    last_record = exec_records[-1]
                    execution_map[current_node.id] = last_record
                    steps += 1

                    # Update prev_hashes for next iteration
                    # We know execution_hash is generated
                    prev_hashes = [last_record.execution_hash] if last_record.execution_hash else []

                    # Find next node
                    outgoing_edges = [e for e in graph.edges if e.from_node == current_node.id]
                    if not outgoing_edges:
                        break

                    # Pick one edge randomly
                    chosen_edge = self.rng.choice(outgoing_edges)
                    current_node = graph.nodes.get(chosen_edge.to_node)

        return trace

    def _execute_node(
        self,
        node: Node,
        _execution_map: dict[str, NodeExecution],
        prev_hashes: list[str] | None = None,
        resolver: Any | None = None,
        fuzzing_vars: set[str] | None = None,
        chaos_config: ChaosConfig | None = None,
    ) -> list[NodeExecution]:
        timestamp = datetime.now(UTC)

        if isinstance(node, SwarmNode):
            # Swarm Expansion Logic
            # Handle 'infinite' or None for concurrency
            if node.max_concurrency == "infinite" or node.max_concurrency is None:
                limit = 100
            else:
                limit = int(node.max_concurrency)

            concurrency = min(limit, 3)  # Use 3 as typical sample
            workers = []
            worker_hashes = []

            for i in range(concurrency):
                w_id = f"{node.id}_worker_{i}"
                w_inputs = {"worker_id": i, "workload": "mock_item"}
                w_outputs = {"result": "processed"}
                w_duration = self.rng.uniform(10, 100)
                if chaos_config:
                    w_duration += chaos_config.latency_ms

                w_state = NodeState.COMPLETED
                w_error = None

                if chaos_config and self.rng.random() < chaos_config.error_rate:
                    w_state = NodeState.FAILED
                    w_error = "HTTP 500 Internal Server Error"

                w_hash = self._generate_hash(
                    f"{w_id}{json.dumps(w_inputs, sort_keys=True)}{json.dumps(w_outputs, sort_keys=True)}"
                )

                workers.append(
                    NodeExecution(
                        node_id=w_id,
                        state=w_state,
                        inputs=w_inputs,
                        outputs=w_outputs,
                        error=w_error,
                        timestamp=timestamp,
                        duration_ms=w_duration,
                        execution_hash=w_hash,
                        parent_hashes=prev_hashes or [],
                        attributes={"mock": True, "worker": True},
                    )
                )
                worker_hashes.append(w_hash)

            # Aggregator
            agg_inputs = {"results": [w.outputs for w in workers]}
            agg_outputs = {"final": "aggregated_result"}
            agg_duration = self.rng.uniform(10, 50)
            if chaos_config:
                agg_duration += chaos_config.latency_ms

            agg_state = NodeState.COMPLETED
            agg_error = None

            if chaos_config and self.rng.random() < chaos_config.error_rate:
                agg_state = NodeState.FAILED
                agg_error = "HTTP 500 Internal Server Error"

            agg_hash = self._generate_hash(
                f"{node.id}{json.dumps(agg_inputs, sort_keys=True)}{json.dumps(agg_outputs, sort_keys=True)}"
            )

            aggregator = NodeExecution(
                node_id=node.id,
                state=agg_state,
                inputs=agg_inputs,
                outputs=agg_outputs,
                error=agg_error,
                timestamp=timestamp,
                duration_ms=agg_duration,
                execution_hash=agg_hash,
                parent_hashes=worker_hashes,
                attributes={"mock": True, "role": "aggregator"},
            )

            return [*workers, aggregator]

        # Standard Node Logic
        inputs = {"mock_input": "data"}
        outputs: Any = {}

        if isinstance(node, PlannerNode):
            raw_output = self._generate_schema_data(node.output_schema, resolver=resolver)
            outputs = raw_output if isinstance(raw_output, dict) else {"result": raw_output}
        elif isinstance(node, HumanNode):
            raw_output = (
                self._generate_schema_data(node.input_schema, resolver=resolver)
                if node.input_schema
                else {"approved": True}
            )
            outputs = raw_output if isinstance(raw_output, dict) else {"result": raw_output}
        else:
            outputs = {"result": "mock_output"}

        if fuzzing_vars:
            for key in outputs:
                if key in fuzzing_vars:
                    # Inject adversarial edge-case data
                    payloads = [
                        "A" * 100000,
                        -999999999,
                        "'; DROP TABLE users; --",
                        "<script>alert(1)</script>",
                        "\x00" * 100,
                    ]
                    outputs[key] = self.rng.choice(payloads)

        duration = self.rng.uniform(10, 500)
        if chaos_config:
            duration += chaos_config.latency_ms

        state = NodeState.COMPLETED
        error = None

        if chaos_config and self.rng.random() < chaos_config.error_rate:
            state = NodeState.FAILED
            error = "HTTP 500 Internal Server Error"

        # Calculate hash
        data_to_hash = f"{node.id}{json.dumps(inputs, sort_keys=True)}{json.dumps(outputs, sort_keys=True)}"
        exec_hash = self._generate_hash(data_to_hash)

        return [
            NodeExecution(
                node_id=node.id,
                state=state,
                inputs=inputs,
                outputs=outputs,
                error=error,
                timestamp=timestamp,
                duration_ms=duration,
                execution_hash=exec_hash,
                parent_hashes=prev_hashes or [],
                attributes={"mock": True},
            )
        ]
