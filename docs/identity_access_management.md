# Identity & Access Management (IAM)

The **Identity & Access Management (IAM)** schema transforms the Coreason Manifest from a static definition into a security-aware **Gatekeeper**. It allows a Recipe to strictly declare *who* is allowed to execute it (Access Control) and *what* user data it requires for context (Context Injection).

This ensures the Runtime Engine can enforce permissions **before** execution starts, preventing unauthorized access and ensuring necessary data is available.

## Key Concepts

### 1. Access Control (RBAC)
Defines the authorization rules for executing a Recipe.

*   **`AccessScope`**: Broad permission levels.
    *   `PUBLIC`: Accessible to anyone (unauthenticated).
    *   `AUTHENTICATED`: Any logged-in user.
    *   `INTERNAL`: Restricted to internal organization members.
    *   `ADMIN`: Restricted to system administrators.

*   **`required_roles`**: A list of specific role strings (e.g., `"finance_admin"`, `"editor"`).
    *   Logic: **OR** (User must have at least one of these roles).

*   **`required_permissions`**: A list of specific permission strings (e.g., `"read:report"`, `"write:budget"`).
    *   Logic: **AND** (User must have ALL of these permissions).

### 2. Context Injection
Defines what user-specific data the Agent needs to perform its task.

*   **`inject_user_profile`**: If `True`, injects the user's ID, Name, and Email into the system prompt.
*   **`inject_locale_info`**: If `True`, injects the user's Timezone and Locale/Language.

### 3. Privacy
Controls how sensitive user data is handled.

*   **`anonymize_pii`**: If `True` (default), the runtime replaces real names and emails with hashes or aliases before sending them to the LLM, protecting user privacy.

## Schema Definition

The configuration is defined in the `IdentityRequirement` model within `src/coreason_manifest/spec/v2/identity.py`.

```python
class IdentityRequirement(CoReasonBaseModel):
    # Access Control
    min_scope: AccessScope = Field(AccessScope.AUTHENTICATED)
    required_roles: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)

    # Context Injection
    inject_user_profile: bool = Field(False)
    inject_locale_info: bool = Field(True)

    # Privacy
    anonymize_pii: bool = Field(True)
```

## Usage in Recipes

The `RecipeDefinition` now includes an optional `identity` field.

### Example: Restricted Finance Report Generator

This recipe requires the user to be an authenticated `finance_admin` and needs their timezone for accurate date formatting.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Quarterly Financial Report"
  version: "1.0.0"

# --- Identity Configuration ---
identity:
  min_scope: "authenticated"
  required_roles:
    - "finance_admin"
    - "cfo"
  required_permissions:
    - "read:financials"
    - "generate:report"
  inject_user_profile: true
  inject_locale_info: true
  anonymize_pii: false  # Need real name for report signature

interface:
  inputs:
    quarter: { type: "string", enum: ["Q1", "Q2", "Q3", "Q4"] }
    year: { type: "integer" }
  outputs:
    report_url: { type: "string" }

topology:
  # ... graph definition ...
```

### Example: Public FAQ Bot

This recipe is open to everyone and doesn't need user details, but benefits from knowing the locale for language selection.

```yaml
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: "Customer Support FAQ"
  version: "1.0.0"

identity:
  min_scope: "public"
  inject_user_profile: false
  inject_locale_info: true  # To respond in the user's language
  anonymize_pii: true

# ... rest of definition ...
```

## Integration with Runtime

When the Runtime Engine receives a request to execute a Recipe:

1.  **Check `identity.min_scope`**: Is the user's session valid for this scope?
2.  **Check `identity.required_roles`**: Does the user have at least one of the listed roles?
3.  **Check `identity.required_permissions`**: Does the user have ALL of the listed permissions?
4.  **Prepare Context**:
    *   If `inject_user_profile` is True, fetch user details.
    *   If `inject_locale_info` is True, fetch locale settings.
    *   If `anonymize_pii` is True, hash PII fields.
5.  **Inject**: Add the prepared context to the System Prompt preamble before invoking the Agent.
