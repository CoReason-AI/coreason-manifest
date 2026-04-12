import re
with open("tests/test_hash_invariance.py", "r") as f:
    content = f.read()

# Replace the whole test function
new_func = """def test_cognitive_agent_node_profile_sort() -> None:
    intent1 = DraftingIntent(
        context_prompt="prompt1",
        resolution_schema={},
        timeout_action="rollback"
    )

    intent2 = DraftingIntent(
        context_prompt="prompt2",
        resolution_schema={},
        timeout_action="rollback"
    )

    agent = CognitiveAgentNodeProfile(
        description="test agent",
        hardware=SpatialHardwareProfile(),
        security=EpistemicSecurityProfile(),
        emitted_intents=[intent2, intent1]
    )
    assert getattr(agent.emitted_intents[0], "context_prompt", "") == "prompt1"
"""

# Regex substitute the whole function
content = re.sub(r'def test_cognitive_agent_node_profile_sort.*?assert agent.emitted_intents\[0\].artifact_cid == "art1"', new_func, content, flags=re.DOTALL)

with open("tests/test_hash_invariance.py", "w") as f:
    f.write(content)
