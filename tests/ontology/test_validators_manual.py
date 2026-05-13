# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

import pytest

from coreason_manifest.spec import ontology

class_names = [
    "RoutingFrontierPolicy",
    "SaeLatentPolicy",
    "MultimodalTokenAnchorState",
    "CausalDirectedEdgeState",
    "DistributionProfile",
    "DocumentLayoutManifest",
    "DelegatedCapabilityManifest",
    "GlobalGovernancePolicy",
    "DynamicRoutingManifest",
    "GenerativeTaxonomyManifest",
    "FormalVerificationReceipt",
    "RDFSerializationIntent",
    "ExecutionSubstrateProfile",
    "MemoizedNodeProfile",
    "MCPServerManifest",
    "TransitionEdgeProfile",
    "CyclicEdgeProfile",
    "CognitiveActionSpaceManifest",
    "OntologicalSurfaceProjectionManifest",
    "MCPClientIntent",
    "MacroGridProfile",
    "MarketContract",
    "MarketResolutionState",
    "NDimensionalTensorManifest",
    "CompositeNodeProfile",
    "PeftAdapterContract",
    "ExogenousEpistemicEvent",
    "HypothesisGenerationEvent",
    "TaskAwardReceipt",
    "DiscourseTreeManifest",
    "UtilityJustificationGraphReceipt",
    "HoareLogicProofReceipt",
    "SemanticEdgeState",
    "CognitiveAgentNodeProfile",
    "HierarchicalDOMManifest",
    "ObservabilityLODPolicy",
    "CouncilTopologyManifest",
    "EvaluatorOptimizerTopologyManifest",
    "EvolutionaryTopologyManifest",
    "SMPCTopologyManifest",
    "SwarmTopologyManifest",
    "NeurosymbolicVerificationTopologyManifest",
    "WorkflowManifest",
    "EpistemicQuarantineSnapshot",
    "BeliefMutationEvent",
    "EpistemicAxiomVerificationReceipt",
    "CognitiveDualVerificationReceipt",
    "EpistemicCurriculumManifest",
    "ConstrainedDecodingPolicy",
    "EmpiricalStatisticalProfile",
    "EpistemicZeroTrustReceipt",
    "EpistemicLedgerState",
]


@pytest.mark.parametrize("cls_name", class_names)
def test_validators_manual_debug(cls_name: str) -> None:
    cls = getattr(ontology, cls_name)

    kwargs: dict[str, Any] = {}
    for field_name, field_info in cls.model_fields.items():
        ann = str(field_info.annotation).lower()
        if "list[" in ann or "set[" in ann or "tuple[" in ann or "dict[" in ann:
            kwargs[field_name] = []
        elif "str" in ann:
            kwargs[field_name] = ""
        else:
            kwargs[field_name] = None

    instance = cls.model_construct(**kwargs)

    for name, dec in cls.__pydantic_decorators__.model_validators.items():
        if dec.info.mode == "after":
            try:
                dec.func(instance)
            except Exception as e:
                print(f"Error in {cls_name}.{name}: {e}")

    for name, dec in cls.__pydantic_decorators__.field_validators.items():
        try:
            import inspect

            sig = inspect.signature(dec.func)
            for field in dec.info.fields:
                v = getattr(instance, field, [])
                if len(sig.parameters) == 1:
                    dec.func(v)
                elif len(sig.parameters) == 2:
                    dec.func(cls, v)
                elif len(sig.parameters) == 3:
                    dec.func(cls, v, None)
        except Exception as e:
            print(f"Error in field_validator {cls_name}.{name}: {e}")
