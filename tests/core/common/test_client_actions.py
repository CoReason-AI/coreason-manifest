import pytest
from pydantic import ValidationError

from coreason_manifest.core.common.client_actions import (
    ActionCopyClipboard,
    ActionDeepLink,
    ActionDownloadFile,
    ActionNativeShare,
    ActionOpenUrl,
    ActionRequestBiometrics,
    ActionShowToast,
    ActionTriggerHaptic,
    ClientActionMap,
    ClientActionType,
)


def test_action_open_url_creation():
    action = ActionOpenUrl(url="https://example.com")
    assert action.action_type == ClientActionType.OPEN_URL
    assert action.url == "https://example.com"
    assert action.target == "_blank"  # default value

    action_self = ActionOpenUrl(url="https://example.com", target="_self")
    assert action_self.target == "_self"


def test_action_deep_link_creation():
    action = ActionDeepLink(route="/home")
    assert action.action_type == ClientActionType.DEEP_LINK
    assert action.route == "/home"
    assert action.params is None  # default value

    action_with_params = ActionDeepLink(route="/user", params={"id": 123})
    assert action_with_params.params == {"id": 123}


def test_action_copy_clipboard_creation():
    action = ActionCopyClipboard(text="copied text")
    assert action.action_type == ClientActionType.COPY_CLIPBOARD
    assert action.text == "copied text"


def test_action_native_share_creation():
    action = ActionNativeShare(title="Share this", text="Some cool content")
    assert action.action_type == ClientActionType.NATIVE_SHARE
    assert action.title == "Share this"
    assert action.text == "Some cool content"
    assert action.url is None

    action_with_url = ActionNativeShare(title="Title", text="Text", url="https://example.com")
    assert action_with_url.url == "https://example.com"


def test_action_download_file_creation():
    action = ActionDownloadFile(url="https://example.com/file.pdf", filename="file.pdf")
    assert action.action_type == ClientActionType.DOWNLOAD_FILE
    assert action.url == "https://example.com/file.pdf"
    assert action.filename == "file.pdf"


def test_action_trigger_haptic_creation():
    action = ActionTriggerHaptic(style="success")
    assert action.action_type == ClientActionType.TRIGGER_HAPTIC
    assert action.style == "success"

    with pytest.raises(ValidationError):
        ActionTriggerHaptic(style="invalid_style")


def test_action_show_toast_creation():
    action = ActionShowToast(message="Hello World")
    assert action.action_type == ClientActionType.SHOW_TOAST
    assert action.message == "Hello World"
    assert action.style == "info"

    action_success = ActionShowToast(message="Done", style="success")
    assert action_success.style == "success"

    with pytest.raises(ValidationError):
        ActionShowToast(message="Bad", style="invalid_style")


def test_action_request_biometrics_creation():
    action = ActionRequestBiometrics(reason="Authenticate to continue")
    assert action.action_type == ClientActionType.REQUEST_BIOMETRICS
    assert action.reason == "Authenticate to continue"


def test_client_action_map_valid_trigger():
    action1 = ActionOpenUrl(url="https://example.com")
    action2 = ActionShowToast(message="Opening URL...")

    action_map = ClientActionMap(trigger="on_click", actions=[action1, action2])
    assert action_map.trigger == "on_click"
    assert len(action_map.actions) == 2
    assert isinstance(action_map.actions[0], ActionOpenUrl)
    assert isinstance(action_map.actions[1], ActionShowToast)


def test_client_action_map_invalid_trigger_on_mount():
    action = ActionShowToast(message="Mounting...")
    with pytest.raises(ValidationError) as exc_info:
        ClientActionMap(trigger="on_mount", actions=[action])

    assert "Invalid trigger 'on_mount'. Client actions must be explicitly triggered by user interaction." in str(
        exc_info.value
    )


def test_client_action_map_invalid_trigger_on_render():
    action = ActionShowToast(message="Rendering...")
    with pytest.raises(ValidationError) as exc_info:
        ClientActionMap(trigger="on_render", actions=[action])

    assert "Invalid trigger 'on_render'. Client actions must be explicitly triggered by user interaction." in str(
        exc_info.value
    )
