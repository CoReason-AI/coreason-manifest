from datetime import datetime
from typing import Annotated, Optional, Union
from uuid import uuid4

from coreason_identity import UserContext
from pydantic import BaseModel, Field

from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import AgentDefinition, AgentDependencies, AgentMetadata, AgentTopology, ModelConfig, Step


def test_optional_user_context() -> None:
    def my_agent(u: Optional[UserContext]) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)
    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "u" not in properties


def test_annotated_user_context() -> None:
    def my_agent(u: Annotated[UserContext, "System User"]) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)
    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "u" not in properties


def test_union_user_context() -> None:
    # A bit weird, but "UserContext or int". If UserContext is possible, it should probably be injected?
    # Or maybe it's ambiguous. But safe default is to inject if it *can* be UserContext.
    def my_agent(u: Union[UserContext, int]) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)
    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "u" not in properties


def test_keyword_only_user_context() -> None:
    def my_agent(*, user_context: UserContext) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)
    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "user_context" not in properties


def test_multiple_user_contexts() -> None:
    def my_agent(u1: UserContext, u2: UserContext) -> str:
        return "ok"

    interface = ManifestLoader.inspect_function(my_agent)
    # Should only list 'user_context' once in injected_params
    assert interface.injected_params == ["user_context"]
    properties = interface.inputs.get("properties", {})
    assert "u1" not in properties
    assert "u2" not in properties


def test_decorator_inspection() -> None:
    from functools import wraps
    from typing import Any

    def my_decorator(f: Any) -> Any:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        return wrapper

    @my_decorator
    def my_agent(arg1: str, user_context: UserContext) -> str:
        return "ok"

    # inspect.signature follows wrappers by default
    interface = ManifestLoader.inspect_function(my_agent)
    assert "user_context" in interface.injected_params
    properties = interface.inputs.get("properties", {})
    assert "arg1" in properties
    assert "user_context" not in properties


def test_complex_workflow() -> None:
    class Query(BaseModel):
        q: str = Field(..., description="The query string")
        limit: int = 10

    class Response(BaseModel):
        answer: str
        timestamp: datetime

    def agent_func(query: Query, user: UserContext) -> Response:
        return Response(answer=f"{query.q} for {user.user_id}", timestamp=datetime.now())

    # 1. Inspect
    interface = ManifestLoader.inspect_function(agent_func)

    assert "user_context" in interface.injected_params
    assert "query" in interface.inputs.get("properties", {})
    assert "user" not in interface.inputs.get("properties", {})

    # 2. Build Definition
    meta = AgentMetadata(
        id=uuid4(), version="0.1.0", name="Complex Agent", author="Test", created_at=datetime.now(), requires_auth=True
    )
    topo = AgentTopology(steps=(Step(id="start"),), model_config=ModelConfig(model="gpt-4", temperature=0.5))
    deps = AgentDependencies()

    defn = AgentDefinition(
        metadata=meta, interface=interface, topology=topo, dependencies=deps, integrity_hash="a" * 64
    )

    # 3. Serialize/Validate
    json_data = defn.model_dump(mode="json")
    assert json_data["metadata"]["requires_auth"] is True
    assert "user_context" in json_data["interface"]["injected_params"]
