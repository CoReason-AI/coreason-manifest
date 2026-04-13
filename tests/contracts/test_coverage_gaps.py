# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Introspective Canonical Sort Determinism Tests.

This module implements a scalable, self-maintaining test harness that
introspects the ontology at import time to automatically discover every
``@model_validator`` that enforces canonical array sorting. It then
generates a parametrized test case per validator, guaranteeing RFC 8785
determinism without requiring manual per-class test authorship.

The approach is consistent with the CoReason test philosophy:
- **Scalable**: New schema classes with canonical sort validators are
  automatically picked up by the introspection engine.
- **Negative-space**: Tests exercise the validator by constructing
  reversed-order inputs and asserting post-validation sort invariants.
- **Maintainable**: No hand-crafted field signatures; uses
  ``model_construct`` + manual validator invocation to bypass field-level
  constraints while still exercising the validator body.

Additionally, targeted tests cover specific validator error paths,
the ``compile_to_base_topology`` method, the ``_SimpleTTLCache`` eviction
path, and the ``align_semantic_manifolds`` utility function.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from typing import Any, cast

import pytest
from pydantic import BaseModel

from coreason_manifest.spec import ontology as o

# ---------------------------------------------------------------------------
# §1. INTROSPECTIVE CANONICAL SORT DISCOVERY ENGINE
# ---------------------------------------------------------------------------
# Automatically discovers all @model_validator methods that perform
# canonical array sorting via `object.__setattr__` + `sorted(...)`.


def _discover_canonical_sort_validators() -> list[
    tuple[str, type[o.CoreasonBaseState], str, list[tuple[str, str | None]]]
]:
    """Introspect the ontology module to find every canonical sort validator.

    Returns a list of tuples:
        (test_id, cls, validator_name, [(field_name, attrgetter_key | None), ...])

    where ``attrgetter_key`` is the sort key for complex objects, or None for
    simple string/int lists sorted by identity.
    """
    # Validators that perform structural integrity checks beyond sorting,
    # or use non-standard sort keys (lambdas, enum .value access).
    # These are tested by their own dedicated test modules.
    excluded_validators: set[str] = {
        "CyclicEdgeProfile::_enforce_structural_integrity_mapping",
        "TransitionEdgeProfile::_enforce_structural_integrity",
        "WorkflowManifest::_enforce_canonical_sort",
        "DynamicRoutingManifest::_enforce_canonical_sort",
    }

    results: list[tuple[str, type[o.CoreasonBaseState], str, list[tuple[str, str | None]]]] = []

    for name in dir(o):
        cls = getattr(o, name, None)
        if not (inspect.isclass(cls) and issubclass(cls, o.CoreasonBaseState) and cls is not o.CoreasonBaseState):
            continue

        # Scan all methods for canonical sort patterns
        for attr_name in dir(cls):
            if not attr_name.startswith(("_enforce", "_sort")):
                continue

            test_id = f"{name}::{attr_name}"
            if test_id in excluded_validators:
                continue

            method = getattr(cls, attr_name, None)
            if method is None:
                continue

            try:
                target = method.fget if isinstance(method, property) else method
                source = inspect.getsource(cast("Callable[..., Any]", target))
            except TypeError, OSError:
                continue

            # Skip methods that raise ValueError (structural integrity, not pure sorting)
            if "raise ValueError" in source:
                continue

            # Parse sorted(...) calls from the source
            # Pattern: object.__setattr__(self, "field_name", sorted(self.field_name, key=...))
            field_sort_pattern = re.compile(
                r'object\.__setattr__\(\s*self,\s*"(\w+)",\s*sorted\(\s*self\.\w+,?\s*'
                r"(?:key=operator\.attrgetter\(([^)]+)\))?\s*\)",
                re.DOTALL,
            )
            fields: list[tuple[str, str | None]] = []
            for match in field_sort_pattern.finditer(source):
                field_name = match.group(1)
                attrgetter_args = match.group(2)
                sort_key: str | None = None
                if attrgetter_args:
                    key_match = re.search(r'"(\w+)"', attrgetter_args)
                    if key_match:
                        sort_key = key_match.group(1)
                fields.append((field_name, sort_key))

            if fields:
                results.append((test_id, cls, attr_name, fields))

    return results


_CANONICAL_SORT_CASES = _discover_canonical_sort_validators()


def _build_unsorted_field_data(
    cls: type[o.CoreasonBaseState],
    field_name: str,
    sort_key: str | None,
) -> list[Any]:
    """Build a minimal 2-element list in reverse-sorted order for a given field."""
    field_info = cls.model_fields.get(field_name)
    if field_info is None:
        return []

    annotation_str = str(field_info.annotation)

    if sort_key is not None:
        # Complex object list — need to build minimal stub objects via model_construct
        # Determine the element type from the field annotation
        inner_type = _resolve_list_element_type(cls, field_name)
        if inner_type is None:
            return []

        # Build two instances with reversed sort keys
        obj_a = _build_stub(inner_type, {sort_key: "aaa-first"})
        obj_z = _build_stub(inner_type, {sort_key: "zzz-last"})
        if obj_a is None or obj_z is None:
            return []
        return [obj_z, obj_a]  # Reversed order

    # Simple list[str] or list[int]
    if "int" in annotation_str.lower():
        return [9, 1, 5]
    return ["zzz-last", "aaa-first"]


def _resolve_list_element_type(cls: type, field_name: str) -> type | None:
    """Resolve the element type of a list field."""
    import typing

    if not (inspect.isclass(cls) and issubclass(cls, BaseModel)):
        return None

    field_info = cls.model_fields.get(field_name)
    if field_info is None:
        return None

    annotation = field_info.annotation
    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        args = typing.get_args(annotation)
        if args:
            elem = args[0]
            if inspect.isclass(elem) and issubclass(elem, o.CoreasonBaseState):
                return elem
    # Try ForwardRef resolution
    anno_str = str(annotation)
    if "ForwardRef" in anno_str:
        # Extract class name from ForwardRef
        match = re.search(r"'(\w+)'", anno_str)
        if match:
            ref_name = match.group(1)
            resolved = getattr(o, ref_name, None)
            if inspect.isclass(resolved):
                return cast("type", resolved)
    return None


def _build_stub(cls: type, overrides: dict[str, Any]) -> Any:
    """Build a minimal instance of a Pydantic model via model_construct."""
    if not hasattr(cls, "model_construct"):
        return None

    # Populate required fields with minimal valid stubs
    defaults: dict[str, Any] = {}
    if not (inspect.isclass(cls) and issubclass(cls, BaseModel)):
        return None
    for fname, finfo in cls.model_fields.items():
        if not finfo.is_required():
            continue
        if fname in overrides:
            continue
        annotation = finfo.annotation
        anno_str = str(annotation)
        if annotation is str or "str" in anno_str[:20]:
            defaults[fname] = f"stub-{fname}"
        elif annotation is float:
            defaults[fname] = 0.5
        elif annotation is int:
            defaults[fname] = 1
        elif annotation is bool:
            defaults[fname] = False
        else:
            defaults[fname] = f"stub-{fname}"

    defaults.update(overrides)
    try:
        return cls.model_construct(**defaults)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# §2. PARAMETRIZED CANONICAL SORT INVARIANT TEST
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("test_id", "cls", "validator_name", "fields"),
    _CANONICAL_SORT_CASES,
    ids=[case[0] for case in _CANONICAL_SORT_CASES],
)
def test_canonical_sort_determinism(
    test_id: str,
    cls: type[o.CoreasonBaseState],
    validator_name: str,
    fields: list[tuple[str, str | None]],
) -> None:
    """RFC 8785 Determinism: Asserts that every discovered canonical sort
    validator produces a monotonically non-decreasing sequence after
    invocation, regardless of input order.

    Uses ``model_construct`` to build instances without triggering
    field-level Pydantic validation (which may reject stub data),
    then manually invokes the sort validator to exercise only the
    sorting logic.
    """
    # Build initial data with all sorted fields in reverse order
    construct_args: dict[str, Any] = {}
    field_expectations: list[tuple[str, str | None]] = []

    for field_name, sort_key in fields:
        data = _build_unsorted_field_data(cls, field_name, sort_key)
        if not data:
            continue
        construct_args[field_name] = data
        field_expectations.append((field_name, sort_key))

    if not construct_args:
        pytest.skip(f"Could not build test data for {test_id}")

    # Fill remaining required fields with stubs
    for fname, finfo in cls.model_fields.items():
        if fname not in construct_args and finfo.is_required():
            annotation = finfo.annotation
            anno_str = str(annotation)
            if annotation is str or "str" in anno_str[:20]:
                construct_args[fname] = f"stub-{fname}"
            elif annotation is float:
                construct_args[fname] = 0.5
            elif annotation is int:
                construct_args[fname] = 1
            elif annotation is bool:
                construct_args[fname] = False
            elif "list" in anno_str.lower():
                construct_args[fname] = []
            elif "dict" in anno_str.lower():
                construct_args[fname] = {}
            else:
                construct_args[fname] = f"stub-{fname}"

    # Construct without validation, then invoke the validator
    instance = cls.model_construct(**construct_args)
    validator_method = getattr(instance, validator_name, None)
    assert validator_method is not None, f"Validator {validator_name} not found on {cls.__name__}"

    result = validator_method()

    # Assert monotonic sort invariant for each field
    for field_name, sort_key in field_expectations:
        sorted_field = getattr(result, field_name, None)
        assert sorted_field is not None, f"Field {field_name} missing after sort"
        assert len(sorted_field) >= 2, f"Field {field_name} has fewer than 2 elements"

        if sort_key:
            keys = [getattr(elem, sort_key, None) for elem in sorted_field]
            sortable_keys = [k for k in keys if k is not None]
            assert sortable_keys == sorted(sortable_keys), (
                f"{cls.__name__}.{field_name}: Sort invariant violated. "
                f"Expected monotonic ordering by '{sort_key}', got {keys}"
            )
        else:
            assert list(sorted_field) == sorted(sorted_field), (
                f"{cls.__name__}.{field_name}: Sort invariant violated. Expected sorted list, got {list(sorted_field)}"
            )


# ---------------------------------------------------------------------------
# §3. TARGETED VALIDATOR ERROR PATH TESTS
# ---------------------------------------------------------------------------


class TestEmpiricalStatisticalProfileInterval:
    """Boundary geometry test for lower_bound < upper_bound invariant."""

    def test_valid_interval_passes(self) -> None:
        obj = o.EmpiricalStatisticalProfile(
            qualifier_type="confidence_interval",
            algebraic_operator="lt",
            value=0.05,
            lower_bound=0.01,
            upper_bound=0.09,
        )
        assert obj.lower_bound == 0.01

    def test_invalid_interval_rejected(self) -> None:
        with pytest.raises(ValueError, match="lower_bound"):
            o.EmpiricalStatisticalProfile(
                qualifier_type="confidence_interval",
                algebraic_operator="lt",
                value=0.05,
                lower_bound=0.09,
                upper_bound=0.01,
            )


class TestExogenousEpistemicEventEscrow:
    """Zero-escrow injection must be rejected."""

    def test_zero_escrow_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"[Ee]scrow"):
            o.ExogenousEpistemicEvent(
                event_cid="test-cid",
                timestamp=1000.0,
                shock_cid="shock-1",
                target_node_hash="a" * 64,
                bayesian_surprise_score=5.0,
                synthetic_payload={"key": "val"},
                escrow=o.SimulationEscrowContract(locked_magnitude=0),
            )


class TestConsensusFederationAdjudicatorIsolation:
    """Adjudicator cannot be a participant (Byzantine separation)."""

    def test_adjudicator_in_participants_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"[Aa]djudicator"):
            o.ConsensusFederationTopologyManifest(
                participant_cids=["did:a:1", "did:a:2", "did:a:3"],
                adjudicator_cid="did:a:1",
                quorum_rules=o.QuorumPolicy(
                    max_tolerable_faults=1,
                    min_quorum_size=4,
                    state_validation_metric="ledger_hash",
                    byzantine_action="quarantine",
                ),
            )


class TestPredictionMarketEmptyProbabilities:
    """Empty probability map must short-circuit validation."""

    def test_empty_probabilities_returns_early(self) -> None:
        obj = o.PredictionMarketState(
            market_cid="mkt-1",
            resolution_oracle_condition_cid="cond-1",
            lmsr_b_parameter="100.0",
            order_book=[],
            current_market_probabilities={},
        )
        assert obj.current_market_probabilities == {}


class TestGenerativeTaxonomyDagIntegrity:
    """Root node must exist in the taxonomy nodes dict."""

    def test_valid_root_succeeds(self) -> None:
        node = o.TaxonomicNodeState(node_cid="root-1", semantic_label="root")
        obj = o.GenerativeTaxonomyManifest(
            manifest_cid="test-cid",
            root_node_cid="root-1",
            nodes={"root-1": node},
        )
        assert obj.root_node_cid == "root-1"

    def test_missing_root_rejected(self) -> None:
        node = o.TaxonomicNodeState(node_cid="other-1", semantic_label="other")
        with pytest.raises(ValueError, match=r"[Rr]oot"):
            o.GenerativeTaxonomyManifest(
                manifest_cid="test-cid",
                root_node_cid="missing-root",
                nodes={"other-1": node},
            )


# ---------------------------------------------------------------------------
# §4. COMPILE-TO-BASE-TOPOLOGY
# ---------------------------------------------------------------------------


class TestConsensusFederationCompile:
    """Verify the macro topology can compile to a base council topology."""

    def test_compile_produces_topology(self) -> None:
        macro = o.ConsensusFederationTopologyManifest(
            participant_cids=["did:a:1", "did:a:2", "did:a:3"],
            adjudicator_cid="did:a:4",
            quorum_rules=o.QuorumPolicy(
                max_tolerable_faults=1,
                min_quorum_size=4,
                state_validation_metric="ledger_hash",
                byzantine_action="quarantine",
            ),
        )
        result = macro.compile_to_base_topology()
        assert result is not None


# ---------------------------------------------------------------------------
# §5. TTL CACHE EVICTION
# ---------------------------------------------------------------------------


class TestSimpleTTLCacheEviction:
    """Exercise the maxsize overflow eviction path."""

    def test_cache_clears_on_overflow(self) -> None:
        cache = o._SimpleTTLCache(ttl=60, maxsize=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") == 1
        # 4th entry triggers full clear
        cache.set("d", 4)
        assert cache.get("a") is None
        assert cache.get("d") == 4


# ---------------------------------------------------------------------------
# §6. ALGEBRA.PY SEMANTIC GRAPH BRANCH
# ---------------------------------------------------------------------------


class TestAlgebraSemanticGraphBranch:
    """Exercise the semantic_graph modality branch in align_semantic_manifolds."""

    def test_semantic_graph_modality(self) -> None:
        from coreason_manifest.utils.algebra import align_semantic_manifolds

        result = align_semantic_manifolds(
            task_cid="task-1",
            source_modalities=["text"],
            target_modalities=["text", "semantic_graph"],  # type: ignore[list-item]
            artifact_event_cid="evt-1",
        )
        assert result is not None


# ---------------------------------------------------------------------------
# §7. SERIALIZER ROUND-TRIP COVERAGE
# ---------------------------------------------------------------------------


class TestFormalLogicProofReceiptSerializer:
    """Verify answer_sets serialization round-trip."""

    def test_answer_sets_serializer(self) -> None:
        obj = o.FormalLogicProofReceipt(
            causal_provenance_id="did:a:1",
            event_cid="test-cid",
            timestamp=1000.0,
            satisfiability="SATISFIABLE",
            answer_sets=[["a", "b"], ["c"]],
        )
        data = obj.model_dump(mode="json")
        assert data["answer_sets"] == [["a", "b"], ["c"]]


class TestPrologDeductionReceiptSerializer:
    """Verify variable_bindings dict key canonical sorting."""

    def test_variable_bindings_sorted_keys(self) -> None:
        obj = o.PrologDeductionReceipt(
            causal_provenance_id="did:a:1",
            event_cid="test-cid",
            timestamp=1000.0,
            truth_value=True,
            variable_bindings=[{"z_var": "value", "a_var": "value"}],
        )
        data = obj.model_dump(mode="json")
        keys = list(data["variable_bindings"][0].keys())
        assert keys == ["a_var", "z_var"]
