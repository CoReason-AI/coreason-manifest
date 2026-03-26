import re
from pathlib import Path

import libcst as cst


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def generate_test(name: str) -> None:
    snake_case_name = camel_to_snake(name)
    test_file_path = Path(f"tests/fuzzing/test_mcp_{snake_case_name}.py")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)

    module = cst.Module(
        body=[
            cst.SimpleStatementLine(
                body=[
                    cst.Import(
                        names=[cst.ImportAlias(name=cst.Name("json"))]
                    )
                ]
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("pathlib"),
                        names=[cst.ImportAlias(name=cst.Name("Path"))]
                    )
                ]
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.Import(
                        names=[cst.ImportAlias(name=cst.Name("pytest"))]
                    )
                ]
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("hypothesis"),
                        names=[cst.ImportAlias(name=cst.Name("given"))]
                    )
                ]
            ),
            cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Name("hypothesis_jsonschema"),
                        names=[cst.ImportAlias(name=cst.Name("from_schema"))]
                    )
                ]
            ),
            cst.EmptyLine(),
            cst.EmptyLine(),
            cst.FunctionDef(
                name=cst.Name("get_target_schema"),
                params=cst.Parameters(),
                returns=cst.Annotation(annotation=cst.Name("dict")),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.ImportFrom(
                                    module=cst.Attribute(
                                        value=cst.Attribute(
                                            value=cst.Name("coreason_manifest"),
                                            attr=cst.Name("spec")
                                        ),
                                        attr=cst.Name("ontology")
                                    ),
                                    names=[cst.ImportAlias(name=cst.Name(name))]
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Return(
                                    value=cst.Call(
                                        func=cst.Attribute(
                                            value=cst.Name(name),
                                            attr=cst.Name("model_json_schema")
                                        )
                                    )
                                )
                            ]
                        )
                    ]
                )
            ),
            cst.EmptyLine(),
            cst.EmptyLine(),
            cst.FunctionDef(
                decorators=[
                    cst.Decorator(
                        decorator=cst.Call(
                            func=cst.Name("given"),
                            args=[
                                cst.Arg(
                                    value=cst.Call(
                                        func=cst.Name("from_schema"),
                                        args=[
                                            cst.Arg(
                                                value=cst.Call(
                                                    func=cst.Name("get_target_schema")
                                                )
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                    )
                ],
                name=cst.Name(f"test_mcp_{snake_case_name}_fuzzing"),
                params=cst.Parameters(
                    params=[
                        cst.Param(
                            name=cst.Name("instance")
                        )
                    ]
                ),
                body=cst.IndentedBlock(
                    body=[
                        cst.SimpleStatementLine(
                            body=[
                                cst.ImportFrom(
                                    module=cst.Attribute(
                                        value=cst.Attribute(
                                            value=cst.Name("coreason_manifest"),
                                            attr=cst.Name("spec")
                                        ),
                                        attr=cst.Name("ontology")
                                    ),
                                    names=[cst.ImportAlias(name=cst.Name(name))]
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assign(
                                    targets=[cst.AssignTarget(target=cst.Name("obj"))],
                                    value=cst.Call(
                                        func=cst.Attribute(
                                            value=cst.Name(name),
                                            attr=cst.Name("model_validate")
                                        ),
                                        args=[
                                            cst.Arg(
                                                value=cst.Name("instance")
                                            )
                                        ]
                                    )
                                )
                            ]
                        ),
                        cst.SimpleStatementLine(
                            body=[
                                cst.Assert(
                                    test=cst.Comparison(
                                        left=cst.Name("obj"),
                                        comparisons=[
                                            cst.ComparisonTarget(
                                                operator=cst.IsNot(),
                                                comparator=cst.Name("None")
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                    ]
                )
            )
        ]
    )

    test_file_path.write_text(module.code, encoding="utf-8")
    print(f"Successfully bootstrapped test file at {test_file_path}")
