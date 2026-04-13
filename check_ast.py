import ast

with open('src/coreason_manifest/spec/ontology.py', 'r', encoding='utf-8') as f:
    code = f.read()

tree = ast.parse(code)

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and stmt.value and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Name) and call.func.id == 'Field':
                    has_default_none = False
                    for kw in call.keywords:
                        if kw.arg == 'default' and isinstance(kw.value, ast.Constant) and kw.value.value is None:
                            has_default_none = True
                            
                    if has_default_none:
                        # Check annotation for None or Optional
                        ann_str = ast.unparse(stmt.annotation)
                        if 'None' not in ann_str and 'Optional' not in ann_str and 'Any' not in ann_str:
                            print(f'Class {node.name}, field {stmt.target.id} has default=None but annotation is: {ann_str}')
                            
print("AST check complete.")
