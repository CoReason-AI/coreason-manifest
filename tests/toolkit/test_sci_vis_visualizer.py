import unittest.mock
from unittest.mock import MagicMock

from coreason_manifest.core.workflow.flow import GraphFlow
from coreason_manifest.toolkit.visualizer import to_mermaid


def test_visual_inspector_mermaid_styling() -> None:
    # Create a dummy Flow simply to pass into to_mermaid
    dummy_flow = MagicMock(spec=GraphFlow)

    # We mock out get_unified_topology because `to_mermaid` calls it
    # to retrieve a flat list of nodes and edges.
    with unittest.mock.patch("coreason_manifest.toolkit.visualizer.get_unified_topology") as mock_topology:
        # Create a mock node representing the new 'visual_inspector'
        mock_node = MagicMock()
        mock_node.id = "mock_visual_node"
        mock_node.type = "visual_inspector"
        mock_node.presentation = None

        # get_unified_topology returns (nodes, edges)
        mock_topology.return_value = ([mock_node], [])

        # Run the visualizer function
        result = to_mermaid(dummy_flow)

        # Verify the custom shape is applied. Default _get_node_shape mapping is {{ for visual_inspector.
        assert "{{" in result
        assert "}}" in result

        # Verify the distinct styling class is injected in the output strings
        assert "classDef visual_inspector fill:#fdebd0,stroke:#d35400,stroke-width:2px;" in result
        assert "mock_visual_node:::visual_inspector" in result or "mock_visual_node" in result
