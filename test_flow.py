from coreason_manifest.core.workflow.flow import GraphFlow, LinearFlow

print("GraphFlow enforce_lifecycle_constraints:", hasattr(GraphFlow, "enforce_lifecycle_constraints"))
print("LinearFlow enforce_lifecycle_constraints:", hasattr(LinearFlow, "enforce_lifecycle_constraints"))
