# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import threading
import time

import clingo
from clingo.ast import ASTType, Function, Literal, ProgramBuilder, Sign, SymbolicAtom, Transformer, parse_string
from clingo.control import Control

from coreason_manifest.spec.ontology import (
    CombinatorialCounterModel,
    EpistemicLogicPremise,
    FormalLogicProofReceipt,
)


class AssumptionTransformer(Transformer):
    def __init__(self, rule_map: dict[str, str]):
        self.rule_idx = 0
        self.rule_map = rule_map

    def visit_Rule(self, rule: clingo.ast.AST) -> clingo.ast.AST:  # noqa: N802
        idx = self.rule_idx
        self.rule_idx += 1

        assumption_name = f"__assume_{idx}"
        self.rule_map[assumption_name] = str(rule)

        loc = rule.location
        fun = Function(loc, assumption_name, [], 0)
        sym_atom = SymbolicAtom(fun)
        lit = Literal(loc, Sign.NoSign, sym_atom)

        new_body = [*list(rule.body), lit]
        return rule.update(body=new_body)


class CombinatorialSolverOracle:
    """The combinatorial execution bridge between the Python ontology and the C-backed clingo engine."""

    @staticmethod
    def solve(
        premise: EpistemicLogicPremise, event_cid: str, provenance_id: str, timeout_ms: int = 10000
    ) -> FormalLogicProofReceipt:
        ctl = Control(["0"])

        timeout_sec = timeout_ms / 1000.0

        def interrupt() -> None:
            ctl.interrupt()

        timer = threading.Timer(timeout_sec, interrupt)

        try:
            parsed_rules = []

            def on_statement(stm: clingo.ast.AST) -> None:
                parsed_rules.append(stm)

            try:
                parse_string(premise.asp_program, on_statement)
            except RuntimeError as e:
                # Syntax hallucination handling
                return FormalLogicProofReceipt(
                    satisfiability="UNKNOWN",
                    event_cid=event_cid,
                    causal_provenance_id=provenance_id,
                    timestamp=time.time(),
                    counter_model=CombinatorialCounterModel(
                        failed_premise_cid=provenance_id,
                        unsat_core=[str(e)[:2000]],
                    ),
                    answer_sets=[],
                )

            rule_map: dict[str, str] = {}
            transformer = AssumptionTransformer(rule_map)

            with ProgramBuilder(ctl) as builder:
                for stm in parsed_rules:
                    if stm.ast_type == ASTType.Rule:
                        new_stm = transformer(stm)
                        builder.add(new_stm)

                        parsed_choice: list[clingo.ast.AST] = []

                        def on_choice(s: clingo.ast.AST, pc: list[clingo.ast.AST] = parsed_choice) -> None:
                            pc.append(s)

                        parse_string(f"{{ __assume_{transformer.rule_idx - 1} }}.", on_choice)
                        for cstm in parsed_choice:
                            if cstm.ast_type == ASTType.Rule:
                                builder.add(cstm)
                    else:
                        builder.add(stm)

            ctl.ground([("base", [])])

            timer.start()

            models = []

            def on_model(m: clingo.Model) -> None:
                symbols = [str(sym) for sym in m.symbols(shown=True) if not sym.name.startswith("__assume_")]
                models.append(symbols)

            assumptions = [(clingo.Function(k), True) for k in rule_map]

            current_timestamp = time.time()

            with ctl.solve(yield_=True, assumptions=assumptions, on_model=on_model) as handle:
                for _ in handle:
                    pass
                result = handle.get()

                if result.satisfiable:
                    return FormalLogicProofReceipt(
                        satisfiability="SATISFIABLE",
                        event_cid=event_cid,
                        causal_provenance_id=provenance_id,
                        timestamp=current_timestamp,
                        answer_sets=models,
                    )
                if result.unsatisfiable:
                    core_symbols = handle.core()
                    # Fallback to map from integers to symbols if handle.core() returns literal integers
                    if len(core_symbols) > 0 and isinstance(core_symbols[0], int):
                        core_syms_mapped: list[clingo.Symbol] = []
                        for lit in core_symbols:
                            core_syms_mapped.extend(sa.symbol for sa in ctl.symbolic_atoms if sa.literal == lit)
                        core_symbols = core_syms_mapped

                    unsat_core_strings = [rule_map[sym.name] for sym in core_symbols if sym.name in rule_map]

                    return FormalLogicProofReceipt(
                        satisfiability="UNSATISFIABLE",
                        event_cid=event_cid,
                        causal_provenance_id=provenance_id,
                        timestamp=current_timestamp,
                        counter_model=CombinatorialCounterModel(
                            failed_premise_cid=provenance_id,
                            unsat_core=[s[:2000] for s in unsat_core_strings],
                        ),
                        answer_sets=[],
                    )

        except RuntimeError as e:
            return FormalLogicProofReceipt(
                satisfiability="UNKNOWN",
                event_cid=event_cid,
                causal_provenance_id=provenance_id,
                timestamp=time.time(),
                counter_model=CombinatorialCounterModel(
                    failed_premise_cid=provenance_id,
                    unsat_core=[str(e)[:2000]],
                ),
                answer_sets=[],
            )
        finally:
            timer.cancel()

        return FormalLogicProofReceipt(
            satisfiability="UNKNOWN",
            event_cid=event_cid,
            causal_provenance_id=provenance_id,
            timestamp=time.time(),
            answer_sets=[],
        )
