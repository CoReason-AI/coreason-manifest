with open("src/coreason_manifest/core/base.py", "r") as f:
    content = f.read()

content = content.replace('        return h\n', '        return int(h)\n')

with open("src/coreason_manifest/core/base.py", "w") as f:
    f.write(content)
