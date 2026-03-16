import re

with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

new_classes = """class NetworkInterceptState(CoreasonBaseState):
    \"\"\"AGENT INSTRUCTION: A deterministic physical actuator representing a headless wiretap on the browser/OS network layer (e.g., CDP Network.responseReceived or eBPF socket trace).\"\"\"

    type: Literal["network_intercept"] = Field(default="network_intercept")
    capture_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    target_url_pattern: str = Field(max_length=2000, description="The regex/glob capturing the specific API endpoint")
    protocol: Literal["http_rest", "websocket", "grpc", "graphql"] = Field(description="The network protocol wiretapped")
    raw_payload_hash: str = Field(min_length=1, max_length=128, pattern="^[a-f0-9]{64}$", description="The exact Merkle root of the intercepted byte stream")
    payload_byte_size: int = Field(le=1000000000, ge=0)


class MemoryHeapSnapshot(CoreasonBaseState):
    \"\"\"AGENT INSTRUCTION: A deterministic physical actuator representing a raw pointer read from an OS-level heap or WebAssembly linear memory matrix.\"\"\"

    type: Literal["memory_heap"] = Field(default="memory_heap")
    snapshot_id: str = Field(min_length=1, max_length=128, pattern="^[a-zA-Z0-9_.:-]+$")
    memory_address_pointer: str = Field(max_length=255, pattern="^0x[a-fA-F0-9]+$", description="The exact hex coordinate of the buffer start")
    buffer_size_bytes: int = Field(le=100000000000, gt=0)
    raw_buffer_hash: str = Field(min_length=1, max_length=128, pattern="^[a-f0-9]{64}$")
"""

target = "class TerminalBufferState(CoreasonBaseState):"
if target in content and new_classes not in content:
    content = content.replace(target, new_classes + "\n\n" + target)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
