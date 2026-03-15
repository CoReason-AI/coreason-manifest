import ast

with open("src/coreason_manifest/spec/ontology.py") as f:
    source = f.read()

tree = ast.parse(source)


def get_le_val(fld_name, is_int):
    if fld_name == "spawning_threshold":
        return 100
    if fld_name == "context_window_token_ceiling":
        return 2000000
    if fld_name == "divergence_temperature_override":
        return 10.0
    if "magnitude" in fld_name:
        return 1000000000
    if "ms" in fld_name:
        return 86400000
    if "seconds" in fld_name:
        return 86400
    if "carbon" in fld_name:
        return 10000.0
    if any(
        k in fld_name
        for k in [
            "ratio",
            "score",
            "probability",
            "factor",
            "weight",
            "epsilon",
            "prior",
            "similarity",
            "delta",
            "rate",
            "tolerance",
            "penalty",
        ]
    ):
        return 1.0
    return 1000000000 if is_int else 1000000000.0


class RewriteFields(ast.NodeTransformer):
    def visit_ClassDef(self, node):
        cls_name = node.name

        # Check if inherits from CoreasonBaseState or BaseStateEvent
        inherits = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in [
                "CoreasonBaseState",
                "BaseStateEvent",
                "SystemFaultEvent",
                "BargeInInterruptEvent",
                "CounterfactualRegretEvent",
                "ToolInvocationEvent",
                "EpistemicPromotionEvent",
                "NormativeDriftEvent",
                "PersistenceCommitReceipt",
                "TokenBurnReceipt",
                "BudgetExhaustionEvent",
                "EpistemicTelemetryEvent",
                "CognitivePredictionReceipt",
                "EpistemicAxiomVerificationReceipt",
                "CognitiveRewardEvaluationReceipt",
                "EpistemicFlowStateReceipt",
                "ObservationEvent",
                "BeliefMutationEvent",
                "CausalExplanationEvent",
            ]:
                inherits = True
                break

        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)

        type_str = ast.unparse(node.annotation)

        # We need to rewrite naked fields first. Wait, we rewrote them earlier, but they were lost by `git restore`.
        # Let's fix the naked fields too.
        fld_name = getattr(node.target, "id", "")

        if fld_name == "source_chain_id" and "str" in type_str:
            if not isinstance(node.value, ast.Call):
                node.value = ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(arg="min_length", value=ast.Constant(value=1)),
                        ast.keyword(arg="max_length", value=ast.Constant(value=128)),
                        ast.keyword(arg="pattern", value=ast.Constant(value="^[a-zA-Z0-9_.:-]+$")),
                    ],
                )
        elif fld_name == "target_source_concept" and "str" in type_str:
            if not isinstance(node.value, ast.Call):
                node.value = ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[],
                    keywords=[ast.keyword(arg="max_length", value=ast.Constant(value=2000))],
                )
        elif fld_name == "source_prediction_id" and "str" in type_str:
            if not isinstance(node.value, ast.Call):
                node.value = ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(arg="min_length", value=ast.Constant(value=1)),
                        ast.keyword(arg="max_length", value=ast.Constant(value=128)),
                        ast.keyword(arg="pattern", value=ast.Constant(value="^[a-zA-Z0-9_.:-]+$")),
                    ],
                )
        elif fld_name == "lmsr_b_parameter" and "str" in type_str:
            if isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "Field":
                has_ml = any(kw.arg == "max_length" for kw in node.value.keywords if kw.arg)
                if not has_ml:
                    node.value.keywords.append(ast.keyword(arg="max_length", value=ast.Constant(value=255)))

        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
            if "int" in type_str or "float" in type_str:
                if (
                    "list" not in type_str
                    and "dict" not in type_str
                    and "Annotated" not in type_str
                    and "set" not in type_str
                ):
                    is_int = "int" in type_str and "float" not in type_str

                    has_le = any(kw.arg in ("le", "lt") for kw in node.value.keywords if kw.arg)
                    has_ge = any(kw.arg in ("ge", "gt") for kw in node.value.keywords if kw.arg)

                    if not has_le:
                        le_val = get_le_val(fld_name, is_int)

                        new_kw_le = ast.keyword(arg="le", value=ast.Constant(value=le_val))
                        node.value.keywords.insert(0, new_kw_le)

                        if fld_name == "spawning_threshold" and not has_ge:
                            new_kw_ge = ast.keyword(arg="ge", value=ast.Constant(value=1))
                            node.value.keywords.insert(0, new_kw_ge)

        return node


transformer = RewriteFields()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)

new_source = ast.unparse(new_tree)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(new_source)
