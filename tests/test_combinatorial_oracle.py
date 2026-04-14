# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from coreason_manifest.oracles.combinatorial import CombinatorialSolverOracle
from coreason_manifest.spec.ontology import EpistemicLogicPremise


def test_combinatorial_oracle_sat() -> None:
    premise = EpistemicLogicPremise(
        asp_program="""
node(1..3).
color(r;g;b).
1 { assign(N, C) : color(C) } 1 :- node(N).
:- assign(1, C), assign(2, C).
""",
    )
    receipt = CombinatorialSolverOracle.solve(
        premise=premise,
        event_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        provenance_id="did:coreason:bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
    )
    assert receipt.satisfiability == "SATISFIABLE"
    assert receipt.counter_model is None
    assert len(receipt.answer_sets) > 0


def test_combinatorial_oracle_unsat() -> None:
    # 3 pigeons in 2 holes, must be exclusive
    premise = EpistemicLogicPremise(
        asp_program="""
pigeon(1..3).
hole(1..2).
1 { assign(P, H) : hole(H) } 1 :- pigeon(P).
:- assign(P1, H), assign(P2, H), P1 != P2.
""",
    )
    receipt = CombinatorialSolverOracle.solve(
        premise=premise,
        event_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        provenance_id="did:coreason:bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
    )
    assert receipt.satisfiability == "UNSATISFIABLE"
    assert receipt.counter_model is not None
    assert "pigeon((1..3))." in receipt.counter_model.unsat_core
    assert "1 <= { assign(P,H): hole(H) } <= 1 :- pigeon(P)." in receipt.counter_model.unsat_core
    assert "#false :- assign(P1,H); assign(P2,H); P1 != P2." in receipt.counter_model.unsat_core
    assert len(receipt.counter_model.unsat_core) == 3


def test_combinatorial_oracle_syntax_error() -> None:
    premise = EpistemicLogicPremise(
        asp_program="""
this is not valid ASP code!
node(1..3
""",
    )
    receipt = CombinatorialSolverOracle.solve(
        premise=premise,
        event_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        provenance_id="did:coreason:bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
    )
    assert receipt.satisfiability == "UNKNOWN"
    assert receipt.counter_model is not None
    assert len(receipt.counter_model.unsat_core) > 0
    assert "syntax error" in receipt.counter_model.unsat_core[0].lower()


def test_combinatorial_oracle_thermodynamic_guillotine() -> None:
    # A payload that creates a massive search space or infinite loop to trigger timeout
    premise = EpistemicLogicPremise(
        asp_program="a(1..1000). b(X,Y,Z) :- a(X), a(Y), a(Z).",
    )
    import time

    t0 = time.time()
    receipt = CombinatorialSolverOracle.solve(
        premise=premise,
        event_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        provenance_id="did:coreason:bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        timeout_ms=100,
    )
    t1 = time.time()

    elapsed_ms = (t1 - t0) * 1000
    # It should terminate near 100ms
    assert elapsed_ms < 5000, f"Execution took too long: {elapsed_ms}ms"

    assert receipt.satisfiability == "UNKNOWN"
    assert receipt.counter_model is not None
    assert "Execution terminated: Thermodynamic bound exceeded (SIGKILL applied)." in receipt.counter_model.unsat_core
