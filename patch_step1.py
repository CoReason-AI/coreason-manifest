with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

# Insert before AnyPresentationIntent (around line 6545)
insert_marker = "type AnyPresentationIntent = Annotated["

new_code = """class EpistemicConstraintPolicy(CoreasonBaseState):
    \"\"\"
    AGENT INSTRUCTION: A mathematical invariant evaluated against an LLM's proxy-based structural plan.

    CAUSAL AFFORDANCE: Enables SymbolicAI's Design-by-Contract (DbC) autonomous correction loop during test-time compute.

    EPISTEMIC BOUNDS: `assertion_ast` must be a strictly parsable Python AST string. It structurally prohibits imports, assignments, or kinetic network calls to guarantee safe downstream evaluation.

    MCP ROUTING TRIGGERS: Design-by-Contract, AST Evaluation, Invariant Checking, SymbolicAI DbC, Zero-Trust Execution
    \"\"\"
    assertion_ast: Annotated[str, StringConstraints(max_length=1024)] = Field(
        description="Strict AST-parsable string constraint (e.g., 'len(plan.outputs) == len(plan.inputs)')."
    )
    remediation_prompt: Annotated[str, StringConstraints(max_length=2048)] = Field(
        description="The exact semantic prompt injected into the LLM if the AST assertion collapses natively."
    )

    @field_validator("assertion_ast", mode="after")
    @classmethod
    def validate_ast_safety(cls, v: str) -> str:
        \"\"\"
        AGENT INSTRUCTION: Automata Theory bounds for AST validation.
        EPISTEMIC BOUNDS: Mechanically parses the string into a syntax tree and explicitly quarantines forbidden kinetic nodes (e.g., imports, assignments, function calls) to mathematically prevent Arbitrary Code Execution (ACE).
        \"\"\"
        try:
            tree = ast.parse(v, mode="eval")
            for node in ast.walk(tree):
                # Blacklist dangerous kinetic nodes
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete, ast.Import, ast.ImportFrom, ast.Yield, ast.YieldFrom, ast.Await, ast.Call)):
                    raise ValueError(f"Kinetic execution bleed detected: Forbidden AST node {type(node).__name__}")
        except SyntaxError as e:
            raise ValueError(f"Invalid syntax in constraint AST: {e}")
        return v


"""

content = content.replace(insert_marker, new_code + insert_marker)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
