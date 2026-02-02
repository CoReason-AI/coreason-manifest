import re
from typing import Any, Dict, List, Optional

import yaml

from coreason_manifest.builder.agent import AgentBuilder
from coreason_manifest.definitions.agent import (
    AgentCapability,
    AgentDefinition,
    AgentStatus,
    CapabilityType,
    DeliveryMode,
)


class SchemaCapability:
    """A capability builder that uses raw JSON schemas instead of Pydantic models.

    This class is used by the DSL loader to bridge the gap between simplified YAML
    definitions and the AgentBuilder, which typically expects typed Pydantic models.
    """

    def __init__(
        self,
        name: str,
        description: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        type: CapabilityType = CapabilityType.ATOMIC,
        delivery_mode: DeliveryMode = DeliveryMode.REQUEST_RESPONSE,
        injected_params: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.type = type
        self.delivery_mode = delivery_mode
        self.injected_params = injected_params or []

    def to_definition(self) -> AgentCapability:
        """Convert to strict AgentCapability definition."""
        return AgentCapability(
            name=self.name,
            type=self.type,
            description=self.description,
            inputs=self.inputs,
            outputs=self.outputs,
            injected_params=self.injected_params,
            delivery_mode=self.delivery_mode,
        )


def _expand_shorthand_type(shorthand: str) -> Dict[str, Any]:
    """Expand a shorthand type string into a JSON Schema dictionary.

    Args:
        shorthand: Type string like 'string', 'int', 'list[string]'.

    Returns:
        JSON Schema dictionary.
    """
    shorthand = shorthand.strip()

    # Handle array/list types
    array_match = re.match(r"^(?:list|array)\[(.+)\]$", shorthand, re.IGNORECASE)
    if array_match:
        inner_type = array_match.group(1)
        return {"type": "array", "items": _expand_shorthand_type(inner_type)}

    # Handle basic types
    start = shorthand.lower()
    if start == "string":
        return {"type": "string"}
    elif start in ("int", "integer"):
        return {"type": "integer"}
    elif start in ("float", "number"):
        return {"type": "number"}
    elif start in ("bool", "boolean"):
        return {"type": "boolean"}
    elif start == "any":
        return {}

    # Fallback/Default (treat as string or maybe error? treating as string seems safe for now or raise)
    # The prompt implies specific mappings. If unknown, we might want to raise error.
    # But for robustness let's assume it's a string if we don't know it, or raise.
    # Let's raise ValueError to be safe.
    raise ValueError(f"Unknown shorthand type: {shorthand}")


def _expand_properties(props: Dict[str, str]) -> Dict[str, Any]:
    """Convert a dictionary of name:shorthand to a JSON Schema Object.

    Args:
        props: Dictionary mapping field names to shorthand types.

    Returns:
        Full JSON Schema Object definition.
    """
    properties = {}
    required = []

    for name, shorthand in props.items():
        properties[name] = _expand_shorthand_type(shorthand)
        required.append(name)

    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


def load_from_yaml(content: str) -> AgentDefinition:
    """Parse a simplified YAML string into a valid AgentDefinition.

    Args:
        content: The YAML string.

    Returns:
        A compiled AgentDefinition.
    """
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("YAML content must resolve to a dictionary.")

    # Extract metadata
    name = data.get("name")
    if not name:
        raise ValueError("Field 'name' is required.")

    version = data.get("version", "0.1.0")
    author = data.get("author", "Unknown")

    status_str = data.get("status", "draft").lower()
    status = AgentStatus.PUBLISHED if status_str == "published" else AgentStatus.DRAFT

    builder = AgentBuilder(name=name, version=str(version), author=author, status=status)

    # Process Capabilities
    capabilities = data.get("capabilities", [])
    for cap_data in capabilities:
        cap_name = cap_data.get("name")
        if not cap_name:
            raise ValueError("Capability must have a 'name'.")

        description = cap_data.get("description", "")
        cap_type_str = cap_data.get("type", "atomic")
        cap_type = CapabilityType(cap_type_str)

        # Delivery mode defaults to request_response, but let's check if it's in YAML
        # The prompt didn't explicitly mention delivery_mode in YAML example, but good to support.
        # We'll use default from AgentCapability if not present.
        delivery_mode_str = cap_data.get("delivery_mode", DeliveryMode.REQUEST_RESPONSE.value)
        delivery_mode = DeliveryMode(delivery_mode_str)

        inputs_shorthand = cap_data.get("inputs", {})
        outputs_shorthand = cap_data.get("outputs", {})

        inputs_schema = _expand_properties(inputs_shorthand)
        outputs_schema = _expand_properties(outputs_shorthand)

        # Create schema capability
        cap = SchemaCapability(
            name=cap_name,
            description=description,
            inputs=inputs_schema,
            outputs=outputs_schema,
            type=cap_type,
            delivery_mode=delivery_mode,
        )

        # Add to builder - ignore type check because AgentBuilder expects TypedCapability
        builder.with_capability(cap)  # type: ignore

    # Process Model Config
    model_data = data.get("model")
    if model_data:
        model_name = model_data.get("name", "gpt-4o")
        temperature = model_data.get("temperature", 0.0)
        builder.with_model(model=model_name, temperature=temperature)

    # Process System Prompt
    system_prompt = data.get("system_prompt")
    if system_prompt:
        builder.with_system_prompt(system_prompt)

    return builder.build()
