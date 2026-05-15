#!/usr/bin/env python3
# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Cross-language binding generator for the CoReason Shared Kernel Ontology.

Reads `coreason_ontology.schema.json` and produces idiomatic TypeScript interfaces
and Rust serde structs using dedicated per-language toolchains:

- TypeScript: `json-schema-to-typescript` (via npx)
- Rust: `cargo-typify` (via cargo)

The CI drift guillotine (`git diff --exit-code bindings/`) enforces that committed
bindings always match the current schema.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import typing
from pathlib import Path


def _strip_union_constraints(obj: typing.Any) -> None:
    if isinstance(obj, dict):
        if "anyOf" in obj:
            has_null = any(opt.get("type") == "null" for opt in obj["anyOf"])
            if has_null:
                for opt in obj["anyOf"]:
                    if opt.get("type") == "string":
                        opt.pop("minLength", None)
                        opt.pop("maxLength", None)
                        opt.pop("pattern", None)
                obj.pop("minLength", None)
                obj.pop("maxLength", None)
                obj.pop("pattern", None)
        if isinstance(obj.get("type"), list) and "null" in obj["type"] and "string" in obj["type"]:
            obj.pop("minLength", None)
            obj.pop("maxLength", None)
            obj.pop("pattern", None)
        # Typify does not support propertyNames constraint, which breaks JsonPrimitiveState compilation
        obj.pop("propertyNames", None)
        # Typify validation strictly rejects Draft 2020-12 style defaults/examples mixed with $refs
        obj.pop("default", None)
        obj.pop("examples", None)
        for v in obj.values():
            _strip_union_constraints(v)
    elif isinstance(obj, list):
        for v in obj:
            _strip_union_constraints(v)


def _build_rooted_schema(schema_path: str, output_path: str) -> None:
    """Build a wrapper schema with a root `type: object` so codegen tools can anchor on it.

    The raw exported schema is `$defs`-only (no root type), which causes most codegen
    tools to emit trivial stubs. This wrapper exposes every `$def` as a property of a
    synthetic root object.
    It additionally strips schema constraints that violate `cargo-typify` union limits.
    """
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    _strip_union_constraints(schema)
    defs = schema.get("$defs", {})

    # Extract the schema version from the original file, or default to 2020-12
    # since we are using $defs instead of definitions.
    schema_dialect = schema.get("$schema", "https://json-schema.org/draft/2020-12/schema")

    wrapper = {
        "$schema": schema_dialect,
        "title": schema.get("title", "Ontology"),
        "description": schema.get("description", ""),
        "type": "object",
        "properties": {name: {"$ref": f"#/$defs/{name}"} for name in defs},
        "$defs": defs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(wrapper, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _generate_typescript(schema_path: str, ts_out: str, node_env: dict[str, str]) -> None:
    """Generate TypeScript interfaces using json-schema-to-typescript (handles large schemas)."""
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"

    print("Generating TypeScript bindings via json-schema-to-typescript...")
    ts_cmd = [npx_cmd, "-y", "json-schema-to-typescript", schema_path, "-o", ts_out]
    subprocess.run(ts_cmd, check=True, env=node_env)  # noqa: S603 # nosec B603

    # Prepend license header
    with open(ts_out, encoding="utf-8") as f:
        content = f.read()

    header = (
        "// Copyright (c) 2026 CoReason, Inc\n"
        "// Licensed under the Prosperity Public License 3.0\n"
        "// https://github.com/CoReason-AI/coreason-manifest\n"
        "//\n"
        "// AUTO-GENERATED — DO NOT EDIT. Regenerate via:\n"
        "//   uv run python scripts/generate_cross_language_bindings.py\n\n"
    )

    with open(ts_out, "w", encoding="utf-8") as f:
        f.write(header + content)

    line_count = content.count("\n")
    print(f"  -> {ts_out}: {line_count:,} lines")


def _generate_rust(schema_path: str, rust_out: str) -> None:
    """Generate Rust serde structs using cargo-typify (handles complex JSON Schema natively)."""
    if not shutil.which("cargo"):
        print("Warning: cargo not found in PATH. Skipping Rust bindings generation.")
        return

    # Check if cargo-typify is installed; install if missing
    result = subprocess.run(  # nosec B603 B607
        ["cargo", "typify", "--help"],  # noqa: S607
        capture_output=True,
    )
    if result.returncode != 0:
        print("  Installing cargo-typify...")
        install_result = subprocess.run(  # nosec B603 B607
            ["cargo", "install", "cargo-typify"],  # noqa: S607
            capture_output=True,
        )
        if install_result.returncode != 0:
            print("Warning: Failed to install cargo-typify (missing MSVC linker?). Skipping Rust bindings.")
            print("  Rust bindings will be generated in CI where build tools are available.")
            return

    print("Generating Rust bindings via cargo-typify...")
    typify_cmd = ["cargo", "typify", schema_path, "-o", rust_out]
    subprocess.run(typify_cmd, check=True)  # noqa: S603 # nosec B603

    # Prepend allow directives and license header
    with open(rust_out, encoding="utf-8") as f:
        rust_code = f.read()

    header = (
        "// Copyright (c) 2026 CoReason, Inc\n"
        "// Licensed under the Prosperity Public License 3.0\n"
        "// https://github.com/CoReason-AI/coreason-manifest\n"
        "//\n"
        "// AUTO-GENERATED — DO NOT EDIT. Regenerate via:\n"
        "//   uv run python scripts/generate_cross_language_bindings.py\n\n"
        "#![allow(non_snake_case)]\n"
        "#![allow(non_camel_case_types)]\n\n"
    )

    with open(rust_out, "w", encoding="utf-8") as f:
        f.write(header + rust_code)

    # Format with cargo fmt if available
    print("Formatting Rust bindings...")
    subprocess.run(  # nosec B603 B607
        ["cargo", "fmt", "--manifest-path", "bindings/rust/Cargo.toml"],  # noqa: S607
        check=True,
    )

    line_count = rust_code.count("\n")
    print(f"  -> {rust_out}: {line_count:,} lines")


def _sync_versions(project_root: Path) -> str:
    """Read the version from pyproject.toml and synchronize bindings.

    Handles both static versions and dynamic versions (vcs-based).
    """
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    version = data.get("project", {}).get("version")

    if not version:
        # If version is missing, check if it's dynamic
        dynamic = data.get("project", {}).get("dynamic", [])
        if "version" in dynamic:
            print("Detected dynamic versioning. Attempting to retrieve version via 'hatch version'...")
            try:
                # Try hatch first
                result = subprocess.run(  # nosec B603 B607 # noqa: S607
                    ["hatch", "version"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                version = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("  'hatch' not found or failed. Falling back to 'git describe'...")
                try:
                    result = subprocess.run(  # nosec B603 B607 # noqa: S607
                        ["git", "describe", "--tags", "--always"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    version = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("  'git' failed. Defaulting to '0.0.0-dev' (quarantine mode).")
                    version = "0.0.0-dev"
        else:
            raise KeyError("Project version not found and not marked as dynamic.")

    # Normalize version for Rust (strip leading 'v', ensure SemVer-ish)
    version = version.removeprefix("v")

    print(f"Synchronizing ecosystem to version: {version}")

    # TypeScript package.json
    ts_pkg_path = project_root / "bindings/typescript/package.json"
    if ts_pkg_path.exists():
        with open(ts_pkg_path, encoding="utf-8") as f:
            ts_pkg = json.load(f)
        ts_pkg["version"] = version
        with open(ts_pkg_path, "w", encoding="utf-8") as f:
            json.dump(ts_pkg, f, indent=2)
            f.write("\n")
        print(f"  -> {ts_pkg_path.relative_to(project_root)} updated.")

    # Rust Cargo.toml
    rust_cargo_path = project_root / "bindings/rust/Cargo.toml"
    if rust_cargo_path.exists():
        content = rust_cargo_path.read_text(encoding="utf-8")
        new_content = re.sub(r'^version = ".*?"', f'version = "{version}"', content, flags=re.MULTILINE)
        rust_cargo_path.write_text(new_content, encoding="utf-8")
        print(f"  -> {rust_cargo_path.relative_to(project_root)} updated.")

    return str(version)


def _update_lockfiles(project_root: Path) -> None:
    """Update uv and cargo lockfiles to ensure environment consistency."""
    print("Updating lockfiles...")

    # UV Lock
    uv_bin = shutil.which("uv") or "uv"
    subprocess.run([uv_bin, "lock", "--upgrade-package", "coreason-manifest"], cwd=project_root, check=True)  # nosec B603 # noqa: S603
    print("  -> uv.lock updated.")

    # Cargo Lock
    rust_dir = project_root / "bindings/rust"
    if rust_dir.exists() and (rust_dir / "Cargo.toml").exists():
        cargo_bin = shutil.which("cargo") or "cargo"
        subprocess.run([cargo_bin, "update"], cwd=rust_dir, check=True)  # nosec B603 # noqa: S603
        print("  -> Cargo.lock updated.")


def main() -> None:
    # Ensure we are working from the project root
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    _sync_versions(project_root)
    _update_lockfiles(project_root)

    schema_file = "coreason_ontology.schema.json"
    ts_out = "bindings/typescript/src/ontology.ts"
    rust_out = "bindings/rust/src/ontology.rs"

    print("Projecting fresh ontology manifold...")
    from universal_ontology_compiler import project_ontology_manifold

    project_ontology_manifold()

    if not os.path.exists(schema_file):
        print(f"Error: Schema file {schema_file} failed to generate.")
        sys.exit(1)

    # Build the rooted wrapper schema (the raw schema is $defs-only)
    wrapper_path = os.path.join(tempfile.gettempdir(), "coreason_ontology_rooted.schema.json")
    print("Building rooted wrapper schema...")
    _build_rooted_schema(schema_file, wrapper_path)

    # Configure npm/npx environment to suppress all warnings and prompts
    node_env = os.environ.copy()
    node_env["npm_config_loglevel"] = "error"
    node_env["npm_config_fund"] = "false"
    node_env["npm_config_audit"] = "false"
    node_env["npm_config_update_notifier"] = "false"
    node_env["npm_config_yes"] = "true"
    node_options = node_env.get("NODE_OPTIONS", "")
    node_env["NODE_OPTIONS"] = f"{node_options} --no-deprecation".strip()

    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"

    # TypeScript generation
    if shutil.which(npx_cmd):
        _generate_typescript(wrapper_path, ts_out, node_env)
    else:
        print(f"Warning: {npx_cmd} not found in PATH. Skipping TypeScript bindings generation.")

    # Rust generation
    _generate_rust(wrapper_path, rust_out)

    # Cleanup
    if os.path.exists(wrapper_path):
        os.unlink(wrapper_path)

    print("Cross-language bindings generated successfully.")


if __name__ == "__main__":
    main()
