import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Fix loop variable binding issue:
content = content.replace('''
        PATCH_DISPATCH = {
            "add": lambda: _apply_patch_add(target, last_part, patch.value),
            "remove": lambda: _apply_patch_remove(target, last_part),
            "replace": lambda: _apply_patch_replace(target, last_part, patch.value),
            "copy": lambda: _apply_patch_copy_move(new_state, target, last_part, patch),
            "move": lambda: _apply_patch_copy_move(new_state, target, last_part, patch),
            "test": lambda: _apply_patch_test(target, last_part, patch.value),
        }
''', '''
        patch_op = patch.op
        patch_value = patch.value
        patch_from = getattr(patch, "from_path", None)
        # Using default arguments in lambdas to correctly bind loop variables
        PATCH_DISPATCH = {
            "add": lambda t=target, lp=last_part, v=patch_value: _apply_patch_add(t, lp, v),
            "remove": lambda t=target, lp=last_part: _apply_patch_remove(t, lp),
            "replace": lambda t=target, lp=last_part, v=patch_value: _apply_patch_replace(t, lp, v),
            "copy": lambda ns=new_state, t=target, lp=last_part, p=patch: _apply_patch_copy_move(ns, t, lp, p),
            "move": lambda ns=new_state, t=target, lp=last_part, p=patch: _apply_patch_copy_move(ns, t, lp, p),
            "test": lambda t=target, lp=last_part, v=patch_value: _apply_patch_test(t, lp, v),
        }
''')

# Fix raised exceptions in `apply_state_differential`:
old_except = '''
            except ValueError as e:
                # We preserve the original exception messaging strategy to not break any possible external test suite reliance on the exact strings in apply_state_differential.
                if patch.op in ("remove", "replace") and "Patch test operation failed" not in str(e) and "Index out of bounds" not in str(e) and "Cannot extract from end of array" not in str(e):
                   raise ValueError(f"Cannot {patch.op} at path {path}: {e}") from e
                if patch.op == "remove":
                    # Special case, old code used from path: {e} and from path {path}: {e} for remove/replace.
                    raise ValueError(f"Cannot remove from path {path}: {e}") from e
                if patch.op == "replace":
                    raise ValueError(f"{e}") from e
                if patch.op in ("copy", "move"):
                    # Exception was: raise ValueError(f"Cannot copy/move to path: {path}") or f"Index out of bounds: {path}"
                    msg = str(e)
                    if msg.startswith("Cannot copy/move to path"):
                        raise ValueError(f"Cannot copy/move to path: {path}") from e
                        raise ValueError(f"Cannot copy/move to path: {path}") from e
                    if msg.startswith("Index out of bounds"):
                        raise ValueError(f"Index out of bounds: {path}") from e
                        raise ValueError(f"Index out of bounds: {path}") from e
                    raise
                if patch.op == "add":
                    msg = str(e)
                    if msg.startswith("Cannot add to path"):
                       raise ValueError(f"Cannot add to path: {path}") from e
                    if msg.startswith("Index out of bounds"):
                       raise ValueError(f"Index out of bounds: {path}") from e
                    raise
                raise
'''

new_except = '''
            except ValueError as e:
                # We preserve the original exception messaging strategy to not break any possible external test suite reliance on the exact strings in apply_state_differential.
                if patch.op in ("remove", "replace") and "Patch test operation failed" not in str(e) and "Index out of bounds" not in str(e) and "Cannot extract from end of array" not in str(e):
                   raise ValueError(f"Cannot {patch.op} at path {path}: {e}") from e
                if patch.op == "remove":
                    # Special case, old code used from path: {e} and from path {path}: {e} for remove/replace.
                    raise ValueError(f"Cannot remove from path {path}: {e}") from e
                if patch.op == "replace":
                    raise ValueError(f"{e}") from e
                if patch.op in ("copy", "move"):
                    # Exception was: raise ValueError(f"Cannot copy/move to path: {path}") or f"Index out of bounds: {path}"
                    msg = str(e)
                    if msg.startswith("Cannot copy/move to path"):
                        raise ValueError(f"Cannot copy/move to path: {path}") from e
                    if msg.startswith("Index out of bounds"):
                        raise ValueError(f"Index out of bounds: {path}") from e
                    raise
                if patch.op == "add":
                    msg = str(e)
                    if msg.startswith("Cannot add to path"):
                       raise ValueError(f"Cannot add to path: {path}") from e
                    if msg.startswith("Index out of bounds"):
                       raise ValueError(f"Index out of bounds: {path}") from e
                    raise
                raise
'''

content = content.replace(old_except, new_except)

with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
