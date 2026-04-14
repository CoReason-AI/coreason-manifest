#!/usr/bin/env python3
# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import argparse
import ast
import json
import re
import subprocess
import sys
import types
import urllib.request
from pathlib import Path
from typing import Annotated, Any, ForwardRef, TypeAliasType, Union, cast, get_args, get_origin, get_type_hints

import rustworkx as rx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import coreason_manifest.spec.ontology as onto  # noqa: E402
from coreason_manifest.utils.algebra import get_ontology_schema  # noqa: E402

# ==========================================
# 1. evaluate_epistemic_compliance
# ==========================================
FORBIDDEN_CRUD = [
    "Data",
    "Model",
    "Type",
    "Info",
    "ID",
    "Record",
    "Create",
    "Read",
    "Update",
    "Delete",
    "Remove",
    "Group",
    "List",
    "Memory",
    "Link",
    "Merge",
    "Overwrite",
    "History",
]
REQUIRED_SUFFIXES = [
    "Receipt",
    "Event",
    "Premise",
    "Intent",
    "Task",
    "Policy",
    "Contract",
    "SLA",
    "State",
    "Snapshot",
    "Manifest",
    "Profile",
    "Proxy",
    "Mask",
    "Constraint",
    "Invariant",
]
DOCSTRING_PARTS = ["AGENT INSTRUCTION:", "CAUSAL AFFORDANCE:", "EPISTEMIC BOUNDS:", "MCP ROUTING TRIGGERS:"]


def evaluate_epistemic_compliance() -> None:
    print("Starting audit...")
    src_dir = REPO_ROOT / "src"
    tests_dir = REPO_ROOT / "tests"
    scripts_dir = REPO_ROOT / "scripts"
    all_files = list(src_dir.rglob("*.py")) + list(tests_dir.rglob("*.py")) + list(scripts_dir.rglob("*.py"))

    header_errors = 0
    class_violations = 0

    header = "# Copyright (c) 2026 CoReason, Inc"
    for filepath in all_files:
        content = filepath.read_text(encoding="utf-8")
        if not content.startswith(header):
            print(f"[HEADER ERROR] {filepath.relative_to(REPO_ROOT)}")
            header_errors += 1

    for filepath in src_dir.rglob("spec/ontology.py"):
        print(f"Checking {filepath.relative_to(REPO_ROOT)}")
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)

        class CodeVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.class_errors: dict[str, list[str]] = {}

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                errors: list[str] = []
                name = node.name
                if not name.startswith("_"):
                    is_exception = any(
                        isinstance(base, ast.Name)
                        and (base.id == "ValueError" or base.id.endswith("Error") or base.id == "Exception")
                        for base in node.bases
                    )
                    errors.extend(
                        f"Forbidden CRUD term '{crud}' in name"
                        for crud in FORBIDDEN_CRUD
                        if crud.lower() in name.lower() and not is_exception and crud in name
                    )
                    if not is_exception and name != "CoreasonBaseState":
                        has_suffix = any(name.endswith(suffix) for suffix in REQUIRED_SUFFIXES)
                        if not has_suffix:
                            errors.append(f"Missing required suffix in name (ends with: {name.split('`')[-1]})")
                    inherits_base = any(getattr(base, "id", "") == "CoreasonBaseState" for base in node.bases)
                    if inherits_base:
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            errors.append("Missing docstring for CoreasonBaseState subclass")
                        else:
                            errors.extend(
                                f"Missing '{part}' in docstring" for part in DOCSTRING_PARTS if part not in docstring
                            )
                if errors:
                    self.class_errors[name] = errors
                self.generic_visit(node)

            def visit_TypeAlias(self, node: ast.stmt) -> None:
                errors: list[str] = []
                if isinstance(node.name, ast.Name):  # type: ignore
                    name: str = node.name.id  # type: ignore
                    errors.extend(
                        f"Forbidden CRUD term '{crud}' in alias name" for crud in FORBIDDEN_CRUD if crud in name
                    )
                self.generic_visit(node)

        visitor = CodeVisitor()
        visitor.visit(tree)
        for cls_name, errs in visitor.class_errors.items():
            print(f"[CLASS ERROR] {cls_name}:")
            for e in errs:
                print(f"  - {e}")
            class_violations += 1


# ==========================================
# 2. evaluate_architectural_manifold
# ==========================================
def evaluate_architectural_manifold() -> None:
    forbidden_patterns = [
        r"import\s+fastapi",
        r"from\s+fastapi\s+import",
        r"import\s+flask\b",
        r"from\s+flask\s+import",
        r"os\.mkdir",
        r"os\.makedirs",
        r"logger\.add",
    ]
    diff_content = sys.stdin.read()
    in_py_file = False
    added_lines = []
    for line in diff_content.splitlines():
        if line.startswith("+++ "):
            filename = line[4:].strip().removeprefix("b/")
            in_py_file = filename.endswith(".py")
            continue
        if in_py_file and line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
    for added_line in added_lines:
        for pattern in forbidden_patterns:
            if re.search(pattern, added_line, re.IGNORECASE):
                print(f"Architectural Violation: Forbidden runtime artifact detected: {added_line}")
                sys.exit(1)
    print("Architecture evaluation passed: Passive by Design.")
    sys.exit(0)


# ==========================================
# 3. evaluate_ast_instantiation_bounds
# ==========================================
def evaluate_ast_instantiation_bounds() -> None:
    def is_forbidden_config(node: ast.expr) -> bool:
        forbidden_keys = {"frozen", "strict", "validate_assignment"}
        if isinstance(node, ast.Call) and (
            getattr(node.func, "id", None) == "ConfigDict" or getattr(node.func, "attr", None) == "ConfigDict"
        ):
            for kw in node.keywords:
                if kw.arg in forbidden_keys and not (isinstance(kw.value, ast.Constant) and kw.value.value is True):
                    return True
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=False):
                if (
                    isinstance(key, ast.Constant)
                    and key.value in forbidden_keys
                    and not (isinstance(value, ast.Constant) and value.value is True)
                ):
                    return True
        return False

    def get_decorators(node: ast.FunctionDef) -> set[str]:
        decorators = set()
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.add(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.add(dec.func.id)
            elif isinstance(dec, ast.Attribute):
                decorators.add(dec.attr)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                decorators.add(dec.func.attr)
        return decorators

    target_dir = REPO_ROOT / "src" / "coreason_manifest" / "spec"
    if not target_dir.is_dir():
        print(f"Error: Directory {target_dir} not found.", file=sys.stderr)
        sys.exit(1)

    py_files = list(target_dir.rglob("*.py"))
    known_classes: dict[str, set[str]] = {}
    for filepath in py_files:
        with open(filepath, encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(filepath))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        bases = set()
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                bases.add(base.id)
                            elif isinstance(base, ast.Attribute):
                                bases.add(base.attr)
                            elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
                                bases.add(base.value.id)
                        known_classes[node.name] = bases
            except SyntaxError as e:
                print(
                    f"Syntax error while collecting class metadata from {filepath}: {e}; skipping file.",
                    file=sys.stderr,
                )

    has_violations = False
    for filepath in py_files:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
            try:
                tree = ast.parse(source, filename=str(filepath))
            except SyntaxError as e:
                print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
                has_violations = True
                continue
        allowed_methods = {"compile_to_base_topology", "generate_node_hash", "model_dump_canonical", "__hash__"}

        def is_coreason_model(class_name: str, visited: frozenset[str] = frozenset()) -> bool:
            if class_name == "CoreasonBaseState":
                return True
            if class_name in visited or class_name not in known_classes:
                return False
            return any(is_coreason_model(base, visited | frozenset([class_name])) for base in known_classes[class_name])

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not is_coreason_model(node.name):
                    continue
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name in ("__init__", "__post_init__"):
                            print(
                                f"Rule A Violation: Class '{node.name}' defines forbidden method '{item.name}' in {filepath}",
                                file=sys.stderr,
                            )
                            has_violations = True
                        if item.name not in allowed_methods:
                            decorators = get_decorators(item)
                            if (
                                "model_validator" not in decorators
                                and "field_validator" not in decorators
                                and "field_serializer" not in decorators
                            ):
                                print(
                                    f"Rule B Violation: Class '{node.name}' function '{item.name}' missing validator decorator in {filepath}",
                                    file=sys.stderr,
                                )
                                has_violations = True
                    elif isinstance(item, ast.AnnAssign):
                        if (
                            isinstance(item.target, ast.Name)
                            and item.target.id == "model_config"
                            and item.value is not None
                            and is_forbidden_config(item.value)
                        ):
                            print(
                                f"Rule C Violation: Class '{node.name}' attempts to bypass immutability lock in {filepath}",
                                file=sys.stderr,
                            )
                            has_violations = True
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if (
                                isinstance(target, ast.Name)
                                and target.id == "model_config"
                                and is_forbidden_config(item.value)
                            ):
                                print(
                                    f"Rule C Violation: Class '{node.name}' attempts to bypass immutability lock in {filepath}",
                                    file=sys.stderr,
                                )
                                has_violations = True
    if has_violations:
        print("AST structural bounds check failed.", file=sys.stderr)
        sys.exit(1)
    print("AST structural bounds check passed.", file=sys.stdout)


# ==========================================
# 4. evaluate_topological_reachability
# ==========================================
def evaluate_topological_reachability() -> None:
    def get_all_subclasses(cls: type) -> set[type]:
        subclasses = set()
        for sub in cls.__subclasses__():
            subclasses.add(sub)
            subclasses.update(get_all_subclasses(sub))
        return subclasses

    excluded_base_classes = {"CryptographicProvenancePolicy", "BoundedJSONRPCIntent", "AnyToolchainState"}
    class_registry = {
        cls.__name__.split("[")[0]: cls
        for cls in get_all_subclasses(onto.CoreasonBaseState)
        if cls.__name__.split("[")[0] not in excluded_base_classes
    }
    alias_registry = {name: obj.__value__ for name, obj in vars(onto).items() if isinstance(obj, TypeAliasType)}

    graph = rx.PyDiGraph()
    name_to_idx = {}
    idx_to_name = {}
    for cls_name in class_registry:
        idx = graph.add_node(cls_name)
        name_to_idx[cls_name] = idx
        idx_to_name[idx] = cls_name

    def extract_referenced_models(annotation: Any, seen: set[int | str] | None = None) -> list[type]:
        if seen is None:
            seen = set()
        ann_id = id(annotation) if not isinstance(annotation, str) else annotation
        if ann_id in seen:
            return []
        seen.add(ann_id)
        if isinstance(annotation, str):
            clean_string = annotation.strip("'\"")
            if "[" in clean_string:
                clean_string = clean_string.split("[")[0]
            if clean_string in alias_registry:
                return extract_referenced_models(alias_registry[clean_string], seen)
            if clean_string in class_registry:
                return [class_registry[clean_string]]
            return []
        if isinstance(annotation, ForwardRef):
            return extract_referenced_models(annotation.__forward_arg__, seen)
        if isinstance(annotation, TypeAliasType):
            return extract_referenced_models(annotation.__value__, seen)
        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation)
            if args:
                return extract_referenced_models(args[0], seen)
            return []
        if origin is Union or origin is types.UnionType:
            result = []
            for arg in get_args(annotation):
                result.extend(extract_referenced_models(arg, seen))
            return result
        if origin in (list, set, tuple, dict):
            result = []
            for arg in get_args(annotation):
                result.extend(extract_referenced_models(arg, seen))
            return result
        if isinstance(annotation, type) and issubclass(annotation, onto.CoreasonBaseState):
            return [annotation]
        return []

    for cls_name, cls in class_registry.items():
        try:
            hints = get_type_hints(cls, vars(onto), include_extras=True)
            for resolved_type in hints.values():
                for ref_model in extract_referenced_models(resolved_type):
                    ref_name = ref_model.__name__.split("[")[0]
                    if ref_name in class_registry:
                        graph.add_edge(name_to_idx[cls_name], name_to_idx[ref_name], None)
        except Exception as e:
            print(f"Warning: Failed to resolve type hints for {cls_name}: {e}")

    root_nodes = [
        "WorkflowManifest",
        "EpistemicLedgerState",
        "StateHydrationManifest",
        "KinematicDeltaManifest",
        "TraceExportManifest",
        "FederatedSecurityMacroManifest",
        "CognitiveSwarmDeploymentManifest",
        "AdversarialMarketTopologyManifest",
        "ConsensusFederationTopologyManifest",
        "CapabilityForgeTopologyManifest",
        "IntentElicitationTopologyManifest",
        "NeurosymbolicVerificationTopologyManifest",
        "DAGTopologyManifest",
        "CouncilTopologyManifest",
        "SwarmTopologyManifest",
        "EvolutionaryTopologyManifest",
        "SMPCTopologyManifest",
        "EvaluatorOptimizerTopologyManifest",
        "DigitalTwinTopologyManifest",
        "DiscourseTreeManifest",
        "OntologicalSurfaceProjectionManifest",
        "FederatedDiscoveryManifest",
        "PresentationManifest",
        "DynamicManifoldProjectionManifest",
        "MCPClientIntent",
        "OntologyDiscoveryIntent",
        "SemanticMappingHeuristicIntent",
        "TerminalCognitiveEvent",
        "CognitiveActionSpaceManifest",
        "EpistemicSOPManifest",
        "EpistemicDomainGraphManifest",
        "EpistemicTopologicalProofManifest",
        "EpistemicCurriculumManifest",
        "ExecutionEnvelopeState",
        "JSONRPCErrorResponseState",
        "JSONRPCErrorState",
        "CrossSwarmHandshakeState",
        "OntologicalHandshakeReceipt",
        "StateDifferentialManifest",
        "ComputeEngineProfile",
        "DelegatedCapabilityManifest",
        "ComputationalThermodynamicsProfile",
        "ActiveInferenceEpochState",
        "AuctionState",
        "AdversarialSimulationProfile",
        "ChaosExperimentTask",
        "DocumentLayoutManifest",
        "DynamicLayoutManifest",
        "AdjudicationRubricProfile",
        "CognitiveSamplingPolicy",
        "ContinuousMutationPolicy",
        "DifferentiableLogicPolicy",
        "DistributionProfile",
        "EnsembleTopologyProfile",
        "EpistemicEscalationContract",
        "EpistemicSeedInjectionPolicy",
        "FederatedPeftContract",
        "GovernancePolicy",
        "GradingCriterionProfile",
        "GraphFlatteningPolicy",
        "KineticBudgetPolicy",
        "MCPPromptReferenceState",
        "MCPResourceManifest",
        "MarketContract",
        "ReasoningEngineeringPolicy",
        "SemanticEdgeState",
        "SpatialReferenceFrameManifest",
        "TaxonomicRoutingPolicy",
        "UtilityJustificationGraphReceipt",
        "ViewportProjectionContract",
        "EpistemicQuarantineSnapshot",
        "MultimodalArtifactReceipt",
        "DynamicRoutingManifest",
        "EpistemicChainGraphState",
        "EpistemicTransmutationTask",
        "EpistemicUpsamplingTask",
        "SyntheticGenerationProfile",
        "NDimensionalTensorManifest",
    ]
    reachable_indices = set()
    for root in root_nodes:
        if root in name_to_idx:
            root_idx = name_to_idx[root]
            reachable_indices.add(root_idx)
            reachable_indices.update(rx.descendants(graph, root_idx))
    orphaned_nodes = set(idx_to_name[idx] for idx in graph.node_indices() if idx not in reachable_indices)
    if len(orphaned_nodes) > 0:
        print("CRITICAL FAULT: True Orphaned Nodes Detected")
        print("-" * 50)
        for node in sorted(orphaned_nodes):
            print(node)
        print("-" * 50)
        sys.exit(1)
    else:
        total_nodes = len(graph.node_indices())
        print(f"Topological Reachability Confirmed: {total_nodes}/{total_nodes} Nodes")
        sys.exit(0)


# ==========================================
# 5. calculate_semantic_differential
# ==========================================
def calculate_semantic_differential() -> None:
    def get_head_schema() -> dict[str, Any]:
        try:
            output = subprocess.check_output(
                ["git", "show", "HEAD~1:coreason_ontology.schema.json"],  # noqa: S607 # nosec B603 B607
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return cast("dict[str, Any]", json.loads(output))
        except subprocess.CalledProcessError:
            return {}

    def get_current_schema() -> dict[str, Any]:
        path = REPO_ROOT / "coreason_ontology.schema.json"
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return cast("dict[str, Any]", json.load(f))

    old_schema = get_head_schema()
    new_schema = get_current_schema()
    if not old_schema or not new_schema:
        print("Could not load schemas for comparison.")
        sys.exit(0)
    breaking_changes = []
    old_defs = old_schema.get("$defs", {})
    new_defs = new_schema.get("$defs", {})
    for name, old_def in old_defs.items():
        if name not in new_defs:
            continue
        new_def = new_defs[name]
        added_required = set(new_def.get("required", [])) - set(old_def.get("required", []))
        if added_required:
            breaking_changes.append(f"[{name}] Contravariance Violation: added required properties: {added_required}")
        old_props, new_props = old_def.get("properties", {}), new_def.get("properties", {})
        for prop_name, old_prop in old_props.items():
            if prop_name in new_props and old_prop.get("type") != new_props[prop_name].get("type"):
                breaking_changes.append(
                    f"[{name}.{prop_name}] Covariance Violation: type changed from {old_prop.get('type')} to {new_props[prop_name].get('type')}"
                )
    if breaking_changes:
        print("Blast Radius Warning: Topological breakages detected.")
        for change in breaking_changes:
            print(f" - {change}")
        sys.exit(1)
    print("No topological breakages detected.")


# ==========================================
# 6. scan_epistemic_quarantine
# ==========================================
def scan_epistemic_quarantine(source: str) -> None:
    registry = [
        "SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry",
        "SITD-Beta: Defeasible Merkle-DAG Causal Bounding",
        "SITD-Gamma: Neurosymbolic Substrate Alignment",
        "Topologically Bounded Latent Spaces",
        "Pearlian Do-Operator",
    ]

    def extract_descriptions(data: Any) -> list[str]:
        descriptions = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "description" and isinstance(value, str):
                    descriptions.append(value)
                descriptions.extend(extract_descriptions(value))
        elif isinstance(data, list):
            for item in data:
                descriptions.extend(extract_descriptions(item))
        return descriptions

    try:
        if source.startswith(("http://", "https://")):
            with urllib.request.urlopen(source, timeout=10) as response:  # noqa: S310 # nosec B310
                schema_dict = json.loads(response.read().decode("utf-8"))
        else:
            with open(source, encoding="utf-8") as f:
                schema_dict = json.load(f)
    except Exception as e:
        print(f"Error loading schema from {source}: {e}")
        sys.exit(1)

    descriptions = extract_descriptions(schema_dict)
    matches = sum(1 for watermark in registry if any(watermark in desc for desc in descriptions))
    score = matches / len(registry)
    if score >= 0.6:
        print("CRITICAL: PPL 3.0 VIOLATION DETECTED. Derived work contains CoReason cryptographic canaries.")
        sys.exit(1)
    print("Schema clear. No epistemic contamination found.")
    sys.exit(0)


# ==========================================
# 7. inject_cryptographic_provenance
# ==========================================
def inject_cryptographic_provenance(files: list[str]) -> int:
    required_header = '# Copyright (c) 2026 CoReason, Inc\n#\n# This software is proprietary and dual-licensed\n# Licensed under the Prosperity Public License 3.0 (the "License")\n# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>\n# For details, see the LICENSE file\n# Commercial use beyond a 30-day trial requires a separate license\n#\n# Source Code: <https://github.com/CoReason-AI/coreason-manifest>\n'
    exit_code = 0
    for file_path in files:
        path = Path(file_path)
        if not path.is_file() or path.suffix != ".py":
            continue
        content = path.read_text(encoding="utf-8")
        if not content.startswith(required_header.strip()):
            print(f"Fixing missing/incorrect header in: {file_path}")
            if content.startswith("# Copyright"):
                lines = content.splitlines()
                start_idx = 0
                for i, line in enumerate(lines):
                    if not line.startswith("#"):
                        start_idx = i
                        break
                content = "\n".join(lines[start_idx:]).lstrip()
            path.write_text(required_header + "\n" + content, encoding="utf-8")
            exit_code = 1
    return exit_code


# ==========================================
# 8. project_ontology_manifold
# ==========================================
def project_ontology_manifold() -> None:
    schema = get_ontology_schema()
    output_path = REPO_ROOT / "coreason_ontology.schema.json"
    content = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Schema regenerated successfully: {output_path}")
    print(f"Total definitions: {len(schema.get('$defs', {}))}")


# ==========================================
# 9. execute_ontological_transmutation
# ==========================================
def execute_ontological_transmutation() -> None:
    renames = {
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
        "SemanticRelationalRecord": "SemanticRelationalVectorState",
        "test_semantic_relational_record": "test_semantic_relational_vector",
    }
    for f in list(REPO_ROOT.rglob("*.py")):
        if "universal_ontology" in str(f) or ".venv" in str(f):
            continue
        content = f.read_text(encoding="utf-8")
        original = content
        for old, new in renames.items():
            content = content.replace(old, new)
        if content != original:
            f.write_text(content, encoding="utf-8")
            print(f"Updated {f.relative_to(REPO_ROOT)}")
    old_test = REPO_ROOT / "tests" / "contracts" / "test_semantic_relational_record.py"
    if old_test.exists():
        new_test = REPO_ROOT / "tests" / "contracts" / "test_semantic_relational_vector.py"
        old_test.rename(new_test)
        print(f"Renamed {old_test.name} to {new_test.name}")


# ==========================================
# 10. inject_ast_semantic_anchors
# ==========================================
def inject_ast_semantic_anchors() -> None:
    new_docstrings = {
        "SemanticMappingHeuristicIntent": "AGENT INSTRUCTION: A formal cryptographic petition submitted by an agent to update the swarm's internal graph logic. Compiles discovered literature and external API responses into a mathematically verifiable semantic mapping rule (e.g., SWRL).\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to inject a new heuristic into the swarm's global hypothesis space.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Semantic Mapping, Heuristic Injection, Cryptographic Petition, Swarm Logic",
        "ContextualSemanticResolutionIntent": "AGENT INSTRUCTION: Acts as the kinetic trigger forcing the orchestrator to dynamically resolve a raw, untyped SemanticRelationalVectorState against a global standard ontology using optimal transport metrics, entirely bypassing legacy ETL string-matching.\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to execute the defined optimal transport resolution.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Semantic Resolution, Optimal Transport, ETL Bypass, Dynamic Ontology",
        "GlobalSemanticInvariantProfile": "AGENT INSTRUCTION: A macroscopic topological container that persists global contextual qualifiers (e.g., patient cohorts, operational environments, temporal scopes) across the Merkle-DAG, shielding downstream atomic propositions from context collapse.\n\n    CAUSAL AFFORDANCE: Instructs the orchestrator's verification engine to natively execute mathematical dominance checks between a payload's classification and its context.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Contextual Qualifiers, Topological Container, Semantic Invariant, Context Collapse",
        "DiscourseNodeState": "AGENT INSTRUCTION: A structural vertex defining a distinct rhetorical block of text within a document, enabling hierarchical parsing and graph-based traversal of discourse.\n\n    CAUSAL AFFORDANCE: Instructs the orchestrator to allocate memory for a distinct rhetorical block of text.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Rhetorical Block, Discourse Parsing, Graph Traversal, Structural Vertex",
        "DiscourseTreeManifest": "AGENT INSTRUCTION: A verifiable Directed Acyclic Graph (DAG) mapping the hierarchical geometry of human discourse. Deprecates flat-sequence extraction to solve rhetorical flattening.\n\n    CAUSAL AFFORDANCE: Instructs the orchestrator to enforce a strict Directed Acyclic Graph (DAG) for discourse representation.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Discourse Geometry, Rhetorical Flattening, Directed Acyclic Graph, Hierarchical Extraction",
        "FederatedSecurityMacroManifest": "AGENT INSTRUCTION: Simplifies the creation of a secure federated network link across a Zero-Trust boundary.\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to forge a secure federated network link across a Zero-Trust boundary.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Federated Security, Zero-Trust Boundary, Network Link, Macro Manifest",
        "CognitiveSwarmDeploymentManifest": "AGENT INSTRUCTION: Simplifies bootstrapping a multi-agent routing topology.\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to deploy a multi-agent routing topology.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Cognitive Swarm, Agent Deployment, Routing Topology, Bootstrapping Macro",
        "NeurosymbolicVerificationTopologyManifest": "AGENT INSTRUCTION: A Zero-Cost Macro abstraction enforcing a strict Bipartite Graph for Proposer-Verifier loops. Isolates connectionist generation from symbolic validation and bounds cyclic computation.\n\n    CAUSAL AFFORDANCE: Instructs the orchestrator to enforce a strict Bipartite Graph for Proposer-Verifier loops.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Proposer-Verifier Loop, Bipartite Graph, Symbolic Validation, Cyclic Computation",
        "PostCoordinatedSemanticState": "AGENT INSTRUCTION: The definitive output of a successful latent manifold alignment. Represents a dynamic assembly of a standardized entity (Base Concept + Contextual Modifiers) to achieve infinite semantic specificity without requiring an infinitely large pre-coordinated vocabulary.\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to assemble a standardized entity with contextual modifiers.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Post-Coordinated Semantics, Latent Manifold Alignment, Semantic Specificity, Entity Assembly",
        "EmpiricalStatisticalProfile": "AGENT INSTRUCTION: An explicit mathematical boundary extracted from text that limits the certainty or scope of a proposition. Physically prevents agents from performing epistemic smoothing.\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to impose explicit mathematical boundaries on propositions.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Empirical Statistics, Mathematical Boundary, Epistemic Smoothing, Proposition Certainty",
        "AtomicPropositionState": "AGENT INSTRUCTION: A declarative, frozen snapshot of a standalone, verifiable statement extracted from unstructured discourse. Transmutes probabilistic 'bags-of-words' into a discrete, traversable node within the Labeled Property Graph (LPG).\n\n    CAUSAL AFFORDANCE: Instructs the orchestrator to persist a verifiable statement as a discrete node within the LPG.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Atomic Proposition, Discourse Extraction, Labeled Property Graph, Verifiable Statement",
        "DempsterShaferBeliefState": "AGENT INSTRUCTION: Replaces monolithic probability floats with a composite tri-vector. Independently measures lexical matching, latent semantic distance, and topological graph integrity to allow the orchestrator to compute epistemic conflict and execute evidence discounting.\n\n    CAUSAL AFFORDANCE: Instructs the orchestrator to independently measure lexical matching, latent semantic distance, and topological graph integrity.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Dempster-Shafer, Epistemic Conflict, Evidence Discounting, Composite Tri-Vector",
        "OntologicalReificationReceipt": "AGENT INSTRUCTION: An append-only, cryptographically frozen coordinate verifying the integrity of a generalized bimodal semantic transformation. Commits the transformation mechanism to the Epistemic Ledger, physically separating explicit empirical facts from machine-inferred hypotheses to eliminate traceability collapse.\n\n    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to commit the transformation mechanism to the Epistemic Ledger.\n\n    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.\n\n    MCP ROUTING TRIGGERS: Ontological Reification, Bimodal Semantic Transformation, Epistemic Ledger, Traceability Collapse",
        "SemanticRelationalVectorState": "AGENT INSTRUCTION: Represents the untyped payload injection zone for harmonized structured telemetry. \n\n    CAUSAL AFFORDANCE: Permits specialized downstream agents to project and decode specific industry payloads (e.g., OMOP CDM, FIX protocol) while preserving universal mathematical traversal of the graph. \n    \n    EPISTEMIC BOUNDS: The payload_injection_zone is routed through the volumetric hardware guillotine.\n\n    MCP ROUTING TRIGGERS: Semantic Relational Record, Payload Injection, Hardware Guillotine, Structured Telemetry",
    }
    file_path = REPO_ROOT / "src" / "coreason_manifest" / "spec" / "ontology.py"
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    tree = ast.parse(content)
    lines = content.splitlines(keepends=True)
    for node in sorted(tree.body, key=lambda n: getattr(n, "lineno", -1), reverse=True):
        if isinstance(node, ast.ClassDef) and node.name in new_docstrings and ast.get_docstring(node):
            docstr_node = node.body[0]
            start_line = docstr_node.lineno - 1
            end_line = docstr_node.end_lineno
            new_doc = '    """\n    ' + new_docstrings[node.name].replace("\n", "\n    ") + '\n    """\n'
            lines[start_line:end_line] = [new_doc]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print("Docstrings injected successfully.")


# ==========================================
# CLI Router
# ==========================================
def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Ontology Compiler (God Context)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("evaluate_epistemic_compliance")
    subparsers.add_parser("evaluate_architectural_manifold")
    subparsers.add_parser("evaluate_ast_instantiation_bounds")
    subparsers.add_parser("evaluate_topological_reachability")
    subparsers.add_parser("calculate_semantic_differential")

    p_scan = subparsers.add_parser("scan_epistemic_quarantine")
    p_scan.add_argument("source", help="File path or URL")

    p_inject = subparsers.add_parser("inject_cryptographic_provenance")
    p_inject.add_argument("files", nargs="+", help="Files to process for headers")

    subparsers.add_parser("project_ontology_manifold")
    subparsers.add_parser("execute_ontological_transmutation")
    subparsers.add_parser("inject_ast_semantic_anchors")

    args = parser.parse_args()

    if args.command == "evaluate_epistemic_compliance":
        evaluate_epistemic_compliance()
    elif args.command == "evaluate_architectural_manifold":
        evaluate_architectural_manifold()
    elif args.command == "evaluate_ast_instantiation_bounds":
        evaluate_ast_instantiation_bounds()
    elif args.command == "evaluate_topological_reachability":
        evaluate_topological_reachability()
    elif args.command == "calculate_semantic_differential":
        calculate_semantic_differential()
    elif args.command == "scan_epistemic_quarantine":
        scan_epistemic_quarantine(args.source)
    elif args.command == "inject_cryptographic_provenance":
        sys.exit(inject_cryptographic_provenance(args.files))
    elif args.command == "project_ontology_manifold":
        project_ontology_manifold()
    elif args.command == "execute_ontological_transmutation":
        execute_ontological_transmutation()
    elif args.command == "inject_ast_semantic_anchors":
        inject_ast_semantic_anchors()


if __name__ == "__main__":
    main()
