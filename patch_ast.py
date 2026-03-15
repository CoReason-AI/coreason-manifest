import ast

with open("to_fix.txt") as f:
    pairs = [tuple(l.strip().split()) for l in f if l.strip()]
    pairs_set = set(pairs)


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
        self.generic_visit(node)

        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                fld_name = stmt.target.id

                if (cls_name, fld_name) in pairs_set:
                    if isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, "id", "") == "Field":
                        has_le = any(kw.arg == "le" for kw in stmt.value.keywords)
                        if not has_le:
                            is_int = False
                            type_str = ast.unparse(stmt.annotation)
                            if "int" in type_str and "float" not in type_str:
                                is_int = True

                            le_val = get_le_val(fld_name, is_int)
                            new_kw_le = ast.keyword(arg="le", value=ast.Constant(value=le_val))
                            stmt.value.keywords.insert(0, new_kw_le)

                            has_ge = any(kw.arg == "ge" for kw in stmt.value.keywords)
                            if fld_name == "spawning_threshold" and not has_ge:
                                new_kw_ge = ast.keyword(arg="ge", value=ast.Constant(value=1))
                                stmt.value.keywords.insert(0, new_kw_ge)

        return node


transformer = RewriteFields()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)

# Unparse the tree to get the new source
new_source = ast.unparse(new_tree)

# Inject comments lost by unparse
# Specifically `# noqa: E501` to lines longer than 120 chars
# Or just run `ruff format .` and `ruff check . --fix --unsafe-fixes` ? No, ruff will complain about line length without noqa.

new_lines = new_source.split("\n")
for i, line in enumerate(new_lines):
    if len(line) > 115 and "# noqa" not in line:
        new_lines[i] = line + "  # noqa: E501"

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write("\n".join(new_lines))
