with open("scripts/generate_cross_language_bindings.py", "r") as f:
    content = f.read()

content = content.replace("import argparse\n", "")

with open("scripts/generate_cross_language_bindings.py", "w") as f:
    f.write(content)
