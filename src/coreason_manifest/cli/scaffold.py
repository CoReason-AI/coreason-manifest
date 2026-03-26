import json

import libcst as cst
import typer


class ClassInjectTransformer(cst.CSTTransformer):
    def __init__(self, name: str, description: str, fields: list[dict] | None = None):
        self.name = name
        self.description = description
        self.fields = fields or []
        self.inserted = False

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:  # noqa: N802, ARG002
        if self.inserted:
            return updated_node

        # Build class:
        # class MyClass(CoreasonBaseState):
        #     """Description"""
        body_items = [
            cst.SimpleStatementLine(body=[cst.Expr(value=cst.SimpleString(value=f'"""{self.description}"""'))])
        ]

        for field in self.fields:
            field_name = field["name"]
            field_type = field.get("type", "Any")
            field_desc = field.get("description", "")

            annotation = cst.Annotation(annotation=cst.Name(field_type))

            # Use Field(...) for description if present
            field_call_args = []
            if field_desc:
                field_call_args.append(
                    cst.Arg(
                        keyword=cst.Name("description"),
                        equal=cst.AssignEqual(),
                        value=cst.SimpleString(value=f'"{field_desc}"')
                    )
                )

            if field_call_args:
                value = cst.Call(
                    func=cst.Name("Field"),
                    args=field_call_args
                )
                body_items.append(
                    cst.SimpleStatementLine(
                        body=[
                            cst.AnnAssign(
                                target=cst.Name(field_name),
                                annotation=annotation,
                                value=value
                            )
                        ]
                    )
                )
            else:
                body_items.append(
                    cst.SimpleStatementLine(
                        body=[
                            cst.AnnAssign(
                                target=cst.Name(field_name),
                                annotation=annotation
                            )
                        ]
                    )
                )

        class_def = cst.ClassDef(
            name=cst.Name(self.name),
            bases=[cst.Arg(value=cst.Name("CoreasonBaseState"))],
            body=cst.IndentedBlock(
                body=body_items
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

    schema_path = Path("coreason_ontology.schema.json")
    fields = []
    if schema_path.exists():
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
            defs = schema.get("$defs", {})
            if name in defs:
                props = defs[name].get("properties", {})
                for prop_name, prop_details in props.items():
                    ptype = prop_details.get("type", "Any")
                    pdesc = prop_details.get("description", "")

                    if ptype == "string":
                        ptype = "str"
                    elif ptype == "integer":
                        ptype = "int"
                    elif ptype == "number":
                        ptype = "float"
                    elif ptype == "boolean":
                        ptype = "bool"

                    fields.append({
                        "name": prop_name,
                        "type": ptype,
                        "description": pdesc
                    })

    code = ontology_path.read_text(encoding="utf-8")
    module = cst.parse_module(code)

    transformer = ClassInjectTransformer(name, description, fields)
    modified_module = module.visit(transformer)

    ontology_path.write_text(modified_module.code, encoding="utf-8")
    typer.echo(f"Successfully scaffolded {name} in ontology.py")
    typer.echo("NOTICE: The generated schema extensions are governed by the Prosperity Public License 3.0.0. For commercial use, contact gowtham.rao@coreason.ai.")

    generate_test(name)
