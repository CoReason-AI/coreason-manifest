import os

test_files = [
    "tests/contracts/test_curriculum_synthesis.py",
    "tests/contracts/test_epistemic_distillation.py",
    "tests/contracts/test_implicit_reward_rl.py"
]

for file in test_files:
    if os.path.exists(file):
        with open(file, "r") as f:
            content = f.read()

        # We need to pass the context since "ext:..." is not allowed unless passed in context
        # Alternatively, we can just use valid OBO relation edges like "is_a"
        content = content.replace('directed_edge_type="ext:causes"', 'directed_edge_type="is_a"')
        content = content.replace('directed_edge_type="ext:type1"', 'directed_edge_type="part_of"')
        content = content.replace('directed_edge_type="ext:type2"', 'directed_edge_type="has_part"')
        content = content.replace('directed_edge_type="ext:type3"', 'directed_edge_type="is_a"')

        with open(file, "w") as f:
            f.write(content)
        print(f"Patched {file}")
