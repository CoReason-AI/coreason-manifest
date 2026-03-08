import sys
import re
import textwrap

files = [
    "src/coreason_manifest/state/argumentation.py",
    "src/coreason_manifest/state/differentials.py",
    "src/coreason_manifest/state/scratchpad.py",
    "src/coreason_manifest/state/semantic.py",
]

for filename in files:
    with open(filename, "r") as f:
        lines = f.readlines()

    out_lines = []
    for line in lines:
        if len(line) > 120 and 'description="' in line:
            match = re.search(r'description="([^"]+)"', line)
            if match:
                desc = match.group(1)
                wrapped = textwrap.wrap(desc, width=80)

                indent_match = re.match(r"^\s*", line)
                indent = len(indent_match.group(0)) if indent_match else 0

                new_desc = "(\n"
                for part in wrapped:
                    new_desc += " " * (indent + 8) + f'"{part}"\n'
                new_desc += " " * (indent + 4) + ")"

                line = line.replace(f'"{desc}"', new_desc)
        out_lines.append(line)

    with open(filename, "w") as f:
        f.writelines(out_lines)
