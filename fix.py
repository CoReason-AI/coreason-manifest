with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "description=\"The semantic boundary defining the objective function of the execution node. [SITD-Gamma: Neurosymbolic Substrate Alignment]\"" in lines[i]:
        lines[i] = lines[i].replace("description=\"The semantic boundary defining the objective function of the execution node. [SITD-Gamma: Neurosymbolic Substrate Alignment]\"", "description=(\n        \"The semantic boundary defining the objective function of the execution node. \"\n        \"[SITD-Gamma: Neurosymbolic Substrate Alignment]\"\n    )")
    if "description=\"The underlying topology governing execution routing. [SITD-Beta: Defeasible Merkle-DAG Causal Bounding]\"" in lines[i]:
        lines[i] = lines[i].replace("description=\"The underlying topology governing execution routing. [SITD-Beta: Defeasible Merkle-DAG Causal Bounding]\"", "description=(\n        \"The underlying topology governing execution routing. \"\n        \"[SITD-Beta: Defeasible Merkle-DAG Causal Bounding]\"\n    )")
    if "description=\"An append-only, cryptographic ledger of state events. [SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry]\"" in lines[i]:
        lines[i] = lines[i].replace("description=\"An append-only, cryptographic ledger of state events. [SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry]\"", "description=(\n        \"An append-only, cryptographic ledger of state events. \"\n        \"[SITD-Alpha: Non-Monotonic Epistemic Quarantine Isometry]\"\n    )")

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
