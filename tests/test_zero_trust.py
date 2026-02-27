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
        c = Constraint(type="max_iterations", value=5)
        n1 = StrategyNode(
            id="start",
            strategy_name="loop",
            inputs={},
            routes={"next": "node2"}
        )
        # Put constraint on the node that loops back
        n2 = StrategyNode(
            id="node2",
            strategy_name="loop",
            inputs={},
            routes={"back": "start"},
            constraints=[c]
        )

        plan = PlanTree(
            id="bounded_cyclic",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )

        # Should NOT raise error
        compile_graph(plan)

    def test_dominance_conditional_compliance(self):
        """
        Test SOTA Dominance Check:
        Route A: Dangerous Node (Computer Use) -> MUST be dominated by Locked Guard.
        Route B: Safe Node -> Need NOT be dominated by Locked Guard.
        """
        skill_guard = AtomicSkill(name="guard", version="1.0.0", definition={})
        skill_danger = AtomicSkill(
            name="danger",
            version="1.0.0",
            definition={},
            capabilities=["computer_use"]
        )
        skill_safe = AtomicSkill(name="safe", version="1.0.0", definition={})

        # Guard Node (Locked)
        n_guard = ActionNode(id="guard", skill=skill_guard, inputs={}, outputs={}, locked=True)
        # Dangerous Node (Unlocked itself, but must be guarded)
        n_danger = ActionNode(id="danger", skill=skill_danger, inputs={}, outputs={}, locked=False)
        # Safe Node
        n_safe = ActionNode(id="safe", skill=skill_safe, inputs={}, outputs={}, locked=False)

        # Locked Strategy Node (The Guard)
        n_guard_strat = StrategyNode(
            id="guard_strat",
            strategy_name="approval",
            inputs={},
            routes={"approved": "danger"},
            locked=True
        )

        # Start Node: Define routes correctly at initialization
        n_start = StrategyNode(
            id="start",
            strategy_name="branch",
            inputs={},
            routes={"risky": "guard_strat", "safe": "safe"}
        )

        plan = PlanTree(
            id="conditional_compliance",
            root_node="start",
            nodes={
                "start": n_start,
                "guard_strat": n_guard_strat, # Locked
                "danger": n_danger,           # High Risk
                "safe": n_safe                # Safe
            }
        )

        # High Risk Node: "danger".
        # Dom(danger) = {start, guard_strat, danger}.
        # Locked Nodes = {guard_strat}.
        # Intersection = {guard_strat}. NOT EMPTY. -> Valid.

        compile_graph(plan) # Should Pass

    def test_dominance_failure(self):
        """Test that missing the guard for a high-risk node fails."""
        skill_danger = AtomicSkill(
            name="danger",
            version="1.0.0",
            definition={},
            capabilities=["computer_use"]
        )

        # Unlocked path to danger
        n_start = StrategyNode(
            id="start",
            strategy_name="direct",
            inputs={},
            routes={"go": "danger"},
            locked=False
        )
        n_danger = ActionNode(
            id="danger",
            skill=skill_danger,
            inputs={},
            outputs={},
            locked=False # Not self-locking
        )

        plan = PlanTree(
            id="unsafe_plan",
            root_node="start",
            nodes={"start": n_start, "danger": n_danger}
        )

        # Dom(danger) = {start, danger}. Locked = {}. Intersection Empty.

        with pytest.raises(ZeroTrustRoutingError, match="not dominated by any Locked Node"):
            compile_graph(plan)


class TestIntegrity:
    def test_hash_smuggling_prevention(self):
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        inputs_safe = {"user": "alice"}
        receipt_safe = generate_execution_receipt("e1", skill, inputs_safe, {})

        # Include _hash_exclude_ to ensure it is NOT stripped (backdoor removal check)
        inputs_backdoor = {"user": "alice", "_hash_exclude_": {"user"}}
        receipt_backdoor = generate_execution_receipt("e2", skill, inputs_backdoor, {})

        # If backdoor worked (was stripped), hash might match safe (if 'user' was excluded)?
        # No, _hash_exclude_ itself would be stripped, and 'user' would be stripped.
        # Result: inputs={}.
        # Safe inputs={"user": "alice"}.
        # Hashes would differ regardless.
        # But we want to prove `_hash_exclude_` is INCLUDED in the hash.

        payload = reconstruct_payload(receipt_backdoor)
        assert "_hash_exclude_" in payload["inputs"]

        assert verify_merkle_proof([receipt_backdoor]) is True


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
