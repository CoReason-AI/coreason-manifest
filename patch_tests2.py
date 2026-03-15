import os

test_files = [
    "tests/contracts/test_epistemic_distillation.py",
    "tests/contracts/test_implicit_reward_rl.py"
]

for file in test_files:
    if os.path.exists(file):
        with open(file, "r") as f:
            content = f.read()

        content = content.replace('directed_edge_type="part_of"', 'directed_edge_type="has_part_temp"')
        content = content.replace('directed_edge_type="has_part"', 'directed_edge_type="part_of"')
        content = content.replace('directed_edge_type="has_part_temp"', 'directed_edge_type="has_part"')

        with open(file, "w") as f:
            f.write(content)
        print(f"Patched {file}")
