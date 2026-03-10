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
        base_file_content = subprocess.check_output(  # noqa: S603
            ["git", "show", f"{git_ref}:{file_path}"],  # noqa: S607
            stderr=subprocess.PIPE,
        ).decode("utf-8")
        base_json = json.loads(base_file_content)
    except subprocess.CalledProcessError as e:
        stderr_output = e.stderr.decode("utf-8") if e.stderr else ""
        if "exists on disk, but not in" in stderr_output or "does not exist" in stderr_output:
            print(f"Warning: Could not fetch {file_path} from {git_ref}. Assuming new file.")
            base_json = {}
        else:
            print(f"Critical Error: Git ref {git_ref} could not be resolved. Git stderr: {stderr_output.strip()}")
            sys.exit(1)

    with open(file_path, encoding="utf-8") as f:
        local_json = json.loads(f.read())

    diff = DeepDiff(base_json, local_json, ignore_order=True)

    if "dictionary_item_removed" in diff or "type_changes" in diff:
        print("Error: Backward-breaking schema change detected!")
        print(diff)
        sys.exit(1)

    if "iterable_item_added" in diff:
        for path in diff["iterable_item_added"]:
            if "['required']" in path:
                print(f"Error: Backward-breaking schema change detected! A new required field was added: {path}")
                sys.exit(1)

    if "dictionary_item_added" in diff:
        for path in diff["dictionary_item_added"]:
            if "['required']" in path:
                print(f"Error: Backward-breaking schema change detected! A new required field was added: {path}")
                sys.exit(1)

    print("Schema change is backward-compatible.")
    sys.exit(0)


if __name__ == "__main__":
    main()
