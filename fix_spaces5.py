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

    lines = content.split("\n")
    for i in range(len(lines) - 1):
        line1 = lines[i]
        line2 = lines[i + 1]

        # In python multiline implicit concatenation, sometimes we have:
        # description=(
        #     "word"
        #     "word"
        # )

        # Let's see if line1 has a `"` at the end (ignoring spaces)
        # and line2 has a `"` at the beginning (ignoring spaces)

        # Regex to find if line ends with quote (but not \" and not ending with a space before quote)
        if line1.strip().endswith('"') and line2.strip().startswith('"'):
            # It's a concatenation.
            # Does the string in line1 end with space?
            # i.e., it looks like `...something "`
            # Let's extract the string content

            # line1.rstrip() ends with `"`
            # the char before `"` is line1.rstrip()[-2]
            stripped1 = line1.rstrip()
            stripped2 = line2.lstrip()

            if len(stripped1) > 1 and stripped1[-1] == '"' and stripped1[-2] != " " and stripped1[-2] != '"':
                # The first string doesn't end with a space
                # Does the second string start with a space?
                if len(stripped2) > 1 and stripped2[0] == '"' and stripped2[1] != " " and stripped2[1] != '"':
                    # Neither has a space! Let's inject one.
                    # We will replace the last `"` in line1 with ` "`

                    # Be careful not to mess up anything else, just add a space before the last `"`
                    idx = line1.rfind('"')
                    if idx != -1:
                        lines[i] = line1[:idx] + " " + line1[idx:]

    new_content = "\n".join(lines)

    with open(filename, "w") as f:
        f.write(new_content)
