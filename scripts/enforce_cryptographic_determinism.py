#!/usr/bin/env python3
import ast
import inspect
import sys
import types
from typing import Annotated, Union, get_args, get_origin

from pydantic import BaseModel

# Import all models to ensure they are registered
from coreason_manifest.spec.ontology import *  # noqa: F403
from coreason_manifest.spec.ontology import CoreasonBaseState


def is_list_type(annotation):
    origin = get_origin(annotation)
    if origin is list or annotation is list:
        return True
    if (
        origin is Union
        or getattr(annotation, "__origin__", None) is Union
        or origin is types.UnionType
        or isinstance(annotation, types.UnionType)
    ):
        for arg in get_args(annotation):
            if is_list_type(arg):
                return True
    if origin is Annotated or getattr(annotation, "__origin__", None) is Annotated:
        return is_list_type(get_args(annotation)[0])
    return False


def get_all_subclasses(cls):
    all_subclasses = []
    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return all_subclasses


def check_ast_for_sort(cls, field_name):
    try:
        source = inspect.getsource(cls)
    except TypeError:
        return False

    # Unindent source if needed
    lines = source.split("\n")
    indent = len(lines[0]) - len(lines[0].lstrip())
    if indent > 0:
        lines = [line[indent:] if line.startswith(" " * indent) else line for line in lines]
    source = "\n".join(lines)

    try:
        tree = ast.parse(source)
    except Exception:
        return False

    for node in ast.walk(tree):
        # We look for a call to `sorted` that targets `field_name`.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sorted":
            # We assume if sorted is called and there is some reference to field_name or it is part of an assignment to field_name, it's valid.
            pass

        # To be rigorous: look for setattr(self, "field_name", sorted(...))
        # or self.field_name = sorted(...)
        # or dict assignment

        # We can just look for assignments where target involves field_name and value is a Call to sorted.
        if isinstance(node, ast.Assign):
            # Check targets
            targets_field = False
            for target in node.targets:
                if (isinstance(target, ast.Attribute) and target.attr == field_name) or (
                    isinstance(target, ast.Name) and target.id == field_name
                ):
                    targets_field = True

            if targets_field and (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "sorted"
            ):
                return True

        # Or look for expressions like object.__setattr__(self, "field_name", sorted(...))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "__setattr__" and len(call.args) >= 3:
                arg1 = call.args[1]
                if isinstance(arg1, ast.Constant) and arg1.value == field_name:
                    arg2 = call.args[2]
                    if isinstance(arg2, ast.Call) and isinstance(arg2.func, ast.Name) and arg2.func.id == "sorted":
                        return True
    return False


def main():
    subclasses = get_all_subclasses(CoreasonBaseState)
    failures = []

    for cls in set(subclasses):
        if not issubclass(cls, BaseModel):
            continue

        for field_name, field_info in cls.model_fields.items():
            if is_list_type(field_info.annotation):
                # Condition A
                schema_extra = field_info.json_schema_extra or {}
                if schema_extra.get("coreason_topological_exemption") is True:
                    continue

                # Condition B
                if check_ast_for_sort(cls, field_name):
                    continue

                # Failed
                failures.append((cls.__name__, field_name))

    if failures:
        for cls_name, field_name in failures:
            sys.stderr.write(
                f"Cryptographic Determinism Violation: class '{cls_name}' field '{field_name}' is a list but is neither sorted nor topologically exempted.\n"
            )
        sys.exit(1)

    print("Cryptographic determinism successfully verified.")
    sys.exit(0)


if __name__ == "__main__":
    main()
