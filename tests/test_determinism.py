# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from coreason_manifest.presentation.intents import DraftingIntent, PresentationEnvelope
from coreason_manifest.presentation.scivis import InsightCard, MacroGrid
from coreason_manifest.state.events import ObservationEvent
from coreason_manifest.state.memory import EpistemicLedger
from coreason_manifest.workflow.envelope import WorkflowEnvelope
from coreason_manifest.workflow.nodes import AgentNode
from coreason_manifest.workflow.topologies import DAGTopology


def test_workflow_envelope_determinism() -> None:
    node1 = AgentNode(description="First node")
    node2 = AgentNode(description="Second node")
    topology1 = DAGTopology(nodes={"node_a": node1, "node_b": node2}, allow_cycles=False, backpressure=None)
    topology2 = DAGTopology(nodes={"node_b": node2, "node_a": node1}, allow_cycles=False, backpressure=None)

    env1 = WorkflowEnvelope(manifest_version="1.0.0", topology=topology1)
    env2 = WorkflowEnvelope(manifest_version="1.0.0", topology=topology2)

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)


def test_presentation_envelope_determinism() -> None:
    intent1 = DraftingIntent()
    intent2 = DraftingIntent()

    panel1 = InsightCard(panel_id="panel_1", title="Insight 1", markdown_content="Content 1")
    panel2 = InsightCard(panel_id="panel_2", title="Insight 2", markdown_content="Content 2")

    grid1 = MacroGrid(layout_matrix=[["panel_1", "panel_2"]], panels=[panel1, panel2])
    grid2 = MacroGrid(layout_matrix=[["panel_1", "panel_2"]], panels=[panel1, panel2])

    env1 = PresentationEnvelope(intent=intent1, grid=grid1)
    env2 = PresentationEnvelope(intent=intent2, grid=grid2)

    assert env1.model_dump_canonical() == env2.model_dump_canonical()
    assert hash(env1) == hash(env2)


def test_epistemic_ledger_determinism() -> None:
    event1 = ObservationEvent(event_id="obs_1", timestamp=100.0)
    event2 = ObservationEvent(event_id="obs_2", timestamp=200.0)

    ledger1 = EpistemicLedger(history=[event1, event2])
    ledger2 = EpistemicLedger(history=[event1, event2])

    assert ledger1.model_dump_canonical() == ledger2.model_dump_canonical()
    assert hash(ledger1) == hash(ledger2)
