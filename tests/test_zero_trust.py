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
                    "routes": {}
                }
            }
        }

        plan = PlanTree.model_validate(data)
        assert isinstance(plan.nodes["n1"], ActionNode)
        assert isinstance(plan.nodes["n2"], StrategyNode)


class TestGatekeeper:
    def test_cycle_detection_strict(self):
        """Test that unbounded cycles are rejected."""
        # start -> node2 -> start (No Constraint)
        n1 = StrategyNode(id="start", strategy_name="loop", inputs={}, routes={"next": "node2"})
        n2 = StrategyNode(id="node2", strategy_name="loop", inputs={}, routes={"back": "start"})

        plan = PlanTree(
            id="cyclic",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )

        with pytest.raises(ZeroTrustRoutingError, match="Unbounded cycle detected"):
            compile_graph(plan)

    def test_cycle_detection_bounded_allowed(self):
        """Test that bounded cycles (with Constraint) are allowed."""
        # start -> node2 -> start (With Constraint)
        c = Constraint(type="max_iterations", value=5)
        n1 = StrategyNode(
            id="start",
            strategy_name="loop",
            inputs={},
            routes={"next": "node2"}
        )
        # The back-edge node (n2) must be guarded to allow the jump back
        n2 = StrategyNode(
            id="node2",
            strategy_name="loop",
            inputs={},
            routes={"back": "start"},
            constraints=[c] # Guard
        )

        plan = PlanTree(
            id="bounded_cyclic",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )

        # Should NOT raise error
        compile_graph(plan)

    def test_detect_bypass_of_locked_node(self):
        """
        Test that graph compilation fails if a locked node is reachable but bypassed by a parallel path.
        """
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        n_start = StrategyNode(
            id="start",
            strategy_name="branch",
            inputs={},
            routes={"path1": "locked_node", "path2": "action_end"}
        )

        n_locked = ActionNode(
            id="locked_node",
            skill=skill,
            inputs={},
            outputs={},
            locked=True
        )

        n_end = ActionNode(
            id="action_end",
            skill=skill,
            inputs={},
            outputs={}
        )

        plan = PlanTree(
            id="bypass_plan",
            root_node="start",
            nodes={"start": n_start, "locked_node": n_locked, "action_end": n_end}
        )

        with pytest.raises(ZeroTrustRoutingError, match="bypasses locked mandatory nodes"):
            compile_graph(plan)


class TestIntegrity:
    def test_hash_smuggling_prevention(self):
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        inputs_safe = {"user": "alice"}
        receipt_safe = generate_execution_receipt("e1", skill, inputs_safe, {})

        inputs_malicious = {"user": "alice", "execution_hash": "fake_hash"}
        receipt_malicious = generate_execution_receipt("e2", skill, inputs_malicious, {})

        assert receipt_safe.execution_hash != receipt_malicious.execution_hash

        payload_malicious = reconstruct_payload(receipt_malicious)
        assert "execution_hash" in payload_malicious["inputs"]

        assert verify_merkle_proof([receipt_malicious]) is True


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
