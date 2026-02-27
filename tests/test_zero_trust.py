# tests/test_zero_trust.py

import pytest
from enum import Enum
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

    def test_cycle_detection_intermediate_constraint(self):
        """
        Test that a constraint on an intermediate node in the loop (not header or back-edge)
        is correctly detected via full path slicing.
        Loop: Start -> Intermediate (Constraint) -> End -> Start
        """
        c = Constraint(type="max_iterations", value=5)

        n_start = StrategyNode(id="start", strategy_name="s", inputs={}, routes={"next": "inter"}, default_route="inter")
        n_inter = StrategyNode(
            id="inter",
            strategy_name="s",
            inputs={},
            routes={"next": "end"},
            default_route="end",
            constraints=[c] # Constraint is here!
        )
        n_end = StrategyNode(id="end", strategy_name="s", inputs={}, routes={"back": "start"}, default_route="start")

        plan = PlanTree(
            id="intermediate_loop",
            root_node="start",
            nodes={"start": n_start, "inter": n_inter, "end": n_end}
        )

        compile_graph(plan) # Should pass

    def test_dominance_conditional_compliance(self):
        """Test SOTA Dominance Check with Guarded High-Risk Node."""
        skill_guard = AtomicSkill(name="guard", version="1.0.0", definition={})
        skill_danger = AtomicSkill(name="danger", version="1.0.0", definition={}, capabilities=["computer_use"])
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
                "start": n_start, "guard": n_guard, "danger": n_danger, "safe": n_safe
            }
        )

        compile_graph(plan)

    def test_dominance_failure(self):
        """Test failure when high-risk node is not guarded."""
        skill_danger = AtomicSkill(name="danger", version="1.0.0", definition={}, capabilities=["computer_use"])
        n_start = StrategyNode(id="start", strategy_name="direct", inputs={}, routes={"go": "danger"}, default_route="danger", locked=False)
        n_danger = ActionNode(id="danger", skill=skill_danger, inputs={}, outputs={}, locked=False)

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

    def test_validate_policy_ignores_unlocked(self):
        """
        Verify validate_policy does NOT throw error for unlocked dangerous node
        if it is topologically valid (compile_graph handles safety).
        """
        # This test ensures we removed the "Split-Brain" check.
        # We need a valid graph first.
        skill_danger = AtomicSkill(name="danger", version="1.0.0", definition={}, capabilities=["computer_use"])
        skill_guard = AtomicSkill(name="guard", version="1.0.0", definition={})

        # Valid guarded graph
        n_guard = ActionNode(id="guard", skill=skill_guard, inputs={}, outputs={}, locked=True, next_node="danger")
        n_danger = ActionNode(id="danger", skill=skill_danger, inputs={}, outputs={}, locked=False)

        plan = PlanTree(
            id="valid_policy",
            root_node="guard",
            nodes={"guard": n_guard, "danger": n_danger}
        )

        # Should pass compile_graph
        compile_graph(plan)

        # Should ALSO pass validate_policy without reports
        reports = validate_policy(plan)
        # We expect 0 reports because n_danger is unlocked but that's allowed by policy now (deferring to gatekeeper)
        assert len(reports) == 0


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

    def test_genesis_forgery_prevention(self):
        """Test prevention of floating unlinked nodes mid-trace."""
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        # 1. Valid Genesis
        r1 = generate_execution_receipt("e1", skill, {}, {})
        # 2. Valid Child
        r2 = generate_execution_receipt("e2", skill, {}, {}, parent_hash=r1.execution_hash)

        # 3. Forged Genesis (No parent) appended to trace
        r_forge = generate_execution_receipt("e_forge", skill, {}, {})

        trace = [r1, r2, r_forge]

        # verify_merkle_proof sorts the trace.
        # r_forge has no deps, so it might come first or last depending on sort stability/algo.
        # But verify logic iterates the sorted trace.
        # If r_forge is sorted to index 0, and r1 (also genesis) is index 1?
        # The genesis rule is: If parent list is empty -> Must be index 0.
        # If we have TWO genesis nodes, one will be at index 0, one at index > 0.
        # The one at index > 0 must fail.

        assert verify_merkle_proof(trace) is False

    def test_enum_serialization(self):
        """Test that Enums are flattened to values in hash computation."""
        class Color(str, Enum):
            RED = "red"
            BLUE = "blue"

        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        # Note: StrictJsonDict technically allows 'str', but Enum is not strictly 'str' in type checker
        # unless str, Enum. But at runtime it's an object.
        # Pydantic serializer handles it.
        # However, CanonicalHashingStrategy uses json.dumps which fails on Enums usually.
        # We rely on model_dump(mode='json') to convert Enum -> 'red'.

        inputs = {"color": Color.RED} # type: ignore (Enum matches str)

        # Should not raise TypeError
        receipt = generate_execution_receipt("e1", skill, inputs, {})

        payload = reconstruct_payload(receipt)
        assert payload["inputs"]["color"] == "red"


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
