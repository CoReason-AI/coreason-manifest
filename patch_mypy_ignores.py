with open("src/coreason_manifest/oracles/combinatorial.py") as f:
    content = f.read()

content = content.replace("import clingo\n", "import clingo  # type: ignore[import-not-found]\n")
content = content.replace("from clingo.ast import (", "from clingo.ast import (  # type: ignore[import-not-found]")
content = content.replace(
    "from clingo.control import Control", "from clingo.control import Control  # type: ignore[import-not-found]"
)
content = content.replace(
    "class AssumptionTransformer(Transformer):", "class AssumptionTransformer(Transformer):  # type: ignore[misc]"
)

with open("src/coreason_manifest/oracles/combinatorial.py", "w") as f:
    f.write(content)

with open("tests/contracts/test_mcp_adapters.py") as f:
    content = f.read()

content = content.replace("import jsonschema\n", "import jsonschema  # type: ignore[import-untyped]\n")

with open("tests/contracts/test_mcp_adapters.py", "w") as f:
    f.write(content)
