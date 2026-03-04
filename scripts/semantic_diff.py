import json
import subprocess
import sys

from deepdiff import DeepDiff


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python semantic_diff.py <git_ref> <file_path>")
        sys.exit(1)

    git_ref = sys.argv[1]
    file_path = sys.argv[2]

    try:
        base_file_content = subprocess.check_output(["git", "show", f"{git_ref}:{file_path}"]).decode("utf-8")  # noqa: S603, S607
        base_json = json.loads(base_file_content)
    except subprocess.CalledProcessError:
        print(f"Warning: Could not fetch {file_path} from {git_ref}. Assuming new file.")
        base_json = {}

    with open(file_path, encoding="utf-8") as f:
        local_json = json.loads(f.read())

    diff = DeepDiff(base_json, local_json, ignore_order=True)

    if "dictionary_item_removed" in diff or "type_changes" in diff:
        print("Error: Backward-breaking schema change detected!")
        print(diff)
        sys.exit(1)

    print("Schema change is backward-compatible.")
    sys.exit(0)


if __name__ == "__main__":
    main()
