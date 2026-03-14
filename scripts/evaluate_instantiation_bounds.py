# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import ast
import sys
from pathlib import Path


def is_forbidden_config(node: ast.expr) -> bool:
    """Check if model_config assignment attempts to set forbidden properties to False or variable."""
    forbidden_keys = {"frozen", "strict", "validate_assignment"}

    if isinstance(node, ast.Call) and (
        getattr(node.func, "id", None) == "ConfigDict" or getattr(node.func, "attr", None) == "ConfigDict"
    ):
        for kw in node.keywords:
            if kw.arg in forbidden_keys and not (isinstance(kw.value, ast.Constant) and kw.value.value is True):
                return True
    elif isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values, strict=False):
            if (
                isinstance(key, ast.Constant)
                and key.value in forbidden_keys
                and not (isinstance(value, ast.Constant) and value.value is True)
            ):
                return True
    return False


def get_decorators(node: ast.FunctionDef) -> set[str]:
    """Extract decorator names from a function definition."""
    decorators = set()
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.add(dec.id)
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
            decorators.add(dec.func.id)
        elif isinstance(dec, ast.Attribute):
            decorators.add(dec.attr)
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            decorators.add(dec.func.attr)
    return decorators


def check_file(filepath: Path, known_classes: dict[str, set[str]]) -> bool:
    """Parse file and check rules. Returns True if violations found."""
    with open(filepath, encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
        return True

    violations = False

    # White-listed methods
    allowed_methods = {
        "compile_to_base_topology",
        "generate_node_hash",
        "model_dump_canonical",
        "__hash__",
    }

    # First, collect classes and their base classes from this file
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = set()
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.add(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.add(base.attr)
                elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
                    bases.add(base.value.id)
            known_classes[node.name] = bases

    def is_coreason_model(class_name: str, visited: frozenset[str] = frozenset()) -> bool:
        if class_name == "CoreasonBaseState":
            return True
        if class_name in visited or class_name not in known_classes:
            return False

        new_visited = visited | frozenset([class_name])
        return any(is_coreason_model(base, new_visited) for base in known_classes[class_name])

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not is_coreason_model(node.name):
                continue

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Rule A: __init__ or __post_init__
                    if item.name in ("__init__", "__post_init__"):
                        print(
                            f"Rule A Violation: Class '{node.name}' "
                            f"defines forbidden method '{item.name}' in {filepath}",
                            file=sys.stderr,
                        )
                        violations = True

                    # Rule B: Missing validator decorator
                    if item.name not in allowed_methods:
                        decorators = get_decorators(item)
                        if "model_validator" not in decorators and "field_validator" not in decorators:
                            # We might have property or classmethod without validator?
                            # The rule says *any* FunctionDef missing the decorators.
                            print(
                                f"Rule B Violation: Class '{node.name}' "
                                f"function '{item.name}' missing validator decorator in {filepath}",
                                file=sys.stderr,
                            )
                            violations = True
                elif isinstance(item, ast.AnnAssign):
                    if (
                        isinstance(item.target, ast.Name)
                        and item.target.id == "model_config"
                        and item.value is not None
                        and is_forbidden_config(item.value)
                    ):
                        print(
                            f"Rule C Violation: Class '{node.name}' attempts to bypass immutability lock in {filepath}",
                            file=sys.stderr,
                        )
                        violations = True

                # Rule C: Immutability lock
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "model_config"
                            and is_forbidden_config(item.value)
                        ):
                            print(
                                f"Rule C Violation: Class '{node.name}' "
                                f"attempts to bypass immutability lock in {filepath}",
                                file=sys.stderr,
                            )
                            violations = True

    return violations


def main() -> None:
    target_dir = Path("src/coreason_manifest/spec")
    if not target_dir.is_dir():
        print(f"Error: Directory {target_dir} not found.", file=sys.stderr)
        sys.exit(1)

    py_files = list(target_dir.rglob("*.py"))
    known_classes: dict[str, set[str]] = {}

    # Pre-parse to map class inheritance globally
    for filepath in py_files:
        with open(filepath, encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(filepath))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = set()
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                bases.add(base.id)
                            elif isinstance(base, ast.Attribute):
                                bases.add(base.attr)
                            elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
                                bases.add(base.value.id)
                        known_classes[node.name] = bases
            except SyntaxError:
                pass

    has_violations = False
    for filepath in py_files:
        if check_file(filepath, known_classes):
            has_violations = True

    if has_violations:
        print("AST structural bounds check failed.", file=sys.stderr)
        sys.exit(1)

    print("AST structural bounds check passed.", file=sys.stdout)


if __name__ == "__main__":
    main()
