# tests/test_zero_trust.py

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.contracts import (
    ActionNode,
    AtomicSkill,
    PlanTree,
    StrategyNode,
)
from coreason_manifest.utils.gatekeeper import compile_graph, ZeroTrustRoutingError
from coreason_manifest.utils.integrity import generate_execution_receipt, verify_merkle_proof
from coreason_manifest.utils.loader import scoped_tool_context, verify_tool_authorization
from coreason_manifest.utils.io import SecurityViolationError


class TestStrictContracts:
    def test_atomic_skill_immutability(self):
        """Test that AtomicSkill enforces strict typing and immutability."""
        skill = AtomicSkill(
            name="test_skill",
            version="1.0.0",
            definition={"input": "str", "output": "str"}
        )
        assert skill.immutable is True

        # Test frozen nature (pydantic frozen=True)
        with pytest.raises(ValidationError):
            skill.name = "new_name"

    def test_node_locking(self):
        """Test that nodes are locked by default."""
        skill = AtomicSkill(
            name="test_skill",
            version="1.0.0",
            definition={"input": "str", "output": "str"}
        )
        node = ActionNode(
            id="node_1",
            skill=skill,
            inputs={"arg": "var1"},
            outputs={"res": "var2"}
        )
        assert node.locked is True

    def test_forbid_extra_fields(self):
        """Test that extra fields are forbidden (Zero Trust Schema)."""
        with pytest.raises(ValidationError):
            AtomicSkill(
                name="test",
                version="1.0.0",
                definition={},
                extra_field="malicious_payload" # type: ignore
            )


class TestGatekeeper:
    def test_compile_valid_graph(self):
        """Test compilation of a valid linear graph."""
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        n1 = StrategyNode(
            id="start",
            strategy_name="direct",
            inputs={},
            routes={"default": "action_1"}
        )
        n2 = ActionNode(
            id="action_1",
            skill=skill,
            inputs={},
            outputs={}
        )

        plan = PlanTree(
            id="plan_1",
            root_node="start",
            nodes={"start": n1, "action_1": n2}
        )

        # Should pass
        compile_graph(plan)

    def test_detect_bypass_of_locked_node(self):
        """
        Test that graph compilation fails if a locked node is unreachable
        (Dead Code / Bypass attempt).
        """
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        # Root -> (No Route) ... LockedNode (Isolated)
        n1 = StrategyNode(
            id="start",
            strategy_name="noop",
            inputs={},
            routes={} # No routes defined!
        )
        n2 = ActionNode(
            id="critical_locked_node",
            skill=skill,
            inputs={},
            outputs={},
            # locked=True by default
        )

        plan = PlanTree(
            id="bad_plan",
            root_node="start",
            nodes={"start": n1, "critical_locked_node": n2}
        )

        with pytest.raises(ZeroTrustRoutingError) as exc:
            compile_graph(plan)

        assert "unreachable" in str(exc.value)

    def test_missing_route_target(self):
        """Test failure when routing to non-existent node."""
        n1 = StrategyNode(
            id="start",
            strategy_name="direct",
            inputs={},
            routes={"default": "missing_node"}
        )

        plan = PlanTree(
            id="broken_link",
            root_node="start",
            nodes={"start": n1}
        )

        with pytest.raises(ZeroTrustRoutingError) as exc:
            compile_graph(plan)

        assert "unknown node" in str(exc.value)

    def test_empty_plan(self):
        plan = PlanTree(
            id="empty",
            root_node="start",
            nodes={}
        )
        with pytest.raises(ZeroTrustRoutingError, match="Plan is empty"):
            compile_graph(plan)

    def test_missing_root_node(self):
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        n1 = ActionNode(id="n1", skill=skill, inputs={}, outputs={})
        plan = PlanTree(
            id="missing_root",
            root_node="start",
            nodes={"n1": n1}
        )
        with pytest.raises(ZeroTrustRoutingError, match="Root node start not found"):
            compile_graph(plan)

    def test_cycle_detection(self):
        """Test that cycles are detected (coverage only, currently allowed)."""
        # start -> node2 -> start
        n1 = StrategyNode(id="start", strategy_name="loop", inputs={}, routes={"next": "node2"})
        n2 = StrategyNode(id="node2", strategy_name="loop", inputs={}, routes={"back": "start"})

        plan = PlanTree(
            id="cyclic",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )
        # Should not raise exception currently, but logic should run
        compile_graph(plan)


class TestIntegrity:
    def test_execution_receipt_generation(self):
        """Test generation of PoTE receipt."""
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})
        inputs = {"a": 1}
        outputs = {"b": 2}

        receipt = generate_execution_receipt(
            execution_id="exec_1",
            skill=skill,
            inputs=inputs,
            outputs=outputs
        )

        assert receipt.locked_status is True
        assert receipt.execution_hash is not None
        assert receipt.timestamp is not None
        # Verify Canonical Hashing is deterministic
        assert receipt.execution_hash == generate_execution_receipt(
             execution_id="exec_1",
             skill=skill,
             inputs=inputs,
             outputs=outputs
        ).execution_hash

    def test_merkle_verification(self):
        """Test the basic merkle verification logic with PoTEs."""
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        # Create a trace
        receipt1 = generate_execution_receipt("e1", skill, {}, {})
        receipt2 = generate_execution_receipt("e2", skill, {}, {}, parent_hash=receipt1.execution_hash)

        trace = [receipt1, receipt2]

        # Verify
        assert verify_merkle_proof(trace) is True

        # Tamper
        trace[0] = trace[0].model_copy(update={"execution_hash": "fake"})
        assert verify_merkle_proof(trace) is False


class TestLoaderSecurity:
    def test_jit_tool_authorization(self):
        """Test ephemeral tool authorization context."""

        # 1. No context -> Fail
        with pytest.raises(SecurityViolationError):
            verify_tool_authorization("dangerous_tool")

        # 2. Context allowed
        with scoped_tool_context({"safe_tool"}):
            verify_tool_authorization("safe_tool") # Should pass

            with pytest.raises(SecurityViolationError):
                verify_tool_authorization("dangerous_tool")

        # 3. Context exited -> Fail again
        with pytest.raises(SecurityViolationError):
            verify_tool_authorization("safe_tool")
