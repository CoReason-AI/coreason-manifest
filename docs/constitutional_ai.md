# Constitutional AI Schemas

Coreason V2 introduces **Constitutional AI** capabilities, allowing Recipes to declare a set of high-level principles ("Laws") and hard constraints ("Sentinel Rules") that govern the agent's behavior.

This schema is designed to support **Chain-of-Thought Critique Loops**, where the runtime injects these principles into the agent's system prompt or uses them in a dedicated `EvaluatorNode` to critique and refine responses.

## The Constitution

A `Constitution` is a structured collection of:
1.  **Laws**: Semantic principles for behavioral guidance (Soft Constraints).
2.  **Sentinel Rules**: Regex patterns for immediate blocking (Hard Constraints).

It is attached to the `PolicyConfig` of a Recipe.

### Example Usage

```python
from coreason_manifest.spec.v2.recipe import RecipeDefinition, PolicyConfig
from coreason_manifest.spec.v2.constitution import Constitution, Law, SentinelRule, LawCategory, LawSeverity

# 1. Define the Constitution
constitution = Constitution(
    laws=[
        Law(
            id="GCP.4",
            category=LawCategory.DOMAIN,
            text="Do not provide medical advice. Refer to a qualified professional.",
            severity=LawSeverity.CRITICAL,
            reference_url="https://fda.gov/guidance"
        ),
        Law(
            id="Brand.1",
            category=LawCategory.TENANT,
            text="Always maintain a professional and empathetic tone.",
            severity=LawSeverity.MEDIUM
        )
    ],
    sentinel_rules=[
        SentinelRule(
            id="SR-001",
            pattern=r"sk-[a-zA-Z0-9]{48}",
            description="Block OpenAI API keys from leaking."
        )
    ]
)

# 2. Attach to Policy
recipe = RecipeDefinition(
    ...,
    policy=PolicyConfig(
        max_retries=3,
        constitution=constitution,
        # Legacy field 'safety_preamble' is now optional and can be overridden by the Constitution
    )
)
```

## Schema Reference

### `Constitution`
| Field | Type | Description |
| :--- | :--- | :--- |
| `laws` | `list[Law]` | List of semantic principles. |
| `sentinel_rules` | `list[SentinelRule]` | List of regex patterns for hard filtering. |

### `Law`
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier (e.g., 'GCP.4'). |
| `category` | `LawCategory` | `Universal`, `Domain`, or `Tenant`. |
| `text` | `str` | The content of the law/principle. |
| `severity` | `LawSeverity` | `Low`, `Medium`, `High`, `Critical`. |
| `reference_url` | `str \| None` | Source of truth URL. |

### `SentinelRule`
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Rule ID. |
| `pattern` | `str` | Regex pattern to match. |
| `description` | `str` | Why this pattern is blocked. |

## Integration with Runtime

When a Recipe with a `Constitution` is executed:
1.  **System Prompt Injection**: The runtime can format the `laws` into a text block (e.g., "OPERATIONAL GUIDELINES") and inject it into the `AgentNode`'s context.
2.  **Evaluator Loops**: An `EvaluatorNode` can be configured to use the `Constitution` as its `evaluation_profile`. The Judge LLM will then score the agent's output against each `Law`.
3.  **Input/Output Filtering**: The runtime's Interception Layer can compile the `sentinel_rules` into a regex engine to block requests or redaction responses that match the patterns.
