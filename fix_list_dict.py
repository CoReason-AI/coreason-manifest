import ast

with open("src/coreason_manifest/spec/ontology.py") as f:
    source = f.read()

tree = ast.parse(source)
bad_fields = []


class FieldVisitor(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                type_str = ast.unparse(stmt.annotation)
                if "list[" in type_str or "dict[" in type_str or "Any" in type_str:
                    if isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, "id", "") == "Field":
                        for kw in stmt.value.keywords:
                            if (
                                kw.arg == "le"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value in (1000000000, 1000000000.0)
                            ):
                                bad_fields.append(
                                    {
                                        "line": stmt.value.lineno,
                                        "col": stmt.value.col_offset,
                                    }
                                )
        self.generic_visit(node)


FieldVisitor().visit(tree)

with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

for patch in bad_fields:
    l_idx = patch["line"] - 1
    line = lines[l_idx]

    # We replace `le=1000000000, ` with nothing
    if "le=1000000000, " in line:
        lines[l_idx] = line.replace("le=1000000000, ", "")
    elif "le=1000000000.0, " in line:
        lines[l_idx] = line.replace("le=1000000000.0, ", "")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
