# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Protocol, runtime_checkable

from coreason_manifest.spec.interfaces.behavior import IAgentRuntime, IResponseHandler, IStreamEmitter


class TestBehaviorProtocols:
    def test_structural_subtyping_check(self) -> None:
        """
        Verify that a concrete class implementing `assist` and `shutdown`
        satisfies the IAgentRuntime protocol.
        """

        class MockAgent:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        assert isinstance(MockAgent(), IAgentRuntime)

    def test_missing_method_check(self) -> None:
        """
        Verify that a class missing a required method does not satisfy the protocol.
        """

        class BadAgent:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass

            # missing shutdown

        assert not isinstance(BadAgent(), IAgentRuntime)

    def test_response_handler_protocol(self) -> None:
        """
        Verify IResponseHandler protocol structure.
        """

        class MockHandler:
            async def emit_thought(self, content: str, source: str = "agent") -> None:
                pass

            async def create_text_stream(self, name: str) -> Any:
                _ = name  # suppress unused argument warning
                return None

            async def log(self, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
                pass

            async def complete(self, outputs: dict[str, Any] | None = None) -> None:
                pass

        assert isinstance(MockHandler(), IResponseHandler)

    def test_stream_emitter_protocol(self) -> None:
        """
        Verify IStreamEmitter protocol structure.
        """

        class MockEmitter:
            async def emit_chunk(self, content: str) -> None:
                pass

            async def close(self) -> None:
                pass

        assert isinstance(MockEmitter(), IStreamEmitter)

    def test_multiple_inheritance_protocol_compliance(self) -> None:
        """
        Complex Case: Verify that a class satisfies the protocol if it inherits
        implementation from multiple base classes.
        """

        class AssistBase:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass

        class ShutdownBase:
            async def shutdown(self) -> None:
                pass

        class CombinedAgent(AssistBase, ShutdownBase):
            pass

        assert isinstance(CombinedAgent(), IAgentRuntime)

    def test_mixin_usage(self) -> None:
        """
        Complex Case: Verify that using a Mixin to provide part of the implementation works.
        """

        class ShutdownMixin:
            async def shutdown(self) -> None:
                pass

        class AgentWithMixin(ShutdownMixin):
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass

        assert isinstance(AgentWithMixin(), IAgentRuntime)

    def test_runtime_checkable_with_getattr(self) -> None:
        """
        Edge Case: Verify that a class with __getattr__ does NOT satisfy the protocol
        if the methods are not explicitly defined or available in dir().
        runtime_checkable protocols usually check specifically for the presence of the method.
        """

        class DynamicAgent:
            def __getattr__(self, name: str) -> Any:
                _ = name
                return lambda *_, **__: None

        # Even though DynamicAgent().assist(...) is callable,
        # isinstance(obj, Protocol) checks for the attribute in the class/instance dict/dir.
        # It typically returns False for __getattr__ based dynamic dispatch.
        assert not isinstance(DynamicAgent(), IAgentRuntime)

    def test_protocol_extension(self) -> None:
        """
        Complex Case: Verify that we can extend the protocol and the implementation
        satisfies both the base and extended protocol.
        """

        @runtime_checkable
        class IExtendedAgentRuntime(IAgentRuntime, Protocol):
            async def specialized_task(self) -> None: ...

        class ExtendedAgent:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                pass

            async def shutdown(self) -> None:
                pass

            async def specialized_task(self) -> None:
                pass

        agent = ExtendedAgent()
        assert isinstance(agent, IAgentRuntime)
        assert isinstance(agent, IExtendedAgentRuntime)

    def test_not_implemented_error_is_still_compliant(self) -> None:
        """
        Edge Case: A class that defines the method but raises NotImplementedError
        is structurally compliant (it has the method).
        """
        class AbstractAgent:
            async def assist(self, session: Any, request: Any, handler: Any) -> None:
                raise NotImplementedError

            async def shutdown(self) -> None:
                raise NotImplementedError

        assert isinstance(AbstractAgent(), IAgentRuntime)

    def test_property_compliance(self) -> None:
        """
        Edge Case: Verify if a property counts as a method for protocol compliance.
        (Protocols usually require methods to be callables, but properties are attributes).
        However, IAgentRuntime requires `assist` to be an async method.
        A property returning a coroutine function might pass strict instance check if it's
        just checking attribute presence.
        """
        class PropertyAgent:
            @property
            def assist(self) -> Any:
                async def _func(session: Any, request: Any, handler: Any) -> None:
                    pass
                return _func

            async def shutdown(self) -> None:
                pass

        # isinstance checks if 'assist' is present. It usually doesn't call it.
        # But if it's a property, it might need to evaluate it or just check descriptor presence.
        # This is a bit of a gray area in runtime_checkable.
        # In Python < 3.12, properties often satisfy protocols looking for methods if they exist.
        assert isinstance(PropertyAgent(), IAgentRuntime)
