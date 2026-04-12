from pathlib import Path

REPO_ROOT = Path(r"c:\files\git\github\coreason-ai\coreason-manifest")

RENAMES = {
    "LiquidTypeContract": "AlgebraicRefinementContract",
    "EpistemicRewardModelPolicy": "EpistemicRewardGradientPolicy",
    "SemanticRelationalRecordState": "SemanticRelationalVectorState",
    "ManifoldAlignmentMetric": "ManifoldAlignmentMetricProfile",
    "IdeationPhase": "IdeationPhaseProfile",
    "StochasticStateNode": "StochasticNodeState",
    "HypothesisSuperposition": "HypothesisSuperpositionState",
    "StochasticTopology": "StochasticTopologyManifest",
    "TargetTopologyEnum": "TargetTopologyProfile",
    "CryptographicProvenanceMixin": "CryptographicProvenancePolicy",
    "ActiveInferenceEpoch": "ActiveInferenceEpochState",
    "ComputationalThermodynamics": "ComputationalThermodynamicsProfile",
    "SemanticMappingHeuristicProposal": "SemanticMappingHeuristicIntent",
    "CognitiveSwarmDeploymentMacro": "CognitiveSwarmDeploymentManifest",
    "PostCoordinatedSemanticConcept": "PostCoordinatedSemanticState",
    "EmpiricalStatisticalQualifier": "EmpiricalStatisticalProfile",
    "DempsterShaferBeliefVector": "DempsterShaferBeliefState",
    # Specific edge cases in references
    "SemanticRelationalRecord": "SemanticRelationalVectorState",  # In `_inject_cognitive_routing_cluster`
    "test_semantic_relational_record": "test_semantic_relational_vector",
}

files = list(REPO_ROOT.rglob("*.py"))
for f in files:
    if "scripts\\audit_compliance.py" in str(f) or "scripts\\refactor_" in str(f) or ".venv" in str(f):
        continue
    content = f.read_text(encoding="utf-8")
    original = content
    for old, new in RENAMES.items():
        content = content.replace(old, new)

    if content != original:
        f.write_text(content, encoding="utf-8")
        print(f"Updated {f.relative_to(REPO_ROOT)}")

# Rename the test file physically
old_test = REPO_ROOT / "tests" / "contracts" / "test_semantic_relational_record.py"
if old_test.exists():
    new_test = REPO_ROOT / "tests" / "contracts" / "test_semantic_relational_vector.py"
    old_test.rename(new_test)
    print(f"Renamed {old_test.name} to {new_test.name}")
