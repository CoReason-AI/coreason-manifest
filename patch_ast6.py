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
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)

        # Check if annotation is int/float or Union containing them
        type_str = ast.unparse(node.annotation)

        # Only inject if we are assigning to a Field(...)
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
            # Use `int` or `float` keyword matching
            if "int" in type_str or "float" in type_str:
                is_int = "int" in type_str and "float" not in type_str

                # Double check to prevent injecting `le=` on fields that are actually string types with `int` in the name,
                # but type_str should just be the literal type annotation like `int`, `int | None`, `float`, etc.
                if (
                    "str" not in type_str
                    and "bool" not in type_str
                    and "list" not in type_str
                    and "dict" not in type_str
                ):
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

# Unparse the tree to get the new source
new_source = ast.unparse(new_tree)

# We can skip the '# noqa' part and rely on ruff to fix things?
# Ruff cannot fix 'line too long' without noqa if it can't wrap it.
# To be safe, we'll write the raw unparsed file, then use ruff.
with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(new_source)
