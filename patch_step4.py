with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

target = """type AnyIntent = Annotated[
    InformationalIntent
    | DraftingIntent
    | AdjudicationIntent
    | EscalationIntent
    | SemanticDiscoveryIntent
    | TaxonomicRestructureIntent
    | LatentProjectionIntent
    | ProgramSynthesisIntent
    | QueryDecompositionManifest,"""

replacement = """type AnyIntent = Annotated[
    InformationalIntent
    | DraftingIntent
    | AdjudicationIntent
    | EscalationIntent
    | SemanticDiscoveryIntent
    | TaxonomicRestructureIntent
    | LatentProjectionIntent
    | ProgramSynthesisIntent
    | QueryDecompositionManifest
    | SchemaInferenceIntent,"""

if target in content:
    content = content.replace(target, replacement)
    with open("src/coreason_manifest/spec/ontology.py", "w") as f:
        f.write(content)
    print("Patched AnyIntent")
else:
    print("Target AnyIntent not found")
