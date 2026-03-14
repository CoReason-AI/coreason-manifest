# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at [https://prosperitylicense.com/versions/3.0.0](https://prosperitylicense.com/versions/3.0.0)
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: [https://github.com/CoReason-AI/coreason-manifest](https://github.com/CoReason-AI/coreason-manifest)

import json
import sys
import urllib.request
from typing import Any

"""
AGENT INSTRUCTION: Pure Python SITD Semantic Scanner
Enforcing the 3.0 PPL No-Execution / Pure Data bounds.
"""

REGISTRY = [
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


def scan_schema(schema_dict: dict[str, Any]) -> float:
    descriptions = extract_descriptions(schema_dict)
    matches = 0
    for watermark in REGISTRY:
        for desc in descriptions:
            if watermark in desc:
                matches += 1
                break
    return matches / len(REGISTRY)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/swarm_watchdog.py <file_path_or_url>")
        sys.exit(1)

    source = sys.argv[1]

    try:
        if source.startswith(("http://", "https://")):
            with urllib.request.urlopen(source) as response:  # noqa: S310
                schema_dict = json.loads(response.read().decode("utf-8"))
        else:
            with open(source, encoding="utf-8") as f:
                schema_dict = json.load(f)
    except Exception as e:
        print(f"Error loading schema from {source}: {e}")
        sys.exit(1)

    score = scan_schema(schema_dict)

    if score >= 0.6:
        print("CRITICAL: PPL 3.0 VIOLATION DETECTED. Derived work contains CoReason cryptographic canaries.")
        sys.exit(1)
    else:
        print("Schema clear. No epistemic contamination found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
