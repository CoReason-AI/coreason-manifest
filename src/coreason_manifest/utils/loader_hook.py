
def _install_audit_hook() -> None:
    global _HOOK_INSTALLED
    if _HOOK_INSTALLED:
        return

    # We define the inner hook function
    def hook(event: str, args: tuple[Any, ...]) -> None:
        jail_root = _jail_root_var.get()
        if not jail_root:
            return

        if event == "open":
            path, mode, flags = args
            # We strictly only care about string paths (file system).
            # If path is an int (fd), we can't easily check it here without fstat/etc,
            # and audit hook arguments are just the arguments passed to open().
            if isinstance(path, (str, Path)):
                try:
                    file_path = Path(path).resolve()

                    # 1. If inside jail, it's allowed.
                    if file_path.is_relative_to(jail_root.resolve()):
                        return

                    # 2. If outside jail, we must be careful.
                    # Python runtime needs to open many files (stdlib, .pyc, encodings, etc.)
                    # Blocking all outside opens will break Python.

                    # However, the requirement is "monitor and block unauthorized file system access ... reducing reliance on custom IO blocking".
                    # And "ensure no runtime execution logic leaks into the spec/ directory" (unrelated but context).

                    # "Implement sys.audit hooks within the loader as a safer, more Pythonic way to monitor and block unauthorized file system access during dynamic agent loading"

                    # During "dynamic agent loading" (which happens inside `_execute_jailed_module` context),
                    # the agent code runs `exec(content, exec_globals)`.
                    # If that code tries to `open('/etc/passwd')`, it should be blocked.

                    # But if that code does `import os`, Python might open `.../lib/python3.12/os.py`.

                    # We can filter based on the extension? .py files are handled by import system (which uses SandboxedPathFinder).
                    # But `open()` hook is hit even for imports if standard loader is used (which we block for jail, but allow for stdlib).

                    # If we are in the jail context, we want to forbid opening NON-PYTHON files outside the jail.
                    # Or specific extensions? No, that's blacklist.

                    # Whitelist approach:
                    # 1. Inside Jail -> OK
                    # 2. Inside sys.base_prefix / sys.base_exec_prefix (Stdlib) -> OK
                    # 3. Inside site-packages? Maybe.

                    # Let's verify if path is relative to sys.base_prefix
                    # We need to handle resolved paths.

                    # Be careful with virtualenvs (sys.prefix != sys.base_prefix sometimes)

                    prefixes = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), Path(sys.exec_prefix).resolve(), Path(sys.base_exec_prefix).resolve()]

                    for prefix in prefixes:
                        if file_path.is_relative_to(prefix):
                            return

                    # If we are here, it is outside jail and outside python runtime.
                    # Raise SecurityViolation!

                    raise SecurityViolationError(f"Unauthorized file access blocked by audit hook: {path}")

                except (ValueError, RuntimeError):
                    # Path resolution failed or similar. Safe to block?
                    # If we can't resolve it, we can't verify it. Block.
                    raise SecurityViolationError(f"Unauthorized file access blocked (resolution failed): {path}")
                except SecurityViolationError:
                    raise
                except Exception:
                    # If any other error (e.g. permission denied during resolve?), we might ignore or block.
                    # Better to block in security context.
                    # But let's just pass for now to avoid crashing benign system calls if any.
                    pass

    try:
        sys.addaudithook(hook)
        _HOOK_INSTALLED = True
    except Exception:
        # Might fail on some implementations or if already audited (though addaudithook allows multiple hooks)
        pass
