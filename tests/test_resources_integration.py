import pytest
from coreason_manifest.definitions.agent import AgentDependencies
from coreason_manifest import (
    RemoteServiceResource,
    ResourceRiskLevel,
    SidecarResource,
)
from pydantic import ValidationError

def test_sidecar_resource():
    # Test valid sidecar
    sidecar = SidecarResource(
        name="redis-sidecar",
        image="redis:alpine",
        env_vars={"REDIS_PORT": "6379"},
        ports=[6379],
        command=["redis-server"]
    )
    assert sidecar.name == "redis-sidecar"
    assert sidecar.image == "redis:alpine"
    assert sidecar.env_vars == {"REDIS_PORT": "6379"}
    assert sidecar.ports == [6379]
    assert sidecar.command == ["redis-server"]

    # Test minimal sidecar
    minimal = SidecarResource(name="minimal", image="busybox")
    assert minimal.env_vars is None
    assert minimal.ports is None
    assert minimal.command is None

def test_remote_service_resource():
    # Test valid remote service
    service = RemoteServiceResource(
        name="weather-api",
        uri="https://api.weather.com",
        scopes=["read"],
        connection_secret_env="WEATHER_API_KEY",
        risk_level=ResourceRiskLevel.SAFE
    )
    assert service.name == "weather-api"
    # Pydantic v2 AnyUrl usually normalizes, let's check basic string match or startswith
    assert str(service.uri).startswith("https://api.weather.com")
    assert service.risk_level == ResourceRiskLevel.SAFE

    # Test invalid uri
    with pytest.raises(ValidationError):
        RemoteServiceResource(
            name="bad-uri",
            uri="not-a-uri",
            risk_level=ResourceRiskLevel.STANDARD
        )

def test_agent_dependencies_integration():
    sidecar = SidecarResource(name="db", image="postgres")
    remote = RemoteServiceResource(
        name="llm",
        uri="https://api.openai.com",
        risk_level=ResourceRiskLevel.CRITICAL
    )

    deps = AgentDependencies(
        sidecars=[sidecar],
        remote_services=[remote]
    )

    assert len(deps.sidecars) == 1
    assert deps.sidecars[0].name == "db"
    assert len(deps.remote_services) == 1
    assert deps.remote_services[0].risk_level == ResourceRiskLevel.CRITICAL
    # Check default for tools
    assert deps.tools == []

def test_resource_risk_level_values():
    assert ResourceRiskLevel.SAFE.value == "SAFE"
    assert ResourceRiskLevel.STANDARD.value == "STANDARD"
    assert ResourceRiskLevel.CRITICAL.value == "CRITICAL"
