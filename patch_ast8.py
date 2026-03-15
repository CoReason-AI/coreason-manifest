import ast


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


with open("src/coreason_manifest/spec/ontology.py") as f:
    source = f.read()

tree = ast.parse(source)


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

        # Or if it's any class in our file, let's just rewrite any AnnAssign matching the pattern
        # The prompt says: "For every violation ... add a mathematically sensible `le` bound to the `Field(...)` constraint."

        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)

        type_str = ast.unparse(node.annotation)

        # Check if the right side is a Field()
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
            # Check if type is int or float, OR Union with int/float
            # Actually, `test_universal_bounds` tests for `field_info.annotation in (int, float)` and unions
            if "int" in type_str or "float" in type_str:
                # Make sure it's not a generic container like list[int] or dict[..., int]
                # Well, `field_info.annotation in (int, float)` literally means the type is just int, float, or Union of int/float/None.
                # So `list` or `dict` in type_str means it's not a plain int/float field.
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
                        fld_name = getattr(node.target, "id", "")
                        if fld_name:
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
