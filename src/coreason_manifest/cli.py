# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import sys
from importlib.metadata import PackageNotFoundError, version

import typer
from rich import print as rprint

from coreason_manifest.utils.loader import load_flow_from_file
from coreason_manifest.utils.validator import validate_flow
from coreason_manifest.utils.visualizer import to_mermaid

app = typer.Typer(help="CoReason Manifest CLI")


def version_callback(value: bool) -> None:
    if value:
        try:
            pkg_version = version("coreason_manifest")
        except PackageNotFoundError:
            pkg_version = "unknown"
        typer.echo(f"coreason {pkg_version}")
        raise typer.Exit()


@app.callback()  # type: ignore[untyped-decorator]
def main(
    version: bool | None = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show the version and exit."
    ),
) -> None:
    """
    CoReason Manifest CLI
    """


@app.command(name="validate")  # type: ignore[untyped-decorator]
def validate(file: str = typer.Argument(..., help="Path to the manifest file")) -> int:
    """
    Validate a manifest file
    """
    return _handle_validate(file)


@app.command(name="visualize")  # type: ignore[untyped-decorator]
def visualize(file: str = typer.Argument(..., help="Path to the manifest file")) -> int:
    """
    Generate Mermaid diagram from manifest
    """
    return _handle_visualize(file)


@app.command(name="create")  # type: ignore[untyped-decorator]
def create() -> None:
    """
    Create a new manifest (Placeholder)
    """
    rprint("[yellow]Create command is not yet implemented.[/yellow]")
    raise typer.Exit(code=1)


def _handle_validate(file_path: str) -> int:
    try:
        flow = load_flow_from_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        rprint(f"[red]❌ Error loading file: {e}[/red]", file=sys.stderr)
        raise typer.Exit(code=1) from e
    except Exception as e:
        rprint(f"[red]❌ Unexpected Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(code=1) from e

    errors = validate_flow(flow)

    if not errors:
        rprint("[green]✅ Flow is valid.[/green]")
        return 0

    rprint("[red]❌ Validation failed:[/red]", file=sys.stderr)
    for error in errors:
        rprint(f"[red]- {error}[/red]", file=sys.stderr)
    raise typer.Exit(code=1)


def _handle_visualize(file_path: str) -> int:
    try:
        flow = load_flow_from_file(file_path)
    except (FileNotFoundError, ValueError) as e:
        rprint(f"[red]❌ Error loading file: {e}[/red]", file=sys.stderr)
        raise typer.Exit(code=1) from e
    except Exception as e:
        rprint(f"[red]❌ Unexpected Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(code=1) from e

    # Optional: Warn if invalid, but proceed
    errors = validate_flow(flow)
    if errors:
        rprint("[yellow]⚠️ Warning: Flow has validation errors:[/yellow]", file=sys.stderr)
        for error in errors:
            rprint(f"[yellow]- {error}[/yellow]", file=sys.stderr)

    diagram = to_mermaid(flow)
    print(diagram)
    return 0


if __name__ == "__main__":
    app()
