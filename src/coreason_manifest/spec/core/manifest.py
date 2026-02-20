from typing import Annotated, Any, ClassVar
import re
import json

from pydantic import ConfigDict, Field, model_validator

from coreason_manifest.spec.core.flow import LinearFlow, GraphFlow
from coreason_manifest.spec.core.resilience import RecoveryReceipt
from coreason_manifest.spec.core_base import ObservableModel

AnyFlow = Annotated[LinearFlow | GraphFlow, Field(discriminator="kind")]


class Manifest(ObservableModel):
    """
    The root container for any Coreason Manifest.
    Includes auto-healing and versioning capabilities.
    """
    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)

    manifest_version: str = "v1"
    flow: AnyFlow

    # Internal storage for recovery receipt
    _recovery_receipt: RecoveryReceipt | None = None

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        auto_heal: bool = False,
    ) -> "Manifest":
        """
        Custom model_validate with auto_heal support.
        """
        if auto_heal:
            obj, receipt = cls._perform_auto_healing(obj)
            if context is None:
                context = {}
            context["recovery_receipt"] = receipt

        instance = super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)

        if auto_heal and context and "recovery_receipt" in context:
            # Bypass frozen attribute check using object.__setattr__
            object.__setattr__(instance, "_recovery_receipt", context["recovery_receipt"])

        return instance

    @property
    def recovery_receipt(self) -> RecoveryReceipt | None:
        return getattr(self, "_recovery_receipt", None)

    @classmethod
    def _perform_auto_healing(cls, data: Any) -> tuple[Any, RecoveryReceipt]:
        mutations = []
        cleaned_data = data

        # 1. Strip Markdown JSON blocks if input is string
        if isinstance(cleaned_data, str):
            original_str = cleaned_data
            if "```json" in cleaned_data:
                match = re.search(r"```json\s*(.*?)\s*```", cleaned_data, re.DOTALL)
                if match:
                    cleaned_data = match.group(1)
                    mutations.append("Stripped markdown code blocks (```json)")
            elif "```" in cleaned_data:
                 match = re.search(r"```\s*(.*?)\s*```", cleaned_data, re.DOTALL)
                 if match:
                    cleaned_data = match.group(1)
                    mutations.append("Stripped markdown code blocks (```)")

            # 2. Strip trailing commas
            # A simple regex approach for trailing commas before } or ]
            # Note: This is a heuristic and might affect string content if not careful.
            # But usually acceptable for "Auto-Heal" of generated JSON.
            cleaned_no_commas = re.sub(r",\s*([}\]])", r"\1", cleaned_data)
            if cleaned_no_commas != cleaned_data:
                cleaned_data = cleaned_no_commas
                mutations.append("Stripped trailing commas")

            # Parse JSON if it was a string
            try:
                cleaned_data = json.loads(cleaned_data)
            except json.JSONDecodeError:
                # If parsing fails, we return whatever we have, validation will likely fail later
                # unless mutations fixed it.
                pass

        # 3. Coerce stringified booleans
        if isinstance(cleaned_data, (dict, list)):
            cleaned_data, changed = cls._recursive_coerce(cleaned_data)
            if changed:
                mutations.append("Coerced stringified booleans")

        return cleaned_data, RecoveryReceipt(mutations=mutations)

    @classmethod
    def _recursive_coerce(cls, obj: Any) -> tuple[Any, bool]:
        changed = False
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                v_new, v_changed = cls._recursive_coerce(v)
                new_obj[k] = v_new
                if v_changed:
                    changed = True
            return new_obj, changed
        elif isinstance(obj, list):
            new_list = []
            for v in obj:
                v_new, v_changed = cls._recursive_coerce(v)
                new_list.append(v_new)
                if v_changed:
                    changed = True
            return new_list, changed
        elif isinstance(obj, str):
            if obj.lower() == "true":
                return True, True
            if obj.lower() == "false":
                return False, True
        return obj, changed
