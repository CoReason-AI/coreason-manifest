# tests/test_zero_trust.py

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.contracts import (
    ActionNode,
    AtomicSkill,
    Constraint,
    PlanTree,
    StrategyNode,
)
from coreason_manifest.utils.gatekeeper import compile_graph, validate_policy, ZeroTrustRoutingError
from coreason_manifest.utils.integrity import generate_execution_receipt, verify_merkle_proof, compute_hash, reconstruct_payload
from coreason_manifest.utils.loader import scoped_tool_context, verify_tool_authorization
from coreason_manifest.utils.io import SecurityViolationError


class TestStrictContracts:
    def test_atomic_skill_json_schema(self):
        """Test that AtomicSkill accepts valid JSON Schema definitions."""
        skill = AtomicSkill(
            name="schema_skill",
            version="1.0.0",
            definition={
                "input": {
                    "type": "object",
                    "properties": {
                        "q": {"type": "string"}
                    }
                }
            }
        )
        assert skill.definition["input"]["type"] == "object"

    def test_node_constraints_and_metadata(self):
        """Test new NodeSpec fields: constraints and metadata."""
        c = Constraint(type="timeout", value=30)
        skill = AtomicSkill(name="s", version="1.0.0", definition={})

        node = ActionNode(
            id="n1",
            skill=skill,
            inputs={},
            outputs={},
            constraints=[c],
            metadata={"audit_id": "12345"}
        )
        assert node.constraints[0].type == "timeout"
        assert node.metadata["audit_id"] == "12345"

    def test_plantree_discriminator(self):
        """Test PlanTree discriminated union serialization."""
        skill = AtomicSkill(name="s", version="1.0.0", definition={})

        data = {
            "id": "p1",
            "root_node": "n1",
            "nodes": {
                "n1": {
                    "type": "action", # Discriminator
                    "id": "n1",
                    "skill": skill.model_dump(),
                    "inputs": {},
                    "outputs": {}
                },
                "n2": {
                    "type": "strategy", # Discriminator
                    "id": "n2",
                    "strategy_name": "foo",
                    "inputs": {},
                    "routes": {},
                    "default_route": "n1" # Required
                }
            }
        }

        plan = PlanTree.model_validate(data)
        assert isinstance(plan.nodes["n1"], ActionNode)
        assert isinstance(plan.nodes["n2"], StrategyNode)


class TestGatekeeper:
    def test_cycle_detection_strict(self):
        """Test that unbounded cycles are rejected."""
        n1 = StrategyNode(id="start", strategy_name="loop", inputs={}, routes={"next": "node2"}, default_route="node2")
        n2 = StrategyNode(id="node2", strategy_name="loop", inputs={}, routes={"back": "start"}, default_route="start")

        plan = PlanTree(
            id="cyclic",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )

        with pytest.raises(ZeroTrustRoutingError, match="Unbounded cycle detected"):
            compile_graph(plan)

    def test_cycle_detection_bounded_allowed_header(self):
        """Test that bounded cycles (with Constraint on Header/Target) are allowed."""
        # start (Constraint Here) -> node2 -> start
        c = Constraint(type="max_iterations", value=5)
        n1 = StrategyNode(
            id="start",
            strategy_name="loop",
            inputs={},
            routes={"next": "node2"},
            default_route="node2",
            constraints=[c] # Guard on Header
        )
        n2 = StrategyNode(
            id="node2",
            strategy_name="loop",
            inputs={},
            routes={"back": "start"},
            default_route="start"
        )

        plan = PlanTree(
            id="bounded_cyclic_header",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )

        # Should NOT raise error
        compile_graph(plan)

    def test_dominance_conditional_compliance(self):
        skill_guard = AtomicSkill(name="guard", version="1.0.0", definition={})
        skill_danger = AtomicSkill(
            name="danger",
            version="1.0.0",
            definition={},
            capabilities=["computer_use"]
        )
        skill_safe = AtomicSkill(name="safe", version="1.0.0", definition={})

        n_guard = ActionNode(id="guard", skill=skill_guard, inputs={}, outputs={}, locked=True, next_node="danger")
        n_danger = ActionNode(id="danger", skill=skill_danger, inputs={}, outputs={}, locked=False)
        n_safe = ActionNode(id="safe", skill=skill_safe, inputs={}, outputs={}, locked=False)

        n_start = StrategyNode(
            id="start",
            strategy_name="branch",
            inputs={},
            routes={"risky": "guard", "safe": "safe"},
            default_route="safe"
        )

        plan = PlanTree(
            id="conditional_compliance",
            root_node="start",
            nodes={
                "start": n_start,
                "guard": n_guard,
                "danger": n_danger,
                "safe": n_safe
            }
        )

        compile_graph(plan)

    def test_dominance_failure(self):
        skill_danger = AtomicSkill(
            name="danger",
            version="1.0.0",
            definition={},
            capabilities=["computer_use"]
        )

        n_start = StrategyNode(
            id="start",
            strategy_name="direct",
            inputs={},
            routes={"go": "danger"},
            default_route="danger",
            locked=False
        )
        n_danger = ActionNode(
            id="danger",
            skill=skill_danger,
            inputs={},
            outputs={},
            locked=False
        )

        plan = PlanTree(
            id="unsafe_plan",
            root_node="start",
            nodes={"start": n_start, "danger": n_danger}
        )

        with pytest.raises(ZeroTrustRoutingError, match="not dominated by any Locked Node"):
            compile_graph(plan)

    def test_ghost_cluster_rejection(self):
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        n_start = ActionNode(id="start", skill=skill, inputs={}, outputs={})
        n_ghost = ActionNode(id="ghost", skill=skill, inputs={}, outputs={})

        plan = PlanTree(
            id="ghost_plan",
            root_node="start",
            nodes={"start": n_start, "ghost": n_ghost}
        )

        with pytest.raises(ZeroTrustRoutingError, match="Graph contains unreachable nodes"):
            compile_graph(plan)

    def test_default_route_validation(self):
        """Test that default_route is validated."""
        n1 = StrategyNode(
            id="start",
            strategy_name="broken",
            inputs={},
            routes={},
            default_route="missing"
        )
        plan = PlanTree(id="p", root_node="start", nodes={"start": n1})
        with pytest.raises(ZeroTrustRoutingError, match="routes to unknown default_route"):
            compile_graph(plan)


class TestIntegrity:
    def test_hash_smuggling_prevention(self):
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        inputs_safe = {"user": "alice"}
        receipt_safe = generate_execution_receipt("e1", skill, inputs_safe, {})

        inputs_backdoor = {"user": "alice", "_hash_exclude_": ["user"]}
        receipt_backdoor = generate_execution_receipt("e2", skill, inputs_backdoor, {})

        inputs_dunder = {"user": "alice", "__hidden__": "payload"}
        receipt_dunder = generate_execution_receipt("e3", skill, inputs_dunder, {})

        assert receipt_safe.execution_hash != receipt_backdoor.execution_hash
        assert receipt_safe.execution_hash != receipt_dunder.execution_hash

        payload_dunder = reconstruct_payload(receipt_dunder)
        assert "__hidden__" in payload_dunder["inputs"]

        assert verify_merkle_proof([receipt_dunder]) is True

    def test_null_preservation(self):
        """Test that None values are PRESERVED in hash (RFC 8785 collision check)."""
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        # {a: 1} vs {a: 1, b: None} must be different
        inputs_none = {"a": 1, "b": None}
        inputs_missing = {"a": 1}

        r1 = generate_execution_receipt("e1", skill, inputs_none, {})
        r2 = generate_execution_receipt("e2", skill, inputs_missing, {})

        assert r1.execution_hash != r2.execution_hash

        # Verify reconstruction includes None
        p1 = reconstruct_payload(r1)
        assert "b" in p1["inputs"]
        assert p1["inputs"]["b"] is None


class TestLoaderSecurity:
    def test_jit_tool_authorization(self):
        with pytest.raises(SecurityViolationError):
            verify_tool_authorization("dangerous_tool")

        with scoped_tool_context({"safe_tool"}):
            verify_tool_authorization("safe_tool")

            with pytest.raises(SecurityViolationError):
                verify_tool_authorization("dangerous_tool")

        with pytest.raises(SecurityViolationError):
            verify_tool_authorization("safe_tool")
