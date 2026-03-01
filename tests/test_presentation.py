import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.presentation import UIEventMap


def test_uieventmap_valid_payload_mapping() -> None:
    # Valid map
    evt = UIEventMap(
        trigger="on_click", action="submit", mutates_variables=["user_id", "status"], payload_mapping={"id": "user_id"}
    )
    assert evt.payload_mapping and evt.payload_mapping["id"] == "user_id"


def test_uieventmap_invalid_payload_mapping_target_not_in_mutates() -> None:
    with pytest.raises(ValidationError, match="not allowed by mutates_variables"):
        UIEventMap(trigger="on_click", action="submit", mutates_variables=["status"], payload_mapping={"id": "user_id"})


def test_uieventmap_invalid_payload_mapping_requires_mutates() -> None:
    with pytest.raises(ValidationError, match="requires mutates_variables to be defined"):
        UIEventMap(trigger="on_click", action="submit", payload_mapping={"id": "user_id"})


def test_uieventmap_no_payload_mapping() -> None:
    evt = UIEventMap(trigger="on_click", action="submit")
    assert evt.payload_mapping is None
