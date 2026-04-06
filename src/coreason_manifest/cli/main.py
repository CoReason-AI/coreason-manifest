# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from __future__ import annotations

import typer

from coreason_manifest.cli.scaffold import app as scaffold_app

app = typer.Typer(help="The Meta-Engineering CLI")

app.add_typer(scaffold_app, name="scaffold", help="AST-Driven Ontological Scaffolding")

if __name__ == "__main__":
    app()
