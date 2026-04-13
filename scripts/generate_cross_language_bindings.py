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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _build_rooted_schema(schema_path: str, output_path: str) -> None:
    """Build a wrapper schema with a root `type: object` so codegen tools can anchor on it.

    The raw exported schema is `$defs`-only (no root type), which causes most codegen
    tools to emit trivial stubs. This wrapper exposes every `$def` as a property of a
    synthetic root object.
    """
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    defs = schema.get("$defs", {})

    wrapper = {
        "$schema": "http://json-schema.org/draft-07/schema#",
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


def main() -> None:
    # Ensure we are working from the project root
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    schema_file = "coreason_ontology.schema.json"
    ts_out = "bindings/typescript/src/ontology.ts"
    rust_out = "bindings/rust/src/ontology.rs"

    if not os.path.exists(schema_file):
        print(f"Error: Schema file {schema_file} not found. Please generate it first.")
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
