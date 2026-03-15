import ast

with open("to_fix.txt") as f:
    pairs = [tuple(l.strip().split()) for l in f if l.strip()]
    pairs_set = set(pairs)


def get_le_val(fld_name, is_int):
    if fld_name == "spawning_threshold":
        return "100"
    if fld_name == "context_window_token_ceiling":
        return "2000000"
    if fld_name == "divergence_temperature_override":
        return "10.0"
    if "magnitude" in fld_name:
        return "1000000000"
    if "ms" in fld_name:
        return "86400000"
    if "seconds" in fld_name:
        return "86400"
    if "carbon" in fld_name:
        return "10000.0"
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
        return "1.0"
    return "1000000000" if is_int else "1000000000.0"


with open("src/coreason_manifest/spec/ontology.py") as f:
    source = f.read()

tree = ast.parse(source)
fields_to_patch = []


class FieldVisitor(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                fld_name = stmt.target.id
                cls_name = node.name

                if (cls_name, fld_name) in pairs_set:
                    if isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, "id", "") == "Field":
                        has_le = any(kw.arg == "le" for kw in stmt.value.keywords)
                        if not has_le:
                            is_int = False
                            if "int" in ast.unparse(stmt.annotation) and "float" not in ast.unparse(stmt.annotation):
                                is_int = True

                            fields_to_patch.append(
                                {"line": stmt.value.lineno, "fld": fld_name, "is_int": is_int, "node": stmt.value}
                            )
        self.generic_visit(node)


FieldVisitor().visit(tree)

with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

fields_to_patch.sort(key=lambda x: x["line"], reverse=True)

for patch in fields_to_patch:
    l_idx = patch["line"] - 1

    le_val = get_le_val(patch["fld"], patch["is_int"])

    node = patch["node"]
    start_line = node.lineno - 1
    end_line = node.end_lineno - 1
    start_col = node.col_offset
    end_col = node.end_col_offset

    # Do not add duplicate arguments
    has_ge = any(kw.arg == "ge" for kw in node.keywords)
    has_le = any(kw.arg == "le" for kw in node.keywords)

    if not has_le:
        new_kw_le = ast.keyword(arg="le", value=ast.Constant(value=eval(le_val)))
        node.keywords.insert(0, new_kw_le)

    if patch["fld"] == "spawning_threshold" and not has_ge:
        new_kw_ge = ast.keyword(arg="ge", value=ast.Constant(value=1))
        node.keywords.insert(0, new_kw_ge)

    new_field_str = ast.unparse(node)

    if start_line == end_line:
        lines[start_line] = lines[start_line][:start_col] + new_field_str + lines[start_line][end_col:]
    else:
        # Instead of completely wiping out lines and breaking comments like "# noqa: E501"
        # we will extract everything that was before `Field(...)` on the first line
        # and everything that is after `Field(...)` on the last line.
        prefix = lines[start_line][:start_col]
        suffix = lines[end_line][end_col:]

        # Now we construct a block of text
        new_text = prefix + new_field_str + suffix
        if not new_text.endswith("\n"):
            new_text += "\n"

        lines[start_line] = new_text
        for r in range(start_line + 1, end_line + 1):
            lines[r] = ""

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
