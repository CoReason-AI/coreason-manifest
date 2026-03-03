from typing import Any


def scrub_genui_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively scrubs PII from a Generative UI payload.
    It looks for 'props' fields inside components and replaces all values within 'props'
    with '[REDACTED_PII]', while maintaining the schema/structure intact.

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
            # Scrub values inside props
            scrubbed[key] = dict.fromkeys(value, "[REDACTED_PII]")
        elif isinstance(value, dict):
            # Recursively scrub nested dictionaries
            scrubbed[key] = scrub_genui_payload(value)
        elif isinstance(value, list):
            # Recursively scrub list items
            scrubbed[key] = [
                scrub_genui_payload(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            scrubbed[key] = value

    return scrubbed
