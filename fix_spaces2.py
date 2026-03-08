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

    # To be safer, let's find all pairs of string literals that are concatenated
    # e.g., "word"\n    "word"
    # match 1: non-space character inside quote: (\w|[.,!?;:\)\]\}])
    # match 2: quote, spaces/newlines, quote: ("[\s\n]+")(")(?=\w|[.,!?;:\[\{\(])
    # Let's write a simpler regex:
    # match any string that ends with a non-space char, has the quote closed, then spaces, then quote opened, then non-space char

    new_content = re.sub(r'([^\s])"(\s*\n\s*)"([^\s])', r"\1 \g<2>\3", content)

    # In my previous attempt `\1 \2\3` didn't work properly maybe because of the quote matching.
    # Let's break it down:
    # We want: r'([^\s\\])"(\s*\n\s*)"([^\s\\])'
    # The replacement should add a space before the first quote.
    # E.g. `word"\n    "word` -> `word "\n    "word`

    with open(filename, "w") as f:
        f.write(new_content)
