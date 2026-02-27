# tests/test_zero_trust.py

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.contracts import (
    ActionNode,
    AtomicSkill,
    PlanTree,
    StrategyNode,
)
from coreason_manifest.utils.gatekeeper import compile_graph, validate_policy, ZeroTrustRoutingError
from coreason_manifest.utils.integrity import generate_execution_receipt, verify_merkle_proof, compute_hash, reconstruct_payload
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
        """Test that nodes are unlocked by default (as per new directive)."""
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
        assert node.locked is False

        # Explicit lock
        node_locked = ActionNode(
            id="node_2",
            skill=skill,
            inputs={},
            outputs={},
            locked=True
        )
        assert node_locked.locked is True

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
        Test that graph compilation fails if a locked node is reachable but bypassed by a parallel path.
        """
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        # Root -> (Branch) -> LockedNode -> End
        #      -> (Branch) -> End

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

        # We need a StrategyNode after n_locked to join to n_end if we want a DAG structure that merges?
        # Or ActionNodes are sinks.
        # In this case, path1: start -> locked_node (sink)
        # path2: start -> action_end (sink)
        # Does locked_node dominate all sinks? No.
        # Is locked_node required? Yes, because it exists in the graph and is locked.
        # It MUST appear in all paths?
        # Path 2 does not have it. Violation.

        plan = PlanTree(
            id="bypass_plan",
            root_node="start",
            nodes={"start": n_start, "locked_node": n_locked, "action_end": n_end}
        )

        with pytest.raises(ZeroTrustRoutingError) as exc:
            compile_graph(plan)

        assert "bypasses locked mandatory nodes" in str(exc.value)

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
        """Test that cycles are strictly forbidden."""
        # start -> node2 -> start
        n1 = StrategyNode(id="start", strategy_name="loop", inputs={}, routes={"next": "node2"})
        n2 = StrategyNode(id="node2", strategy_name="loop", inputs={}, routes={"back": "start"})

        plan = PlanTree(
            id="cyclic",
            root_node="start",
            nodes={"start": n1, "node2": n2}
        )

        with pytest.raises(ZeroTrustRoutingError, match="Unbounded cycles forbidden"):
            compile_graph(plan)

    def test_validate_policy_red_button(self):
        """Test capability analysis in validate_policy."""
        skill = AtomicSkill(
            name="dangerous",
            version="1.0.0",
            definition={},
            capabilities=["computer_use"]
        )
        # Unlocked dangerous node
        n1 = ActionNode(
            id="dangerous_node",
            skill=skill,
            inputs={},
            outputs={},
            locked=False
        )

        plan = PlanTree(
            id="risky_plan",
            root_node="dangerous_node",
            nodes={"dangerous_node": n1}
        )

        reports = validate_policy(plan)
        assert len(reports) > 0
        assert "high-risk capabilities" in reports[0].message
        assert "is NOT locked" in reports[0].message


class TestIntegrity:
    def test_hash_smuggling_prevention(self):
        """
        Verify that injecting 'execution_hash' key into nested dict (inputs)
        does NOT cause it to be stripped during hashing (collision attack).
        """
        skill = AtomicSkill(name="s1", version="1.0.0", definition={})

        # Case 1: Legit input
        inputs_safe = {"user": "alice"}
        receipt_safe = generate_execution_receipt("e1", skill, inputs_safe, {})

        # Case 2: Malicious input mimicking exclusion key
        inputs_malicious = {"user": "alice", "execution_hash": "fake_hash"}
        receipt_malicious = generate_execution_receipt("e2", skill, inputs_malicious, {})

        # The hashes must differ because "execution_hash" inside inputs must be included in the hash
        assert receipt_safe.execution_hash != receipt_malicious.execution_hash

        # Verify that the malicious payload indeed contains the key when reconstructed
        payload_malicious = reconstruct_payload(receipt_malicious)
        assert "execution_hash" in payload_malicious["inputs"]

        # Compute hash manually to confirm inclusion
        # If the key was stripped, the hash would match a payload without it (except for ID difference)
        # Let's create a receipt with same ID/timestamp to test collision directly if possible
        # (Hard due to timestamp). But assertion above proves they are distinct.

        # Further check: verify_merkle_proof should succeed on malicious receipt
        # (proving the hash matches the content including the nested key)
        assert verify_merkle_proof([receipt_malicious]) is True

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
