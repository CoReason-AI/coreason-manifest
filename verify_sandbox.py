import sys
import shutil
import os
from pathlib import Path
from coreason_manifest.utils.loader import sandbox_context, load_agent_from_ref
from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError

def verify_sandboxed_path_finder():
    base = Path("verify_sandbox")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    jail = base / "jail"
    jail.mkdir()

    # 1. Test allowed import
    (jail / "utils.py").write_text("def helper(): return 'helped'")
    (jail / "utils.py").chmod(0o600)
    (jail / "agent.py").write_text("import utils\nclass Agent:\n    def run(self): return utils.helper()")
    (jail / "agent.py").chmod(0o600)

    print("Testing allowed import...")
    agent_cls = load_agent_from_ref("agent.py:Agent", root_dir=jail)
    agent = agent_cls()
    assert agent.run() == "helped"
    print("Allowed import passed.")

    # 2. Test disallowed import (outside jail)
    outside = base / "outside"
    outside.mkdir()
    (outside / "forbidden.py").write_text("SECRET = 'fail'")

    (jail / "malicious.py").write_text("import forbidden\nclass Agent:\n    pass")
    (jail / "malicious.py").chmod(0o600)

    # We must try to trick python into finding 'forbidden' via sys.path or something,
    # but since we are not adding 'outside' to sys.path, normal python wouldn't find it anyway.
    # The SandboxedPathFinder only looks in jail.

    # However, if we symlink it into jail?
    (jail / "forbidden_link.py").symlink_to(outside / "forbidden.py")

    print("Testing symlink escape...")
    (jail / "symlink_agent.py").write_text("import forbidden_link\nclass Agent:\n    pass")
    (jail / "symlink_agent.py").chmod(0o600)

    try:
        load_agent_from_ref("symlink_agent.py:Agent", root_dir=jail)
        print("ERROR: Symlink escape check FAILED. Should have raised SecurityJailViolationError.")
        sys.exit(1)
    except SecurityJailViolationError as e:
        print(f"Symlink escape check passed: {e}")
    except ImportError as e:
        # If SandboxedPathFinder returns None (because it detected escape and returned None or raised),
        # then import fails.
        # But our Finder implementation raises SecurityJailViolationError inside find_spec if it finds it but it escapes.
        # If it returns None, then ModuleNotFoundError is raised.
        # Let's check our implementation.
        # Our implementation raises SecurityJailViolationError.
        print(f"Caught unexpected ImportError: {e}")
        # If find_spec returns None, it means it didn't find it or explicitly ignored it.
        # If we want strict blocking of symlinks that exist but point outside, we should ensure find_spec sees them.
        sys.exit(1)

    # 3. Test standard library shadowing
    print("Testing stdlib shadowing...")
    (jail / "os.py").write_text("x=1")
    (jail / "shadow_agent.py").write_text("import os\nclass Agent:\n    val = os.name")
    (jail / "shadow_agent.py").chmod(0o600)

    agent_cls = load_agent_from_ref("shadow_agent.py:Agent", root_dir=jail)
    # If it loaded local os, it would have x=1 and no 'name' (or different behavior).
    # Since we filter stdlib in find_spec, it should return None, and python should fall back to standard importer.
    # So 'import os' should get the real os module.
    assert agent_cls.val == os.name
    print("Stdlib shadowing passed.")

    print("All verification checks passed.")
    shutil.rmtree(base)

if __name__ == "__main__":
    verify_sandboxed_path_finder()
