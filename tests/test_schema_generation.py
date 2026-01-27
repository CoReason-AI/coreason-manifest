from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from coreason_identity import UserContext
from pydantic import BaseModel, ValidationError

from coreason_manifest.errors import ManifestSyntaxError
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import (
    AgentDefinition,
    AgentDependencies,
    AgentInterface,
    AgentMetadata,
    AgentTopology,
    ModelConfig,
    Step,
)


def test_inspect_function_with_user_context() -> None:
    def my_agent(arg1: str, user_context: UserContext) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)

    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "user_context" not in properties
    assert "arg1" in properties


def test_inspect_function_with_user_context_by_name() -> None:
    def my_agent(arg1: str, user_context: int) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)

    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "user_context" not in properties


def test_inspect_function_without_user_context() -> None:
    def my_agent(arg1: int) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)

    assert "user_context" not in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "arg1" in properties


def test_inspect_function_forbidden_args() -> None:
    def my_agent(api_key: str) -> None:
        pass

    with pytest.raises(ManifestSyntaxError) as exc:
        ManifestLoader.inspect_function(my_agent)
    assert "forbidden" in str(exc.value)

    def my_agent_token(token: str) -> None:
        pass

    with pytest.raises(ManifestSyntaxError) as exc:
        ManifestLoader.inspect_function(my_agent_token)
    assert "forbidden" in str(exc.value)


def test_inspect_function_pydantic_return() -> None:
    class Result(BaseModel):
        val: int

    def my_agent(x: int) -> Result:
        return Result(val=x)

    interface = ManifestLoader.inspect_function(my_agent)
    properties = interface.outputs.get("properties", {})
    assert "val" in properties


def test_inspect_function_class_method() -> None:
    class MyAgent:
        def run(self, x: int) -> int:
            return x

    interface = ManifestLoader.inspect_function(MyAgent.run)
    properties = interface.inputs.get("properties", {})
    assert "self" not in properties
    assert "x" in properties


def test_inspect_function_no_hints() -> None:
    def my_agent(x: Any) -> Any:
        return x

    interface = ManifestLoader.inspect_function(my_agent)
    properties = interface.inputs.get("properties", {})
    assert "x" in properties


def test_agent_definition_validation_success() -> None:
    meta = AgentMetadata(
        id=uuid4(), version="1.0.0", name="Test", author="Me", created_at=datetime.now(), requires_auth=True
    )
    interface = AgentInterface(inputs={}, outputs={}, injected_params=["user_context"])
    topo = AgentTopology(
        steps=(Step(id="1", description="test"),), model_config=ModelConfig(model="gpt-4", temperature=0.1)
    )
    deps = AgentDependencies()

    agent = AgentDefinition(
        metadata=meta, interface=interface, topology=topo, dependencies=deps, integrity_hash="a" * 64
    )
    assert agent.metadata.requires_auth is True


def test_agent_definition_validation_failure() -> None:
    meta = AgentMetadata(
        id=uuid4(), version="1.0.0", name="Test", author="Me", created_at=datetime.now(), requires_auth=True
    )
    interface = AgentInterface(inputs={}, outputs={}, injected_params=[])
    topo = AgentTopology(
        steps=(Step(id="1", description="test"),), model_config=ModelConfig(model="gpt-4", temperature=0.1)
    )
    deps = AgentDependencies()

    with pytest.raises(ValidationError) as exc:
        AgentDefinition(metadata=meta, interface=interface, topology=topo, dependencies=deps, integrity_hash="a" * 64)
    assert "Agent requires authentication but 'user_context' is not an injected parameter" in str(exc.value)


def test_inspect_function_create_model_fail() -> None:
    def my_agent(**kwargs: Any) -> None:
        pass

    interface = ManifestLoader.inspect_function(my_agent)
    assert interface.inputs is not None


def test_inspect_function_return_none() -> None:
    def my_agent() -> None:
        pass

    interface = ManifestLoader.inspect_function(my_agent)
    assert interface.outputs == {}
