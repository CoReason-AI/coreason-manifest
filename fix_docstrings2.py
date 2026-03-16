with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

content = content.replace(
    '"""AGENT INSTRUCTION: A deterministic physical actuator representing a headless wiretap on the browser/OS network layer\n    (e.g., CDP Network.responseReceived or eBPF socket trace)."""',
    '"""\n    AGENT INSTRUCTION: A deterministic physical actuator representing a headless wiretap\n    on the browser/OS network layer (e.g., CDP Network.responseReceived or eBPF socket trace).\n    """'
)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
