import clingo
from clingo.ast import Transformer, parse_string, ProgramBuilder, Literal, SymbolicAtom, Function, Sign, ASTType

prog = """
pigeon(1..3).
hole(1..2).
1 { assign(P, H) : hole(H) } 1 :- pigeon(P).
:- assign(P1, H), assign(P2, H), P1 != P2.
"""

parsed_rules = []
parse_string(prog, lambda stm: parsed_rules.append(stm))

rule_map = {}

class AssumptionTransformer(Transformer):
    def __init__(self):
        self.rule_idx = 0

    def visit_Rule(self, rule):
        idx = self.rule_idx
        self.rule_idx += 1

        assumption_name = f"__assume_{idx}"
        rule_map[assumption_name] = str(rule)

        loc = rule.location
        fun = Function(loc, assumption_name, [], 0)
        sym_atom = SymbolicAtom(fun)
        lit = Literal(loc, Sign.NoSign, sym_atom)

        new_body = list(rule.body) + [lit]
        return rule.update(body=new_body)

transformer = AssumptionTransformer()

ctl = clingo.Control(["0"])
with ProgramBuilder(ctl) as builder:
    for stm in parsed_rules:
        if stm.ast_type == ASTType.Rule:
            new_stm = transformer(stm)
            builder.add(new_stm)

            parsed_choice = []
            parse_string(f"{{ __assume_{transformer.rule_idx - 1} }}.", lambda s: parsed_choice.append(s))
            for cstm in parsed_choice:
                if cstm.ast_type == ASTType.Rule:
                    builder.add(cstm)
        else:
            builder.add(stm)

ctl.ground([("base", [])])
assumptions = [(clingo.Function(k), True) for k in rule_map.keys()]

with ctl.solve(yield_=True, assumptions=assumptions) as handle:
    print(handle.get())
    core_symbols = handle.core()

    if len(core_symbols) > 0 and isinstance(core_symbols[0], int):
        core_syms_mapped = []
        for lit in core_symbols:
            for sa in ctl.symbolic_atoms:
                if sa.literal == lit:
                    core_syms_mapped.append(sa.symbol)
        core_symbols = core_syms_mapped

    core = [rule_map[sym.name] for sym in core_symbols if sym.name in rule_map]
    print("CORE:", core)
