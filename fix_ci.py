with open("src/coreason_manifest/compute/stochastic.py", "r") as f:
    content = f.read()

content = content.replace(
"""        if self.confidence_interval_95 is not None:
            if self.confidence_interval_95[0] >= self.confidence_interval_95[1]:""",
"""        if self.confidence_interval_95 is not None and self.confidence_interval_95[0] >= self.confidence_interval_95[1]:"""
)

with open("src/coreason_manifest/compute/stochastic.py", "w") as f:
    f.write(content)

with open("src/coreason_manifest/state/semantic.py", "r") as f:
    content = f.read()

content = content.replace(
"""        if self.valid_from is not None and self.valid_to is not None:
            if self.valid_to < self.valid_from:""",
"""        if self.valid_from is not None and self.valid_to is not None and self.valid_to < self.valid_from:"""
)

with open("src/coreason_manifest/state/semantic.py", "w") as f:
    f.write(content)

with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

content = content.replace(
"""    if confidence_interval_95 is not None:
        if confidence_interval_95[0] >= confidence_interval_95[1]:""",
"""    if confidence_interval_95 is not None and confidence_interval_95[0] >= confidence_interval_95[1]:"""
)

import re
content = re.sub(r'def test_telemetry_routing\(payload: dict\[str, Any\]\) -> None:\n    parsed = trace_export_batch_adapter\.validate_python\(payload\)', r'def test_telemetry_routing(payload: dict[str, Any]) -> None:\n    trace_export_batch_adapter.validate_python(payload)', content)

with open("tests/test_fuzzing.py", "w") as f:
    f.write(content)
