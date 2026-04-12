with open("tests/test_hash_invariance.py") as f:
    content = f.read()

import_statement = """from coreason_manifest.spec.ontology import (
    CognitiveAgentNodeProfile,
    DraftingIntent,
    EpistemicSecurityProfile,
    ExecutionNodeReceipt,
    SpatialHardwareProfile,
    TraceExportManifest,
)"""

content = content.replace(import_statement, "")

top_import = """from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    CognitiveAgentNodeProfile,
    DraftingIntent,
    EpistemicSecurityProfile,
    ExecutionNodeReceipt,
    PermissionBoundaryPolicy,
    RedactionPolicy,
    SaeLatentPolicy,
    SemanticClassificationProfile,
    SemanticFlowPolicy,
    SideEffectProfile,
    SpatialHardwareProfile,
    SpatialToolManifest,
    TraceExportManifest,
    TransitionEdgeProfile,
)"""

old_top_import = """from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    CognitiveAgentNodeProfile,
    DraftingIntent,
    EpistemicSecurityProfile,
    ExecutionNodeReceipt,
    PermissionBoundaryPolicy,
    RedactionPolicy,
    SaeLatentPolicy,
    SemanticClassificationProfile,
    SemanticFlowPolicy,
    SideEffectProfile,
    SpatialHardwareProfile,
    SpatialToolManifest,
    TraceExportManifest,
    TransitionEdgeProfile,
)"""

# In case it is the first time running
content = content.replace(old_top_import, top_import)

old_top_import_2 = """from coreason_manifest.spec.ontology import (
    CognitiveActionSpaceManifest,
    PermissionBoundaryPolicy,
    RedactionPolicy,
    SaeLatentPolicy,
    SemanticClassificationProfile,
    SemanticFlowPolicy,
    SideEffectProfile,
    SpatialToolManifest,
    TransitionEdgeProfile,
)"""

content = content.replace(old_top_import_2, top_import)

with open("tests/test_hash_invariance.py", "w") as f:
    f.write(content)
