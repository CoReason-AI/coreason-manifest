with open("tests/test_hash_invariance.py", "r") as f:
    content = f.read()

target_trace = """    manifest = TraceExportManifest(
        trace_id="trace1",
        version="1.0.0",
        schema_version="1.0.0",
        execution_nodes=[node2, node1]
    )"""

repl_trace = """    manifest = TraceExportManifest(
        batch_cid="batch-123",
        execution_nodes=[node2, node1]
    )"""

target_agent = """    intent1 = DraftingIntent(
        artifact_cid="art1",
        proposed_content="draft 1"
    )
    intent2 = DraftingIntent(
        artifact_cid="art2",
        proposed_content="draft 2"
    )"""

repl_agent = """    intent1 = DraftingIntent(
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
    intent2.artifact_cid = "art2"
"""

content = content.replace(target_trace, repl_trace)
content = content.replace(target_agent, repl_agent)

with open("tests/test_hash_invariance.py", "w") as f:
    f.write(content)
