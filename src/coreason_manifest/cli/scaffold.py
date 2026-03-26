import libcst as cst
import typer


class ClassInjectTransformer(cst.CSTTransformer):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.inserted = False

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:  # noqa: N802, ARG002
        if self.inserted:
            return updated_node

        # Build class:
        # class MyClass(CoreasonBaseState):
        #     """Description"""
        class_def = cst.ClassDef(
            name=cst.Name(self.name),
            bases=[cst.Arg(value=cst.Name("CoreasonBaseState"))],
            body=cst.IndentedBlock(
                body=[
                    cst.SimpleStatementLine(body=[cst.Expr(value=cst.SimpleString(value=f'"""{self.description}"""'))])
                ]
            ),
        )

        new_body = list(updated_node.body)

        # find where to insert
        insert_idx = len(new_body)
        for i, node in enumerate(new_body):
            if isinstance(node, cst.SimpleStatementLine):
                for stmt in node.body:
                    if (
                        isinstance(stmt, cst.Expr)
                        and isinstance(stmt.value, cst.Call)
                        and isinstance(stmt.value.func, cst.Attribute)
                        and stmt.value.func.attr.value == "model_rebuild"
                    ):
                        insert_idx = i
                        break
                if insert_idx == i:
                    break

        # insert class
        new_body.insert(insert_idx, class_def)

        # append MyClass.model_rebuild() at the end
        rebuild_call = cst.SimpleStatementLine(
            body=[
                cst.Expr(value=cst.Call(func=cst.Attribute(value=cst.Name(self.name), attr=cst.Name("model_rebuild"))))
            ]
        )
        new_body.append(rebuild_call)

        self.inserted = True
        return updated_node.with_changes(body=new_body)


app = typer.Typer()


@app.command()
def mcp(name: str, description: str) -> None:
    from pathlib import Path

    from .test_bootstrapper import generate_test

    ontology_path = Path("src/coreason_manifest/spec/ontology.py")
    if not ontology_path.exists():
        typer.echo(f"Could not find {ontology_path}", err=True)
        raise typer.Exit(1)

    code = ontology_path.read_text(encoding="utf-8")
    module = cst.parse_module(code)

    transformer = ClassInjectTransformer(name, description)
    modified_module = module.visit(transformer)

    ontology_path.write_text(modified_module.code, encoding="utf-8")
    typer.echo(f"Successfully scaffolded {name} in ontology.py")

    generate_test(name)
