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

    # The previous regex was: r'([^\s])"(\s*\n\s*)"([^\s])'
    # Actually, we want to match:
    # A character that is not a space or quote: ([^\s"])
    # The end quote: "
    # Some whitespace including newline: (\s*\n\s*)
    # The start quote: "
    # A character that is not a space or quote: ([^\s"])

    # We want to replace it with:
    # \1 "\2"\3

    new_content = re.sub(r'([^\s"])("\s*\n\s*")([^\s"])', r"\1 \2\3", content)

    with open(filename, "w") as f:
        f.write(new_content)
