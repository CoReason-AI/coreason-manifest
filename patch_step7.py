with open("src/coreason_manifest/__init__.py", "r") as f:
    content = f.read()

exports = [
    '"MemoryHeapSnapshot"',
    '"NetworkInterceptState"',
    '"SchemaInferenceIntent"'
]

for exp in exports:
    if exp not in content:
        # Simple string manipulation to add in alphabetical order.
        lines = content.split('\n')
        all_start = -1
        all_end = -1
        for i, line in enumerate(lines):
            if '__all__ = [' in line:
                all_start = i
            if all_start != -1 and ']' in line:
                all_end = i
                break

        all_lines = lines[all_start+1:all_end]
        all_lines.append(f"    {exp},")
        all_lines.sort()

        # Replace the __all__ block
        content = '\n'.join(lines[:all_start+1] + all_lines + lines[all_end:])

with open("src/coreason_manifest/__init__.py", "w") as f:
    f.write(content)
print("Updated __init__.py")
