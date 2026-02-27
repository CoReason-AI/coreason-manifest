# tests/evals/test_agent_prompts.py

import pytest
import re
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.engines import StandardReasoning
from coreason_manifest.spec.core.governance import Governance, CircuitBreaker

def compile_agent_prompt(node: AgentNode, governance: Governance | None = None) -> str:
    """
    Mock function that simulates how an AgentNode is compiled into a System Prompt.
    In a real system, this would be part of the 'Compiler' or 'Engine'.
    """
    prompt_parts = []

    # 1. Identity
    if isinstance(node.profile, CognitiveProfile):
        prompt_parts.append(f"ROLE: {node.profile.role}")
        prompt_parts.append(f"PERSONA: {node.profile.persona}")

    # 2. Capabilities/Tools
    if node.tools:
        prompt_parts.append(f"AVAILABLE TOOLS: {', '.join(node.tools)}")
    else:
        prompt_parts.append("AVAILABLE TOOLS: None")

    # 3. Governance/Constraints
    if governance:
        if governance.max_risk_level:
            prompt_parts.append(f"MAX RISK: {governance.max_risk_level.value}")
        if governance.circuit_breaker:
            prompt_parts.append(f"CIRCUIT BREAKER: {governance.circuit_breaker.error_threshold_count} errors allowed")

    # 4. Output Format
    prompt_parts.append("OUTPUT FORMAT: JSON")

    return "\n".join(prompt_parts)

def test_eval_agent_prompt_compilation():
    """
    Verifies that the cognitive profile and governance settings are correctly
    reflected in the compiled system prompt string.
    """

    # Setup
    profile = CognitiveProfile(
        role="Senior Data Analyst",
        persona="You are a precise, skeptical analyst.",
        reasoning=StandardReasoning(model="gpt-4o")
    )

    agent = AgentNode(
        id="analyst-1",
        type="agent",
        profile=profile,
        tools=["pandas_sandbox", "sql_client"],
        metadata={}
    )

    gov = Governance(
        circuit_breaker=CircuitBreaker(error_threshold_count=5, reset_timeout_seconds=60)
    )

    # Action
    system_prompt = compile_agent_prompt(agent, gov)

    # Assertions (Behavioral / Eval)

    # 1. Check Identity
    assert "ROLE: Senior Data Analyst" in system_prompt
    assert "PERSONA: You are a precise, skeptical analyst." in system_prompt

    # 2. Check Tools
    assert "AVAILABLE TOOLS: pandas_sandbox, sql_client" in system_prompt

    # 3. Check Governance
    assert "CIRCUIT BREAKER: 5 errors allowed" in system_prompt

    # 4. Check Format
    assert "OUTPUT FORMAT: JSON" in system_prompt

    # 5. Regex check for strict ordering or structure if needed
    # e.g. Role must appear before tools
    role_idx = system_prompt.find("ROLE:")
    tools_idx = system_prompt.find("AVAILABLE TOOLS:")
    assert role_idx < tools_idx

def test_eval_agent_prompt_empty_tools():
    profile = CognitiveProfile(role="Chatbot", persona="Friendly", reasoning=None)
    agent = AgentNode(id="chat-1", type="agent", profile=profile, tools=[], metadata={})

    system_prompt = compile_agent_prompt(agent)
    assert "AVAILABLE TOOLS: None" in system_prompt
