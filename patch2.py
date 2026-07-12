import re

with open("scripts/generate_cross_language_bindings.py", "r") as f:
    content = f.read()

# Replace the specific lines inside `def main()` that were causing undefined variable errors
content = re.sub(
    r"_sync_versions\(project_root, override_version=args\.version\)\n\s+_update_lockfiles\(project_root\)",
    r"# _sync_versions(project_root, override_version=args.version)\n    # _update_lockfiles(project_root)",
    content,
    flags=re.MULTILINE
)

with open("scripts/generate_cross_language_bindings.py", "w") as f:
    f.write(content)
