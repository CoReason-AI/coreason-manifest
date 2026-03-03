from coreason_manifest.core.state.persistence import JSONPatchOperation, PatchOp
from coreason_manifest.core.state.state_rewind import apply_rewind, generate_inverse_patches

state = {"a": {"b": [1, 2, 3]}, "c": "test"}
patches = [
    JSONPatchOperation(op=PatchOp.ADD, path="/a/b/-", value=4),
    JSONPatchOperation(op=PatchOp.REPLACE, path="/c", value="changed"),
    JSONPatchOperation(op=PatchOp.REMOVE, path="/a/b/0", value=None),
]

# Apply patches locally (mock application)
state2 = {"a": {"b": [2, 3, 4]}, "c": "changed"}

inverses = generate_inverse_patches(state, patches)
print("INVERSES:")
for i in inverses:
    print(i.model_dump(exclude_unset=True))

rewound = apply_rewind(state2, inverses)
print("REWOUND:")
print(rewound)
print("ORIGINAL:")
print(state)
assert rewound == state, "Rewind failed to restore state!"
print("SUCCESS!")
