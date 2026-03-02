from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class ClientActionType(StrEnum):
    OPEN_URL = "open_url"
    DEEP_LINK = "deep_link"
    COPY_CLIPBOARD = "copy_clipboard"
    NATIVE_SHARE = "native_share"
    DOWNLOAD_FILE = "download_file"
    TRIGGER_HAPTIC = "trigger_haptic"
    SHOW_TOAST = "show_toast"
    REQUEST_BIOMETRICS = "request_biometrics"


class ActionOpenUrl(CoreasonModel):
    action_type: Literal[ClientActionType.OPEN_URL] = ClientActionType.OPEN_URL
    url: str
    target: Literal["_blank", "_self"] = "_blank"


class ActionDeepLink(CoreasonModel):
    action_type: Literal[ClientActionType.DEEP_LINK] = ClientActionType.DEEP_LINK
    route: str
    params: dict[str, Any] | None = None


class ActionCopyClipboard(CoreasonModel):
    action_type: Literal[ClientActionType.COPY_CLIPBOARD] = ClientActionType.COPY_CLIPBOARD
    text: str


class ActionNativeShare(CoreasonModel):
    action_type: Literal[ClientActionType.NATIVE_SHARE] = ClientActionType.NATIVE_SHARE
    title: str
    text: str
    url: str | None = None


class ActionDownloadFile(CoreasonModel):
    action_type: Literal[ClientActionType.DOWNLOAD_FILE] = ClientActionType.DOWNLOAD_FILE
    url: str
    filename: str


class ActionTriggerHaptic(CoreasonModel):
    action_type: Literal[ClientActionType.TRIGGER_HAPTIC] = ClientActionType.TRIGGER_HAPTIC
    style: Literal["light", "medium", "heavy", "success", "error"]


class ActionShowToast(CoreasonModel):
    action_type: Literal[ClientActionType.SHOW_TOAST] = ClientActionType.SHOW_TOAST
    message: str
    style: Literal["info", "success", "error"] = "info"


class ActionRequestBiometrics(CoreasonModel):
    action_type: Literal[ClientActionType.REQUEST_BIOMETRICS] = ClientActionType.REQUEST_BIOMETRICS
    reason: str


ClientActionPayload = Annotated[
    ActionOpenUrl
    | ActionDeepLink
    | ActionCopyClipboard
    | ActionNativeShare
    | ActionDownloadFile
    | ActionTriggerHaptic
    | ActionShowToast
    | ActionRequestBiometrics,
    Field(discriminator="action_type"),
]


class ClientActionMap(CoreasonModel):
    trigger: str
    actions: list[ClientActionPayload]

    @model_validator(mode="after")
    def validate_trigger(self) -> "ClientActionMap":
        """Enforce that client actions are explicitly triggered by user interaction."""
        if self.trigger.lower() in ("on_mount", "on_render"):
            raise ValueError(
                f"Invalid trigger '{self.trigger}'. Client actions must be explicitly triggered by user interaction."
            )
        return self
