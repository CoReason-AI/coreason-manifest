from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.domains.scivis_provenance import (
    ActorIdentity,
    ActorType,
    ElementAttribution,
    ExecutionAudit,
    ProvenanceManifest,
    StateHashLog,
)


@st.composite
def actor_identity_strategy(draw: st.DrawFn) -> ActorIdentity:
    return ActorIdentity(
        actor_type=draw(st.sampled_from(list(ActorType))),
        actor_version_or_id=draw(st.text(min_size=1)),
    )


@st.composite
def element_attribution_strategy(draw: st.DrawFn) -> ElementAttribution:
    return ElementAttribution(
        target_element_id=draw(st.text(min_size=1)),
        created_by=draw(actor_identity_strategy()),
        last_modified_by=draw(actor_identity_strategy()),
        was_human_verified=draw(st.booleans()),
    )


@st.composite
def execution_audit_strategy(draw: st.DrawFn) -> ExecutionAudit:
    return ExecutionAudit(
        target_element_id=draw(st.text(min_size=1)),
        dataset_checksum=draw(st.one_of(st.none(), st.text(min_size=1))),
        execution_script_hash=draw(st.one_of(st.none(), st.text(min_size=1))),
    )


@st.composite
def state_hash_log_strategy(draw: st.DrawFn) -> StateHashLog:
    return StateHashLog(
        intent_hash=draw(st.text(min_size=1)),
        semantic_ast_hash=draw(st.text(min_size=1)),
        spatial_ast_hash=draw(st.text(min_size=1)),
    )


@st.composite
def provenance_manifest_strategy(draw: st.DrawFn) -> ProvenanceManifest:
    return ProvenanceManifest(
        manifest_id=draw(st.text(min_size=1)),
        timestamp_utc=draw(st.text(min_size=1)),
        state_chain=draw(state_hash_log_strategy()),
        element_attributions=draw(st.lists(element_attribution_strategy(), max_size=5)),
        execution_audits=draw(st.lists(execution_audit_strategy(), max_size=5)),
        is_journal_compliant=draw(st.booleans()),
    )


@given(provenance_manifest_strategy())
def test_provenance_manifest_round_trip(manifest: ProvenanceManifest) -> None:
    json_data = manifest.model_dump_json()
    loaded_manifest = ProvenanceManifest.model_validate_json(json_data)
    assert manifest == loaded_manifest
