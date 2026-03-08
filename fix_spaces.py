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

    # We are looking for something like:
    # "some string"
    # "another string"
    # inside parentheses.
    # The regex below looks for a string literal ending in a letter/punctuation,
    # followed by optional whitespace/newlines, followed by another string literal starting with a letter.
    # We want to replace it by adding a space before the closing quote of the first string.

    # We can iteratively find all `"` followed by `\n` and spaces and `"`, and check if there's a space.
    # Actually, a simpler way is to find: ([a-zA-Z0-9_\.,\)\-])"[\s\n]*"([a-zA-Z0-9])
    # Replace with: \1 " "\2 (but keeping the newline)
    # Let's just do a controlled regex substitution:

    def add_space_if_needed(match):
        end_of_first = match.group(1)
        between = match.group(2)
        start_of_second = match.group(3)

        # If the first string doesn't end with a space, and the second doesn't start with a space, add a space.
        if not end_of_first.endswith(" ") and not start_of_second.startswith(" "):
            # add a space to the end of the first string
            return f'{end_of_first} "{between}"{start_of_second}'
        return match.group(0)

    # find: "word"\n\s*"word"
    # Group 1: anything inside the first quote
    # Group 2: the whitespace between quotes
    # Group 3: anything inside the second quote
    # Actually, just finding the boundary:
    # ([^\s\\])"(\s*\n\s*)"([^\s\\]) -> \1 "\2"\3

    new_content = re.sub(r'([^\s\\"])("[\s\n]*")([^\s\\"])', r"\1 \2\3", content)

    with open(filename, "w") as f:
        f.write(new_content)
