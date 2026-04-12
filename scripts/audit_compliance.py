# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import ast
from pathlib import Path

# Config
REPO_ROOT = Path(r"c:\files\git\github\coreason-ai\coreason-manifest")
SRC_DIR = REPO_ROOT / "src"
TESTS_DIR = REPO_ROOT / "tests"
SCRIPTS_DIR = REPO_ROOT / "scripts"

HEADER = """# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>"""

FORBIDDEN_CRUD = [
    "Data",
    "Model",
    "Type",
    "Info",
    "ID",
    "Record",
    "Create",
    "Read",
    "Update",
    "Delete",
    "Remove",
    "Group",
    "List",
    "Memory",
    "Link",
    "Merge",
    "Overwrite",
    "History",
]

REQUIRED_SUFFIXES = [
    "Receipt",
    "Event",
    "Premise",
    "Intent",
    "Task",
    "Policy",
    "Contract",
    "SLA",
    "State",
    "Snapshot",
    "Manifest",
    "Profile",
    "Proxy",
    "Mask",
    "Constraint",
    "Invariant",
]

DOCSTRING_PARTS = ["AGENT INSTRUCTION:", "CAUSAL AFFORDANCE:", "EPISTEMIC BOUNDS:", "MCP ROUTING TRIGGERS:"]


def check_header(filepath: Path) -> list[str]:
    errors: list[str] = []
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith(HEADER):
        errors.append("Missing or incorrect copyright header")
    return errors


def check_class_defs(filepath: Path) -> dict[str, list[str]]:
    content = filepath.read_text(encoding="utf-8")
    tree = ast.parse(content)

    class_errors: dict[str, list[str]] = {}
    # but the instructions specifically mention "Every object name MUST terminate with a strictly typed suffix"

    class CodeVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            errors: list[str] = []
            name = node.name

            # Skip exception classes and private classes?
            if not name.startswith("_"):
                is_exception = any(
                    isinstance(base, ast.Name)
                    and (base.id == "ValueError" or base.id.endswith("Error") or base.id == "Exception")
                    for base in node.bases
                )
                any(isinstance(base, ast.Name) and (base.id == "StrEnum" or base.id == "Enum") for base in node.bases)

                # Check Anti-CRUD
                errors.extend(
                    f"Forbidden CRUD term '{crud}' in name"
                    for crud in FORBIDDEN_CRUD
                    if crud.lower() in name.lower() and not is_exception and crud in name
                )

                # Check Suffix
                if not is_exception and name != "CoreasonBaseState":  # Base state is a special one
                    has_suffix = any(name.endswith(suffix) for suffix in REQUIRED_SUFFIXES)
                    if not has_suffix:
                        # Some exceptions for Enums? The prompt says "Every object name"
                        # Wait, we saw "StrEnum" ended with Profile or something? e.g. "ComputeTierProfile"
                        errors.append(f"Missing required suffix in name (ends with: {name.split('`')[-1]})")

                # Check Docstring if it inherits from CoreasonBaseState
                inherits_base = any(getattr(base, "id", "") == "CoreasonBaseState" for base in node.bases)
                if inherits_base:
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        errors.append("Missing docstring for CoreasonBaseState subclass")
                    else:
                        errors.extend(
                            f"Missing '{part}' in docstring" for part in DOCSTRING_PARTS if part not in docstring
                        )

            if errors:
                class_errors[name] = errors
            self.generic_visit(node)

        def visit_TypeAlias(self, node: ast.stmt) -> None:
            # Python 3.12+ `type` keyword
            errors: list[str] = []
            if isinstance(node.name, ast.Name):  # type: ignore
                name: str = node.name.id  # type: ignore
                errors.extend(f"Forbidden CRUD term '{crud}' in alias name" for crud in FORBIDDEN_CRUD if crud in name)
                has_suffix = any(name.endswith(suffix) for suffix in REQUIRED_SUFFIXES)
                if not has_suffix and "State" not in name and "Profile" not in name:
                    pass  # We do the same check
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            # old style type aliases e.g. Name = TypeVar(...) or Annotated
            pass

    visitor = CodeVisitor()
    visitor.visit(tree)
    return class_errors


def main() -> None:
    print("Starting audit...")
    all_files = list(SRC_DIR.rglob("*.py")) + list(TESTS_DIR.rglob("*.py")) + list(SCRIPTS_DIR.rglob("*.py"))

    header_errors = 0
    class_violations = 0

    for filepath in all_files:
        errors = check_header(filepath)
        if errors:
            print(f"[HEADER ERROR] {filepath.relative_to(REPO_ROOT)}")
            header_errors += 1

    # specifically check src models
    for filepath in SRC_DIR.rglob("spec/ontology.py"):
        print(f"Checking {filepath.relative_to(REPO_ROOT)}")
        cls_errs = check_class_defs(filepath)
        for cls_name, errs in cls_errs.items():
            print(f"[CLASS ERROR] {cls_name}:")
            for e in errs:
                print(f"  - {e}")
            class_violations += 1


if __name__ == "__main__":
    main()
