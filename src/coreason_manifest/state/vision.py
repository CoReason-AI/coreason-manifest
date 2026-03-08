# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the universal visual-semantic extraction schemas.
This is a STRICTLY EPISTEMIC BOUNDARY. These schemas translate raw visual arrays into
verified, geometric topologies. YOU ARE EXPLICITLY FORBIDDEN from introducing execution
scripts or OCR parsing loops here. All validation must be pure mathematical geometry."""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.state.semantic import MultimodalTokenAnchor

# ==========================================
# 1. Document Layout Analysis
# ==========================================


class DocumentLayoutBlock(CoreasonBaseModel):
    block_id: str = Field(min_length=1, description="Unique structural identifier for this geometric region.")
    block_type: Literal["header", "paragraph", "figure", "table", "footnote", "caption", "equation"] = Field(
        description="The taxonomic classification of the layout region."
    )
    anchor: MultimodalTokenAnchor = Field(description="The strict visual and token coordinate bindings for this block.")


class DocumentLayoutAnalysis(CoreasonBaseModel):
    blocks: dict[str, DocumentLayoutBlock] = Field(
        description="Dictionary mapping block_ids to their strict spatial definitions."
    )
    reading_order_edges: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Directed edges defining the topological sort (chronological flow) of the document.",
    )

    @model_validator(mode="after")
    def verify_dag_and_integrity(self) -> Self:
        adj: dict[str, list[str]] = {node_id: [] for node_id in self.blocks}
        for source, target in self.reading_order_edges:
            if source not in self.blocks:
                raise ValueError(f"Source block '{source}' does not exist.")
            if target not in self.blocks:
                raise ValueError(f"Target block '{target}' does not exist.")
            adj[source].append(target)

        # Detect cycles (DFS)
        visited: set[str] = set()
        recursion_stack: set[str] = set()

        for start_node in self.blocks:
            if start_node in visited:
                continue

            stack = [(start_node, iter(adj[start_node]))]
            visited.add(start_node)
            recursion_stack.add(start_node)

            while stack:
                curr, neighbors = stack[-1]
                try:
                    neighbor = next(neighbors)
                    if neighbor not in visited:
                        visited.add(neighbor)
                        recursion_stack.add(neighbor)
                        stack.append((neighbor, iter(adj[neighbor])))
                    elif neighbor in recursion_stack:
                        raise ValueError("Reading order contains a cyclical contradiction.")
                except StopIteration:
                    recursion_stack.remove(curr)
                    stack.pop()
        return self


# ==========================================
# 2. Mathematical Notation Normalization
# ==========================================


class MathematicalNotationExtraction(CoreasonBaseModel):
    math_type: Literal["inline", "display"] = Field(description="The structural context of the equation.")
    syntax: Literal["latex", "mathml"] = Field(description="The strict symbolic compilation language.")
    expression: str = Field(min_length=1, description="The raw, unescaped mathematical syntax string.")
    anchor: MultimodalTokenAnchor = Field(
        description="The strict visual and token coordinate bindings. Cannot be None."
    )

    @model_validator(mode="after")
    def verify_grounding(self) -> Self:
        if self.anchor.token_span_start is None and self.anchor.bounding_box is None:
            raise ValueError("Mathematical extractions must have a definitive visual or token bounding box.")
        return self


# ==========================================
# 3. Visual-to-Numerical Statistical Data
# ==========================================

type ChartAxisScale = Literal["linear", "log", "categorical", "datetime"]


class AffineTransformMatrix(CoreasonBaseModel):
    pixel_min: float = Field(description="The absolute minimal visual coordinate on this axis.")
    pixel_max: float = Field(description="The absolute maximal visual coordinate on this axis.")
    domain_min: float = Field(description="The semantic/data value corresponding to pixel_min.")
    domain_max: float = Field(description="The semantic/data value corresponding to pixel_max.")
    scale_type: ChartAxisScale = Field(description="The mathematical progression between min and max.")


class StatisticalChartExtraction(CoreasonBaseModel):
    axes: dict[str, AffineTransformMatrix] = Field(
        description="Named axes (e.g., 'x', 'y') defining the affine transformation boundaries."
    )
    data_series: list[dict[str, float | str]] = Field(
        description="The discrete semantic tuples extracted from the chart markers."
    )

    @model_validator(mode="after")
    def verify_dimensional_isometry(self) -> Self:
        axis_keys = set(self.axes.keys())
        for point in self.data_series:
            point_keys = set(point.keys())
            if not point_keys.issubset(axis_keys) and not axis_keys.issubset(point_keys):
                # We allow extra keys for series names/labels, but it MUST contain all axis keys
                missing = axis_keys - point_keys
                if missing:
                    raise ValueError(f"Data point missing required axis dimensions: {missing}")
        return self


# ==========================================
# 4. Tabular Data Serialization
# ==========================================


class TableCell(CoreasonBaseModel):
    row_index: int = Field(ge=0, description="The zero-indexed absolute matrix row.")
    col_index: int = Field(ge=0, description="The zero-indexed absolute matrix column.")
    row_span: int = Field(default=1, ge=1, description="The vertical height of the cell.")
    col_span: int = Field(default=1, ge=1, description="The horizontal width of the cell.")
    content: str = Field(description="The normalized text value.")
    anchor: MultimodalTokenAnchor = Field(description="The physical location of the cell within the image or document.")


class TabularDataExtraction(CoreasonBaseModel):
    cells: list[TableCell] = Field(description="The sparse tensor representing all populated cells.")

    @model_validator(mode="after")
    def detect_geometric_collisions(self) -> Self:
        occupied_coordinates: set[tuple[int, int]] = set()

        for cell in self.cells:
            for r in range(cell.row_index, cell.row_index + cell.row_span):
                for c in range(cell.col_index, cell.col_index + cell.col_span):
                    coord = (r, c)
                    if coord in occupied_coordinates:
                        raise ValueError(f"Geometric Collision Detected: Cell overlapping at coordinate {coord}.")
                    occupied_coordinates.add(coord)
        return self
