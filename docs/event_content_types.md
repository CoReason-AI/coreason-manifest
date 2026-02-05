# Event Content Types

This specification defines the standard MIME types used in the `datacontenttype` field of `CloudEvent` envelopes within the Coreason ecosystem.

## Overview

To ensure strict protocol compliance and prevent "magic string" errors, Coreason defines a set of standard MIME types for event payloads. These are available via the `EventContentType` enumeration.

## Standard Types

The `EventContentType` enum (inheriting from `str` and `Enum`) defines the following values:

| Enum Member | MIME Type | Description |
| :--- | :--- | :--- |
| `JSON` | `application/json` | Standard JSON payload. Default. |
| `STREAM` | `application/vnd.coreason.stream+json` | Used for streaming responses (SSE-compatible data). |
| `ERROR` | `application/vnd.coreason.error+json` | Structured error reports. |
| `ARTIFACT` | `application/vnd.coreason.artifact+json` | References to generated artifacts (files, images). |

## Usage

### Python

```python
from coreason_manifest import CloudEvent, EventContentType

# Using the Enum
event = CloudEvent(
    id="evt-1",
    source="urn:mysource",
    type="my.event",
    time=datetime.now(timezone.utc),
    datacontenttype=EventContentType.ERROR,
    data={"code": "500", "message": "Internal Server Error"}
)

# Serializes to:
# {
#   ...
#   "datacontenttype": "application/vnd.coreason.error+json",
#   ...
# }
```

### Polymorphism

The `CloudEvent.datacontenttype` field is typed as `Union[EventContentType, str]`. This allows:
1.  **Strict Typing:** Using `EventContentType` members for known Coreason types.
2.  **Flexibility:** Passing raw strings for custom or external MIME types (e.g., `text/plain`, `image/png`).

```python
# Custom content type
event = CloudEvent(
    ...
    datacontenttype="application/x-custom-type"
)
```
