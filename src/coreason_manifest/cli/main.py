from __future__ import annotations

import typer

from coreason_manifest.cli.scaffold import app as scaffold_app

app = typer.Typer(help="The Meta-Engineering CLI")

app.add_typer(scaffold_app, name="scaffold", help="AST-Driven Ontological Scaffolding")

if __name__ == "__main__":
    app()
