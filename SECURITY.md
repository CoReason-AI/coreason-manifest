# Security Policy

## Supported Versions

Use the latest version of `coreason-manifest` to ensure you have the latest security patches.

| Version | Supported |
| ------- | ------------------ |
| 0.21.x  | :white_check_mark: |
| < 0.21.0| :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities to `security@coreason.ai`.

## Known Security Considerations

### 1. Arbitrary Code Execution (ACE) via CLI

The `coreason` CLI executes Python code when loading agent definitions from `.py` files (e.g., `coreason inspect my_agent.py:agent`). This is by design to support dynamic manifest generation via `AgentBuilder`.

**Risk:** Loading an untrusted Python file can execute malicious code on your machine.
**Mitigation:** Only run `coreason` CLI commands on files you trust. Treat `.py` manifest definitions as executable code.

### 2. Remote Code Execution (RCE) via Schema

The `ManifestV2` schema supports defining executable logic:
- `LogicStep`: Contains raw Python code in the `code` field.
- `MCPServerDefinition`: Contains system commands in `command` and `args` fields.
- `SkillDefinition`: References scripts via `scripts` field.

**Risk:** If a runtime implementation blindly executes these fields from an untrusted manifest, it creates an RCE vulnerability.
**Mitigation:** Runtime implementations must:
- Sanitize and sandbox execution of `LogicStep` code.
- Require explicit user approval before executing `MCPServerDefinition` commands.
- Validate `scripts` paths against an allowlist or sandbox.

### 3. Path Traversal Risks

While `$ref` resolution is protected by `ReferenceResolver` (Jail), other URI fields are not automatically validated by the library:
- `ToolRequirement.uri`
- `ToolDefinition.uri`
- `SkillDefinition.instructions_uri`

**Risk:** An attacker could reference local files (e.g., `file:///etc/passwd`) or internal network resources.
**Mitigation:** Runtime implementations must validate all URIs before access.

### 4. Denial of Service (DoS)

The `GraphTopology` allows cycles (loops). An infinite loop in a graph recipe could cause resource exhaustion.
**Mitigation:** Runtime implementations should enforce execution limits (e.g., `max_steps`, timeouts).
