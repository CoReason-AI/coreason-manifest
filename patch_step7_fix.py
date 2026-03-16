with open("src/coreason_manifest/__init__.py", "r") as f:
    content = f.read()

exports = [
    '"MemoryHeapSnapshot",',
    '"NetworkInterceptState",',
    '"SchemaInferenceIntent",'
]

lines = content.split('\n')
all_idx = lines.index('__all__ = [')
end_idx = lines.index(']', all_idx)

current_exports = [line.strip() for line in lines[all_idx+1:end_idx]]
for exp in exports:
    if exp not in current_exports:
        current_exports.append(exp)

current_exports.sort()

new_lines = lines[:all_idx+1] + [f"    {exp}" for exp in current_exports] + lines[end_idx:]

with open("src/coreason_manifest/__init__.py", "w") as f:
    f.write('\n'.join(new_lines))
