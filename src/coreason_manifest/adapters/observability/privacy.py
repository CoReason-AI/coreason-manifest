from typing import Any

SAFE_UI_PROPS = {"variant", "size", "disabled", "color", "isLoading", "className", "style", "id", "name", "type", "key"}


def scrub_genui_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively scrubs PII from a Generative UI payload.
    It looks for 'props' fields inside components and replaces sensitive values within 'props'
    with '[REDACTED_PII]', while maintaining safe UI styling properties and schema intact.

    Args:
        payload: The GenUI payload dictionary.

    Returns:
        A new dictionary with scrubbed PII.
    """
    if not isinstance(payload, dict):
        return payload

    scrubbed: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "props" and isinstance(value, dict):
            # Scrub values inside props unless they are in SAFE_UI_PROPS
            scrubbed[key] = {k: v if k in SAFE_UI_PROPS else "[REDACTED_PII]" for k, v in value.items()}
        elif isinstance(value, dict):
            # Recursively scrub nested dictionaries
            scrubbed[key] = scrub_genui_payload(value)
        elif isinstance(value, list):
            # Recursively scrub list items
            scrubbed[key] = [scrub_genui_payload(item) if isinstance(item, dict) else item for item in value]
        else:
            scrubbed[key] = value

    return scrubbed
