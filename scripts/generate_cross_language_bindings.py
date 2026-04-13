#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


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

    env = os.environ.copy()
    env["npm_config_yes"] = "true"
    env["npm_config_loglevel"] = "error"

    use_shell = os.name == "nt"

    print("Generating TypeScript bindings...")
    ts_cmd = ["npx", "quicktype", "-s", "schema", schema_file, "-o", ts_out, "--just-types"]
    subprocess.run(ts_cmd, check=True, env=env, shell=use_shell)  # noqa: S603 # nosec B603

    print("Generating Rust bindings...")
    rust_cmd = [
        "npx",
        "quicktype",
        "-s",
        "schema",
        schema_file,
        "-o",
        rust_out,
        "--visibility",
        "public",
        "--derive-debug",
        "--derive-clone",
        "--derive-partial-eq",
    ]
    subprocess.run(rust_cmd, check=True, env=env, shell=use_shell)  # noqa: S603 # nosec B603

    print("Post-processing Rust bindings...")
    with open(rust_out, encoding="utf-8") as f:
        rust_code = f.read()

    rust_code = "#![allow(non_snake_case)]\n#![allow(non_camel_case_types)]\n" + rust_code

    with open(rust_out, "w", encoding="utf-8") as f:
        f.write(rust_code)

    print("Formatting TypeScript...")
    subprocess.run(["npx", "prettier", "--write", ts_out], check=True, env=env, shell=use_shell)  # noqa: S603, S607 # nosec B603 B607

    print("Formatting Rust...")
    subprocess.run(["cargo", "fmt", "--manifest-path", "bindings/rust/Cargo.toml"], check=True, shell=use_shell)  # noqa: S607 # nosec B603 B607

    print("Cross-language bindings generated successfully.")


if __name__ == "__main__":
    main()
