from pathlib import Path

HEADER = """# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""

files = [
    "tests/contracts/test_empirical_statistical_qualifier.py",
    "tests/contracts/test_macros.py",
    "tests/contracts/test_rejection_receipts.py",
    "tests/contracts/test_semantic_relational_vector.py",
    "tests/fuzzing/test_active_inference_epochs.py",
    "tests/fuzzing/test_entropic_simulation.py",
    "scripts/audit_compliance.py",
    "scripts/evaluate_topological_reachability.py",
]

for f in files:
    path = Path(f)
    content = path.read_text(encoding="utf-8")
    if not content.startswith("# Copyright"):
        path.write_text(HEADER + content, encoding="utf-8")
