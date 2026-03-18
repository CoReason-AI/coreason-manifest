import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# 1. Import ManifestViolationReceipt
content = content.replace("System2RemediationIntent,", "System2RemediationIntent,\n    ManifestViolationReceipt,")

# 2. Fix calculate_latent_alignment ValueError -> TamperFaultEvent
content = content.replace('raise ValueError("TamperFaultEvent: Latent alignment failed.")', 'raise TamperFaultEvent("Latent alignment failed.")')

# 3. generate_correction_prompt rewrite
new_generate_correction_prompt = """def generate_correction_prompt(error: ValidationError, target_node_id: str, fault_id: str) -> System2RemediationIntent:
    \"\"\"
    Pure functional adapter. Maps a raw Pythonic pydantic.ValidationError into a
    language-model-legible System2RemediationIntent without triggering runtime side effects.
    \"\"\"
    receipts: list[ManifestViolationReceipt] = []
    for err in error.errors():
        loc_path = "".join(f"/{item!s}" for item in err["loc"]) if err["loc"] else "/"
        err_type = err["type"]
        msg = err.get("msg", "Invalid structural payload.")

        receipts.append(ManifestViolationReceipt(
            failing_pointer=loc_path,
            violation_type=err_type,
            diagnostic_message=msg
        ))

    return System2RemediationIntent(
        fault_id=fault_id,
        target_node_id=target_node_id,
        violation_receipts=receipts
    )"""

old_generate_correction_prompt_re = r'def generate_correction_prompt\(.*?-> System2RemediationIntent:\n.*?return System2RemediationIntent\([^)]+\)'
content = re.sub(old_generate_correction_prompt_re, new_generate_correction_prompt, content, flags=re.DOTALL)


# 4. Refactoring apply_state_differential to use dispatch

# Remove existing functions and create the top-level helpers
apply_state_differential_re = r'def apply_state_differential\(.*?return new_state'

new_helpers_and_dispatch = """def _resolve_from_path(new_state: Any, from_path: str) -> tuple[Any, Any]:
    if not isinstance(from_path, str) or not from_path.startswith("/"):
        raise ValueError(f"Invalid from_path: {from_path}")

    from_parts = [p.replace("~1", "/").replace("~0", "~") for p in from_path.split("/")[1:]]
    from_target: Any = new_state
    for part in from_parts[:-1]:
        if isinstance(from_target, dict):
            if part not in from_target:
                raise ValueError(f"Invalid from_path: {from_path}")
            from_target = from_target[part]
        elif isinstance(from_target, list):
            try:
                idx = int(part)
                from_target = from_target[idx]
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid from_path: {from_path}") from e
        else:
            raise ValueError(f"Invalid from_path: {from_path}")

    from_last = from_parts[-1]
    return from_target, from_last

def _extract_from_target(t: Any, key: str) -> Any:
    if isinstance(t, dict):
        if key not in t:
            raise ValueError("Key not found")
        return t[key]
    if isinstance(t, list):
        if key == "-":
            raise ValueError("Cannot extract from end of array")
        try:
            idx = int(key)
            if idx < 0 or idx >= len(t):
                raise ValueError("Index out of bounds")
            return t[idx]
        except ValueError as e:
            raise ValueError("Invalid index") from e
    raise ValueError("Target is not dict or list")

def _ablate_from_target(t: Any, key: str) -> None:
    if isinstance(t, dict):
        if key not in t:
            raise ValueError("Key not found")
        del t[key]
    elif isinstance(t, list):
        if key == "-":
            raise ValueError("Cannot remove from end of array")
        try:
            idx = int(key)
            if idx < 0 or idx >= len(t):
                raise ValueError("Index out of bounds")
            t.pop(idx)
        except ValueError as e:
            raise ValueError("Invalid index") from e

def _apply_patch_add(target: Any, last_part: str, value: Any) -> None:
    if isinstance(target, dict):
        target[last_part] = value
    elif isinstance(target, list):
        if last_part == "-":
            target.append(value)
        else:
            try:
                idx = int(last_part)
                if idx < 0 or idx > len(target):
                    raise ValueError(f"Index out of bounds: {last_part}")
                target.insert(idx, value)
            except ValueError as e:
                raise ValueError(f"Invalid index: {last_part}") from e
    else:
        raise ValueError(f"Cannot add to path: {last_part}")

def _apply_patch_remove(target: Any, last_part: str) -> None:
    try:
        _ablate_from_target(target, last_part)
    except ValueError as e:
        raise ValueError(f"Cannot remove from path: {e}") from e

def _apply_patch_replace(target: Any, last_part: str, value: Any) -> None:
    try:
        _extract_from_target(target, last_part)
        if isinstance(target, dict):
            target[last_part] = value
        elif isinstance(target, list):
            if last_part == "-":
                raise ValueError("Cannot replace at end of array")
            idx = int(last_part)
            target[idx] = value
    except ValueError as e:
        raise ValueError(f"Cannot replace at path: {e}") from e

def _apply_patch_copy_move(new_state: Any, target: Any, last_part: str, patch: Any) -> None:
    from_path = patch.from_path
    if from_path is None:
        raise ValueError("from_path is mathematically required for copy/move operations.")

    if patch.path.startswith(from_path + "/"):
        raise ValueError(f"The 'from' location MUST NOT be a proper prefix of the 'path' location: {patch.path}")

    try:
        from_target, from_last = _resolve_from_path(new_state, from_path)
        val = _extract_from_target(from_target, from_last)
        if patch.op == "move":
            _ablate_from_target(from_target, from_last)
        if patch.op == "copy":
            val = copy.deepcopy(val)
    except ValueError as e:
        raise ValueError(f"Invalid from_path operation: {e}") from e

    if isinstance(target, dict):
        target[last_part] = val
    elif isinstance(target, list):
        if last_part == "-":
            target.append(val)
        else:
            try:
                idx = int(last_part)

                if patch.op == "move" and from_target is target:
                    try:
                        from_idx = int(from_last)
                        if from_idx < int(last_part):
                            idx -= 1
                    except ValueError:
                        pass

                if idx < 0 or idx > len(target):
                    raise ValueError(f"Index out of bounds")
                target.insert(idx, val)
            except ValueError as e:
                raise ValueError(f"Invalid index: {last_part}") from e
    else:
        raise ValueError(f"Cannot copy/move to path")

def _apply_patch_test(target: Any, last_part: str, value: Any) -> None:
    try:
        current_val = _extract_from_target(target, last_part)
        if current_val != value:
            raise ValueError("Patch test operation failed.")
    except ValueError as e:
        if "Patch test operation failed" in str(e):
            raise
        raise ValueError("Patch test operation failed.") from e

def apply_state_differential(
    current_state: dict[str, Any], manifest: ontology.StateDifferentialManifest
) -> dict[str, Any]:
    \"\"\"
    A pure mathematical functor to apply an RFC 6902 JSON patch without mutating the input dictionary.
    \"\"\"
    new_state = copy.deepcopy(current_state)

    for patch in manifest.patches:
        path = patch.path
        if not path.startswith("/"):
            if path == "":
                if patch.op == "test":
                    if new_state != patch.value:
                        raise ValueError("Patch test operation failed.")
                    continue
                raise ValueError(f"Invalid path or root operation not supported: {path}")
            raise ValueError(f"Invalid JSON pointer: {path}")

        parts = []
        for p in path.split("/")[1:]:
            if "~" in p and not (p.endswith(("~0", "~1")) or "~0" in p or "~1" in p):
                raise ValueError(f"Invalid JSON pointer: {path}")
            parts.append(p.replace("~1", "/").replace("~0", "~"))

        target: Any = new_state
        for part in parts[:-1]:
            if isinstance(target, dict):
                if part not in target:
                    raise ValueError(f"Invalid path: {path}")
                target = target[part]
            elif isinstance(target, list):
                try:
                    idx = int(part)
                    target = target[idx]
                except (ValueError, IndexError) as e:
                    raise ValueError(f"Invalid path: {path}") from e
            else:
                raise ValueError(f"Invalid path: {path}")

        last_part = parts[-1]

        PATCH_DISPATCH = {
            "add": lambda: _apply_patch_add(target, last_part, patch.value),
            "remove": lambda: _apply_patch_remove(target, last_part),
            "replace": lambda: _apply_patch_replace(target, last_part, patch.value),
            "copy": lambda: _apply_patch_copy_move(new_state, target, last_part, patch),
            "move": lambda: _apply_patch_copy_move(new_state, target, last_part, patch),
            "test": lambda: _apply_patch_test(target, last_part, patch.value),
        }

        try:
            PATCH_DISPATCH[patch.op]()
        except ValueError as e:
            # We preserve the original exception messaging strategy to not break any possible external test suite reliance on the exact strings in apply_state_differential.
            if patch.op in ("remove", "replace") and not "Patch test operation failed" in str(e):
               raise ValueError(f"Cannot {patch.op} at path {path}: {e}") from e
            elif patch.op == "remove":
                # Special case, old code used from path: {e} and from path {path}: {e} for remove/replace.
                raise ValueError(f"Cannot remove from path {path}: {e}") from e
            elif patch.op == "replace":
                raise ValueError(f"Cannot replace at path {path}: {e}") from e
            elif patch.op in ("copy", "move"):
                # Exception was: raise ValueError(f"Cannot copy/move to path: {path}") or f"Index out of bounds: {path}"
                msg = str(e)
                if msg == "Cannot copy/move to path":
                    raise ValueError(f"Cannot copy/move to path: {path}")
                elif msg == "Index out of bounds":
                    raise ValueError(f"Index out of bounds: {path}")
                raise
            elif patch.op == "add":
                msg = str(e)
                if msg.startswith("Cannot add to path"):
                   raise ValueError(f"Cannot add to path: {path}")
                elif msg.startswith("Index out of bounds"):
                   raise ValueError(f"Index out of bounds: {path}")
                raise
            raise

    return new_state"""


content = re.sub(apply_state_differential_re, new_helpers_and_dispatch, content, flags=re.DOTALL)


with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
