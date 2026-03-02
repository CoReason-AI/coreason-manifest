with open("src/coreason_manifest/toolkit/builder.py", "r") as f:
    content = f.read()

content = content.replace("            from typing import Any\n", "")
content = content.replace("        from typing import Literal\n", "")

with open("src/coreason_manifest/toolkit/builder.py", "w") as f:
    f.write(content)
