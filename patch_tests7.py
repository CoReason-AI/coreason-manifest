with open("tests/test_hash_invariance.py") as f:
    content = f.read()

target = """    intent1 = DraftingIntent(
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
    object.__setattr__(intent2, "artifact_cid", "art2")


    agent = CognitiveAgentNodeProfile(
        description="test agent",
        hardware=SpatialHardwareProfile(),
        security=EpistemicSecurityProfile(),
        emitted_intents=[intent2, intent1]
    )
    assert agent.emitted_intents[0].artifact_cid == "art1\""""

repl = """    intent1 = DraftingIntent(
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
    assert getattr(agent.emitted_intents[0], "context_prompt", "") == "prompt1\""""

content = content.replace(target, repl)

with open("tests/test_hash_invariance.py", "w") as f:
    f.write(content)
