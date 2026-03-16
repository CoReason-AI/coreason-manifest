with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

target = "type AnyToolchainState = Annotated[\n    BrowserDOMState | TerminalBufferState | ViewportRasterState,"
replacement = "type AnyToolchainState = Annotated[\n    BrowserDOMState | TerminalBufferState | ViewportRasterState | NetworkInterceptState | MemoryHeapSnapshot,"

if target in content:
    content = content.replace(target, replacement)
    with open("src/coreason_manifest/spec/ontology.py", "w") as f:
        f.write(content)
    print("Patched AnyToolchainState")
else:
    print("Target not found")
