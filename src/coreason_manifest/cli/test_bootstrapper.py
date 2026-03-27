import re
from pathlib import Path
from typing import Any

import libcst as cst


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def generate_test(name: str, fields: list[dict[str, Any]] | None = None) -> None:
    fields = fields or []
    snake_case_name = camel_to_snake(name)
    test_file_path = Path(f"tests/fuzzing/test_mcp_{snake_case_name}.py")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)

    module = cst.Module(
        body=[
            cst.SimpleStatementLine(body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("json"))])]),
            cst.SimpleStatementLine(
                body=[cst.ImportFrom(module=cst.Name("pathlib"), names=[cst.ImportAlias(name=cst.Name("Path"))])]
            ),
            cst.SimpleStatementLine(body=[cst.Import(names=[cst.ImportAlias(name=cst.Name("pytest"))])]),
            cst.SimpleStatementLine(
                body=[cst.ImportFrom(module=cst.Name("hypothesis"), names=[cst.ImportAlias(name=cst.Name("given"))])]
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("hypothesis_jsonschema"), names=[cst.ImportAlias(name=cst.Name("from_schema"))]
                    )
                ]
            ),
            cst.SimpleStatementLine(
                body=[cst.ImportFrom(module=cst.Name("typing"), names=[cst.ImportAlias(name=cst.Name("Any"))])]
            ),
            cst.FunctionDef(
                name=cst.Name("get_target_schema"),
                params=cst.Parameters(),
                returns=cst.Annotation(annotation=cst.parse_expression("dict[str, Any]")),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.ImportFrom(
                                    module=cst.Attribute(
                                        value=cst.Attribute(value=cst.Name("coreason_manifest"), attr=cst.Name("spec")),
                                        attr=cst.Name("ontology"),
                                    ),
                                    names=[cst.ImportAlias(name=cst.Name(name))],
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Return(
                                    value=cst.Call(
                                        func=cst.Attribute(value=cst.Name(name), attr=cst.Name("model_json_schema"))
                                    )
                                )
                            ]
                        ),
                    ]
                ),
            ),
            cst.FunctionDef(
                decorators=[
                    cst.Decorator(
                        decorator=cst.Call(
                            func=cst.Name("given"),
                            args=[
                                cst.Arg(
                                    value=cst.Call(
                                        func=cst.Name("from_schema"),
                                        args=[cst.Arg(value=cst.Call(func=cst.Name("get_target_schema")))],
                                    )
                                )
                            ],
                        )
                    )
                ],
                name=cst.Name(f"test_mcp_{snake_case_name}_fuzzing"),
                params=cst.Parameters(
                    params=[
                        cst.Param(
                            name=cst.Name("instance"),
                            annotation=cst.Annotation(annotation=cst.parse_expression("dict[str, Any]")),
                        )
                    ]
                ),
                returns=cst.Annotation(annotation=cst.Name("None")),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.ImportFrom(
                                    module=cst.Attribute(
                                        value=cst.Attribute(value=cst.Name("coreason_manifest"), attr=cst.Name("spec")),
                                        attr=cst.Name("ontology"),
                                    ),
                                    names=[cst.ImportAlias(name=cst.Name(name))],
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assign(
                                    targets=[cst.AssignTarget(target=cst.Name("obj"))],
                                    value=cst.Call(
                                        func=cst.Attribute(value=cst.Name(name), attr=cst.Name("model_validate")),
                                        args=[cst.Arg(value=cst.Name("instance"))],
                                    ),
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assert(
                                    test=cst.Comparison(
                                        left=cst.Name("obj"),
                                        comparisons=[
                                            cst.ComparisonTarget(operator=cst.IsNot(), comparator=cst.Name("None"))
                                        ],
                                    )
                                )
                            ]
                        ),
                    ]
                ),
            ),
        ]
    )

    # Inject property boundary assertions
    test_func = module.body[-1]
    if not isinstance(test_func, cst.FunctionDef) or not isinstance(test_func.body, cst.IndentedBlock):
        raise TypeError("Expected test_func to be a FunctionDef with an IndentedBlock body")  # pragma: no cover

    body_items = list(test_func.body.body)

    for field in fields:
        field_name = field["name"]
        checks = []
        if "minimum" in field:
            val = str(field["minimum"])
            checks.append(f"obj.{field_name} is None or obj.{field_name} >= {val}")
        if "maximum" in field:
            val = str(field["maximum"])
            checks.append(f"obj.{field_name} is None or obj.{field_name} <= {val}")
        if "exclusiveMinimum" in field:
            val = str(field["exclusiveMinimum"])
            checks.append(f"obj.{field_name} is None or obj.{field_name} > {val}")
        if "exclusiveMaximum" in field:
            val = str(field["exclusiveMaximum"])
            checks.append(f"obj.{field_name} is None or obj.{field_name} < {val}")

        for check in checks:
            stmt = cst.parse_statement(f"assert {check}")
            body_items.append(stmt)

    updated_func = test_func.with_deep_changes(test_func.body, body=body_items)
    new_module_body = list(module.body)
    new_module_body[-1] = updated_func
    updated_module = module.with_changes(body=new_module_body)

    test_file_path.write_text(updated_module.code, encoding="utf-8")
    print(f"Successfully bootstrapped test file at {test_file_path}")
