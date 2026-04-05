import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

fields = """    epistemic_enforcement: TruthMaintenancePolicy | None = Field(
        default=None, description="Ties the topology to the Truth Maintenance layer."
    )
    lifecycle_phase: Literal["draft", "live"] = Field(
        default="live", description="The execution phase of the graph. 'draft' allows incomplete structural state."
    )
    architectural_intent: str | None = Field(
        max_length=2000, default=None, description="The AI's declarative rationale for selecting this topology."
    )
    justification: str | None = Field(
        max_length=2000,
        default=None,
        description="Cryptographic/audit justification for this topology's configuration.",
    )
    nodes: dict[NodeIdentifierState, AnyNodeProfile] = Field(description="Flat registry of all nodes in this topology.")
    shared_state_contract: StateContract | None = Field(
        default=None, description="The schema-on-write contract governing the internal state of this topology."
    )
    information_flow: InformationFlowPolicy | None = Field(
        default=None,
        description="The structural Payload Loss Prevention (PLP) contract governing all state mutations in this topology.",
    )
    observability: ObservabilityLODPolicy | None = Field(
        default=None,
        description="The dynamic Level of Detail and Spectral Coarsening physics bound to this macroscopic execution graph.",
    )\n"""

children = [
    'CouncilTopologyManifest', 'DAGTopologyManifest', 'DigitalTwinTopologyManifest',
    'EvaluatorOptimizerTopologyManifest', 'EvolutionaryTopologyManifest', 'SMPCTopologyManifest',
    'SwarmTopologyManifest', 'CapabilityForgeTopologyManifest', 'IntentElicitationTopologyManifest',
    'NeurosymbolicVerificationTopologyManifest'
]

for child in children:
    pattern = r'(class ' + child + r'\(BaseTopologyManifest\):(?:\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\'))?)'

    def repl(m):
        base = m.group(1).replace('BaseTopologyManifest', 'CoreasonBaseState')
        return base + '\n\n' + fields

    content = re.sub(pattern, repl, content)

# Remove BaseTopologyManifest definition completely
base_pattern = r'class BaseTopologyManifest\(CoreasonBaseState\):\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\')?[\s\S]*?description="The dynamic Level of Detail and Spectral Coarsening physics bound to this macroscopic execution graph\.",\s*\)\n'
content = re.sub(base_pattern, '', content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
