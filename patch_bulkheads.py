import re

def patch_file(filepath, pattern, replacement):
    with open(filepath, "r") as f:
        content = f.read()
    content = re.sub(pattern, replacement, content)
    with open(filepath, "w") as f:
        f.write(content)

# memory.py -> EpistemicLedger.history
patch_file(
    "src/coreason_manifest/state/memory.py",
    r"history: list\[AnyStateEvent\] = Field\(description=\"An append-only, cryptographic ledger of state events\.\"\)",
    "history: list[AnyStateEvent] = Field(max_length=10000, description=\"An append-only, cryptographic ledger of state events.\")"
)

# argumentation.py -> ArgumentGraph.claims, attacks
patch_file(
    "src/coreason_manifest/state/argumentation.py",
    r"claims: dict\[str, ArgumentClaim\] = Field\(description=\"A registry of all active claims, keyed by claim_id\.\"\)",
    "claims: dict[str, ArgumentClaim] = Field(max_length=10000, description=\"A registry of all active claims, keyed by claim_id.\")"
)

patch_file(
    "src/coreason_manifest/state/argumentation.py",
    r"attacks: dict\[str, DefeasibleAttack\] = Field\(\n        default_factory=dict, description=\"A registry of all directed attack edges, keyed by attack_id\.\"\n    \)",
    "attacks: dict[str, DefeasibleAttack] = Field(\n        default_factory=dict, max_length=10000, description=\"A registry of all directed attack edges, keyed by attack_id.\"\n    )"
)

patch_file(
    "src/coreason_manifest/state/argumentation.py",
    r"text_chunk: str = Field\(description=\"The natural language representation of the proposition\.\"\)",
    "text_chunk: str = Field(max_length=50000, description=\"The natural language representation of the proposition.\")"
)

# schemas.py -> ExecutionSpan.events
patch_file(
    "src/coreason_manifest/telemetry/schemas.py",
    r"events: list\[SpanEvent\] = Field\(default_factory=list, description=\"Structured log records emitted during the span\.\"\)",
    "events: list[SpanEvent] = Field(default_factory=list, max_length=5000, description=\"Structured log records emitted during the span.\")"
)

# scivis.py -> InsightCard.markdown_content
patch_file(
    "src/coreason_manifest/presentation/scivis.py",
    r"markdown_content: str = Field\(description=\"The semantic text summary written in Markdown\.\"\)",
    "markdown_content: str = Field(max_length=50000, description=\"The semantic text summary written in Markdown.\")"
)

# semantic.py -> SemanticNode.text_chunk
patch_file(
    "src/coreason_manifest/state/semantic.py",
    r"text_chunk: str = Field\(description=\"The raw natural language representation of the memory\.\"\)",
    "text_chunk: str = Field(max_length=50000, description=\"The raw natural language representation of the memory.\")"
)
