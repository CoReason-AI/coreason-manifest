import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

# Fields to inline
fields = """    event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern="^[a-zA-Z0-9_.:-]+$",
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark binding this node to the Merkle-DAG.",
    )
    prior_event_hash: str | None = Field(
        default=None,
        pattern="^[a-f0-9]{64}$",
        min_length=1,
        max_length=128,
        description="The SHA-256 hash of the temporally preceding event, establishing the Merkle-DAG chain.",
    )
    timestamp: float = Field(
        ge=0.0,
        le=253402300799.0,
        description="Causal Ancestry markers required to resolve decentralized event ordering.",
    )\n"""

# Children of BaseStateEvent:
# SystemFaultEvent
# CausalExplanationEvent
# CounterfactualRegretEvent
# BargeInInterruptEvent
# EpistemicPromotionEvent
# BudgetExhaustionEvent
# TokenBurnReceipt
# NormativeDriftEvent
# PersistenceCommitReceipt
# HypothesisGenerationEvent
# ToolInvocationEvent
# BeliefMutationEvent
# ObservationEvent
# EpistemicTelemetryEvent
# CognitivePredictionReceipt
# IntentClassificationReceipt
# EpistemicAxiomVerificationReceipt
# CognitiveRewardEvaluationReceipt
# EpistemicFlowStateReceipt

children = [
    'SystemFaultEvent', 'CausalExplanationEvent', 'CounterfactualRegretEvent',
    'BargeInInterruptEvent', 'EpistemicPromotionEvent', 'BudgetExhaustionEvent',
    'TokenBurnReceipt', 'NormativeDriftEvent', 'PersistenceCommitReceipt',
    'HypothesisGenerationEvent', 'ToolInvocationEvent', 'BeliefMutationEvent',
    'ObservationEvent', 'EpistemicTelemetryEvent', 'CognitivePredictionReceipt',
    'IntentClassificationReceipt', 'EpistemicAxiomVerificationReceipt',
    'CognitiveRewardEvaluationReceipt', 'EpistemicFlowStateReceipt'
]

for child in children:
    # Find `class Child(BaseStateEvent):` and replace with `class Child(CoreasonBaseState):`
    # Then insert fields right after the docstring or class def.

    # regex to find class and docstring
    pattern = r'(class ' + child + r'\(BaseStateEvent\):(?:\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\'))?)'

    def repl(m):
        base = m.group(1).replace('BaseStateEvent', 'CoreasonBaseState')
        return base + '\n\n' + fields

    content = re.sub(pattern, repl, content)

# Remove BaseStateEvent definition completely
base_pattern = r'class BaseStateEvent\(CoreasonBaseState\):\s*(?:r?"""[\s\S]*?"""|r?\'\'\'[\s\S]*?\'\'\')?[\s\S]*?timestamp: float = Field\([\s\S]*?description="Causal Ancestry markers required to resolve decentralized event ordering\.",\s*\)\n'
content = re.sub(base_pattern, '', content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
