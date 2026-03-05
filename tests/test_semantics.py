# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import ast
from pathlib import Path


def get_all_python_files() -> list[Path]:
    """Retrieve all Python files in the src/coreason_manifest directory."""
    src_dir = Path("src/coreason_manifest")
    return list(src_dir.rglob("*.py"))


def test_no_future_imports() -> None:
    """Assertion 1: Prove there are ZERO imports of __future__."""
    for py_file in get_all_python_files():
        with py_file.open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "__future__", f"Found __future__ import in {py_file}"


def test_no_legacy_typing_imports() -> None:
    """
    Assertion 2: Prove there are ZERO imports of uppercase typing collections
    (List, Dict, Tuple, Set, Union, TypeAlias, TypeVar) from the typing module.
    """
    forbidden_typing = {"List", "Dict", "Tuple", "Set", "Union", "TypeAlias", "TypeVar"}
    for py_file in get_all_python_files():
        with py_file.open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                for alias in node.names:
                    assert alias.name not in forbidden_typing, (
                        f"Found forbidden typing import '{alias.name}' in {py_file}"
                    )


def test_pydantic_field_descriptions() -> None:
    """
    Assertion 3: Parse all Pydantic model class definitions and prove that
    every single class attribute explicitly uses Field(...) and contains a description kwarg.
    """
    for py_file in get_all_python_files():
        with py_file.open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # We skip classes that don't inherit from anything, or don't seem like Pydantic models.
                # However, all models in this codebase should inherit from CoreasonBaseModel
                # or similar. We'll check all class attributes that have type annotations.
                for body_item in node.body:
                    if isinstance(body_item, ast.AnnAssign):
                        # It's a typed class attribute
                        # We need to ensure the value is a call to Field
                        target_id = getattr(body_item.target, "id", "unknown")
                        assert body_item.value is not None, (
                            f"Class attribute '{target_id}' in '{node.name}' ({py_file}) "
                            f"must be explicitly assigned a Field(...)."
                        )
                        assert isinstance(body_item.value, ast.Call), (
                            f"Class attribute '{target_id}' in '{node.name}' ({py_file}) must be a call to Field(...)."
                        )
                        func = body_item.value.func
                        if isinstance(func, ast.Name):
                            func_name = func.id
                        elif isinstance(func, ast.Attribute):
                            func_name = func.attr
                        else:
                            func_name = ""

                        assert func_name == "Field", (
                            f"Class attribute '{target_id}' in '{node.name}' ({py_file}) "
                            f"must be initialized with Field(...)."
                        )

                        # Check that 'description' is in keywords
                        has_description = any(kw.arg == "description" for kw in body_item.value.keywords)
                        assert has_description, (
                            f"Class attribute '{target_id}' in '{node.name}' ({py_file}) "
                            f"must have a 'description' kwarg in Field(...)."
                        )

def test_models_inherit_coreason_base() -> None:
    """
    Assertion 4: Prove all schema inherit from CoreasonBaseModel,
    preventing direct inheritance from Pydantic BaseModel.
    """
    for py_file in get_all_python_files():
        with py_file.open("r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "CoreasonBaseModel":
                    continue
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        assert base.id != "BaseModel", (
                            f"Class '{node.name}' in {py_file} inherits directly from BaseModel "
                            f"instead of CoreasonBaseModel."
                        )
                    elif isinstance(base, ast.Attribute):
                        assert base.attr != "BaseModel", (
                            f"Class '{node.name}' in {py_file} inherits directly from BaseModel "
                            f"instead of CoreasonBaseModel."
                        )
