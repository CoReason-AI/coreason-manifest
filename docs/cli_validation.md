# CLI Validation Command

The `validate` command is a static analysis tool included in the `coreason-manifest` CLI. It allows developers and CI/CD pipelines to verify that agent definition files conform to the strict Coreason Agent Manifest (CAM) schema without executing the agent.

## Usage

```bash
coreason validate <file_path> [options]
```

### Arguments

*   `file_path`: Path to the static definition file. Supported extensions are `.json`, `.yaml`, and `.yml`.

### Options

*   `--json`: If specified, the command will output the validated, normalized JSON structure of the agent to `stdout` upon success. This is useful for piping the valid definition to other tools.

## Validation Logic

The command employs an intelligent validation strategy:

1.  **Format Detection:** It loads the file using the appropriate parser (`json` or `PyYAML`).
2.  **Schema Detection:**
    *   If the root object contains an `apiVersion` key, it validates against the full **`ManifestV2`** schema (including workflow, policy, etc.).
    *   Otherwise, it attempts to validate against the standalone **`AgentDefinition`** schema.
3.  **Strict Validation:** It uses Pydantic to enforce type safety, required fields, and constraints.

## Output & Exit Codes

### Success
If validation succeeds, the command prints a success message to `stdout` and exits with code **0**.

```text
✅ Valid Agent: ResearchAssistant (v1.0.0)
```

If `--json` is used, the full JSON object follows.

### Failure
If validation fails, the command prints formatted error messages to `stdout` and exits with code **1**.

```text
❌ Validation Failed:
  • workflow -> steps -> step-1: Input tag 'unknown_type' found using 'type' does not match any of the expected tags: 'agent', 'logic', 'council', 'switch'
```

### Errors
For file not found, permission errors, or malformed JSON/YAML (parsing errors), the command prints an error message to `stderr` and exits with code **1**.

## CI/CD Integration

The `validate` command is designed for use in CI pipelines (e.g., GitHub Actions, GitLab CI).

Example GitHub Action step:

```yaml
- name: Validate Agent Manifests
  run: |
    pip install coreason-manifest
    coreason validate agent.yaml
```
