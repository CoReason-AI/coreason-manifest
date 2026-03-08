import re

files = [
    "src/coreason_manifest/state/semantic.py",
    "src/coreason_manifest/state/differentials.py",
    "src/coreason_manifest/state/scratchpad.py",
    "src/coreason_manifest/state/argumentation.py",
]

for filename in files:
    with open(filename, "r") as f:
        content = f.read()

    # Maybe the quotes are part of the groups?
    # Let's just write a python script that parses through strings.
    # For now, let's just find `"\n` and look around it.

    lines = content.split("\n")
    for i in range(len(lines) - 1):
        line1 = lines[i]
        line2 = lines[i + 1]

        # Check if line1 ends with `"`, optionally followed by `,` or `)` (no, because it's a multiline string, so it just ends with `"`)
        match1 = re.search(r'([^\s])"\s*$', line1)
        match2 = re.search(r'^\s*"([^\s])', line2)

        if match1 and match2:
            # We found a string ending without a space, and the next line starting without a space!
            # e.g., `    "word"` and `    "word"`

            # Add a space before the ending quote of line1
            line1 = re.sub(r'([^\s])"\s*$', r'\1 "', line1)
            lines[i] = line1

    new_content = "\n".join(lines)

    with open(filename, "w") as f:
        f.write(new_content)
