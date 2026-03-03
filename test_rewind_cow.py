from coreason_manifest.core.state.state_rewind import apply_rewind, _get_cow_parent
from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp

state = {"a": {"b": [1, 2, 3]}, "c": "test"}
patch = JSONPatchOperation(op=PatchOp.ADD, path="/a/b/-", value=4)
new_state = apply_rewind(state, [patch])

print("Testing sibling immutability:")
assert id(state["c"]) == id(new_state["c"]), "Sibling C was deepcopied!"

print("Testing parent variation:")
assert id(state["a"]["b"]) != id(new_state["a"]["b"]), "Node B was not CoW'd!"
assert id(state["a"]) != id(new_state["a"]), "Node A was not CoW'd!"
assert id(state) != id(new_state), "Root was not CoW'd!"

print("Success! Tests completely pass CoW logic checks!")
