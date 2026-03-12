from typing import Literal

import hypothesis.strategies as st
from hypothesis import given

from coreason_manifest.spec.ontology import SMPCTopologyManifest, SystemNodeProfile

# W3C DID specification regex from NodeIdentifierState
did_strategy = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)


@given(
    protocol=st.sampled_from(["garbled_circuits", "secret_sharing", "oblivious_transfer"]),
    func_uri=st.text(min_size=1),
    node_ids=st.lists(did_strategy, min_size=2, unique=True),
)
def test_smpc_topology_manifest_ordering(
    protocol: Literal["garbled_circuits", "secret_sharing", "oblivious_transfer"], func_uri: str, node_ids: list[str]
) -> None:
    """
    Test that SMPCTopologyManifest preserves the structural sequence of participant_node_ids
    in accordance with Paradigm 2: Structural Sequences (The Topological Exemption).
    """

    # We enforce specific ordering to make sure the array is not sorted by the validator
    ordered_node_ids = sorted(node_ids, reverse=True)

    # BaseTopologyManifest requires `nodes`
    manifest = SMPCTopologyManifest(
        smpc_protocol=protocol,
        joint_function_uri=func_uri,
        participant_node_ids=ordered_node_ids,
        nodes={n_id: SystemNodeProfile(description="dummy") for n_id in ordered_node_ids},
    )

    # The structural order MUST be maintained
    assert manifest.participant_node_ids == ordered_node_ids
