with open("tests/test_hash_invariance.py") as f:
    content = f.read()

target = """    intent1 = DraftingIntent(
        context_prompt="prompt",
        resolution_schema={},
        timeout_action="rollback"
    )
    intent1.artifact_cid = "art1"

    intent2 = DraftingIntent(
        context_prompt="prompt",
        resolution_schema={},
        timeout_action="rollback"
    )
    intent2.artifact_cid = "art2\""""

repl = """    intent1 = DraftingIntent(
        context_prompt="prompt",
        resolution_schema={},
        timeout_action="rollback"
    )
    object.__setattr__(intent1, "artifact_cid", "art1")

    intent2 = DraftingIntent(
        context_prompt="prompt",
        resolution_schema={},
        timeout_action="rollback"
    )
    object.__setattr__(intent2, "artifact_cid", "art2")"""

content = content.replace(target, repl)

with open("tests/test_hash_invariance.py", "w") as f:
    f.write(content)
