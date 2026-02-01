import unittest
from datetime import datetime
from uuid import uuid4

from coreason_manifest.definitions.audit import (
    CognitiveStep,
    GenAIOperation,
    GenAITokenUsage,
    ReasoningTrace,
)
from coreason_manifest.definitions.message import (
    ChatMessage,
    Role,
    TextPart,
    ToolCallRequestPart,
    ToolCallResponsePart,
)


class TestGapAnalysisFeatures(unittest.TestCase):
    def test_tool_call_arguments(self) -> None:
        # Test Dict arguments
        part1 = ToolCallRequestPart(name="test", arguments={"a": 1})
        self.assertEqual(part1.parsed_arguments, {"a": 1})

        # Test String arguments
        part2 = ToolCallRequestPart(name="test", arguments='{"b": 2}')
        self.assertEqual(part2.parsed_arguments, {"b": 2})

        # Test Invalid String
        part3 = ToolCallRequestPart(name="test", arguments="invalid")
        self.assertEqual(part3.parsed_arguments, {})

    def test_message_factories(self) -> None:
        # User
        user_msg = ChatMessage.user("Hello")
        self.assertEqual(user_msg.role, Role.USER)
        self.assertEqual(len(user_msg.parts), 1)
        part0 = user_msg.parts[0]
        self.assertIsInstance(part0, TextPart)
        self.assertEqual(part0.content, "Hello")

        # Assistant
        asst_msg = ChatMessage.assistant("Hi there")
        self.assertEqual(asst_msg.role, Role.ASSISTANT)
        self.assertEqual(len(asst_msg.parts), 1)
        part_asst = asst_msg.parts[0]
        self.assertIsInstance(part_asst, TextPart)
        self.assertEqual(part_asst.content, "Hi there")

        # Tool
        tool_msg = ChatMessage.tool("call_123", {"result": "success"})
        self.assertEqual(tool_msg.role, Role.TOOL)
        self.assertEqual(len(tool_msg.parts), 1)
        part_tool = tool_msg.parts[0]
        self.assertIsInstance(part_tool, ToolCallResponsePart)
        self.assertEqual(part_tool.id, "call_123")
        self.assertEqual(part_tool.response, {"result": "success"})

    def test_token_usage_arithmetic(self) -> None:
        t1 = GenAITokenUsage(
            input=10, output=20, total=30, prompt_tokens=10, completion_tokens=20, total_tokens=30, details={"a": 1}
        )
        t2 = GenAITokenUsage(
            input=5, output=5, total=10, prompt_tokens=5, completion_tokens=5, total_tokens=10, details={"b": 2}
        )

        # Test __add__
        t3 = t1 + t2
        self.assertEqual(t3.input, 15)
        self.assertEqual(t3.output, 25)
        self.assertEqual(t3.total, 40)
        self.assertEqual(t3.prompt_tokens, 15)
        self.assertEqual(t3.completion_tokens, 25)
        self.assertEqual(t3.total_tokens, 40)
        self.assertEqual(t3.details, {"a": 1, "b": 2})

        # Test __iadd__
        t1 += t2
        self.assertEqual(t1.input, 15)
        self.assertEqual(t1.output, 25)
        self.assertEqual(t1.total, 40)
        self.assertEqual(t1.details, {"a": 1, "b": 2})

    def test_genai_operation_factory(self) -> None:
        # Test CognitiveStep.thought() which is alias for GenAIOperation.thought()
        step = CognitiveStep.thought("Thinking process...")

        self.assertIsInstance(step, GenAIOperation)
        self.assertEqual(step.operation_name, "thought")
        self.assertEqual(step.provider, "internal")
        self.assertEqual(step.model, "internal")
        self.assertIsNotNone(step.span_id)
        self.assertIsNotNone(step.trace_id)

        self.assertEqual(len(step.output_messages), 1)
        msg = step.output_messages[0]
        self.assertEqual(msg.role, Role.ASSISTANT)
        part = msg.parts[0]
        self.assertIsInstance(part, TextPart)
        self.assertEqual(part.content, "Thinking process...")

        # Test with overrides
        custom_trace = str(uuid4())
        step2 = GenAIOperation.thought("More thinking", trace_id=custom_trace, model="gpt-4")
        self.assertEqual(step2.trace_id, custom_trace)
        self.assertEqual(step2.model, "gpt-4")
        part2 = step2.output_messages[0].parts[0]
        self.assertIsInstance(part2, TextPart)
        self.assertEqual(part2.content, "More thinking")

        # Test output_messages collision avoidance
        # If output_messages passed in kwargs, it should be ignored or overridden
        step3 = GenAIOperation.thought("Thinking", output_messages=[])
        # Should still have the assistant message
        self.assertEqual(len(step3.output_messages), 1)
        part3 = step3.output_messages[0].parts[0]
        self.assertIsInstance(part3, TextPart)
        self.assertEqual(part3.content, "Thinking")

    def test_reasoning_trace_metadata(self) -> None:
        trace = ReasoningTrace(
            trace_id=str(uuid4()),
            agent_id="test-agent",
            start_time=datetime.now(),
            metadata={"execution_path": ["node1", "node2"]},
        )
        self.assertEqual(trace.metadata["execution_path"], ["node1", "node2"])


if __name__ == "__main__":
    unittest.main()
