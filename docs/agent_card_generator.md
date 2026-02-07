# Agent Card Generator

The Agent Card Generator is a utility within `coreason-manifest` designed to bridge the gap between technical definitions and human-readable documentation. It adheres to the "Glass Box" philosophy, ensuring that the transparency of an Agent's configuration is accessible to non-technical stakeholders such as Compliance Officers, Product Managers, and End Users.

By generating a standardized Markdown "Agent Card" directly from the `ManifestV2` object, this tool guarantees that the documentation never drifts from the actual code.

## Key Features

*   **Automated Generation:** Converts `ManifestV2` objects into formatted Markdown.
*   **Standardized Sections:** Automatically populates sections for Metadata, Financials, Governance, and API Contracts.
*   **Robustness:** Gracefully handles missing optional fields (e.g., Resources, Evaluation metrics).
*   **Zero Dependencies:** Implemented using standard Python string manipulation, keeping the package lightweight.

## Usage

The utility is exported as `render_agent_card` from the root package.

```python
from coreason_manifest import render_agent_card, load

# 1. Load your manifest (e.g., from a YAML file)
manifest = load("my_agent.yaml")

# 2. Generate the card
markdown_card = render_agent_card(manifest)

# 3. Save or display the markdown
print(markdown_card)
```

## Output Structure

The generated Agent Card includes the following sections:

1.  **Header:** Agent Name, Version, Role, and Creation Date.
2.  **Description:** The Agent's backstory or description, formatted as a blockquote.
3.  **Resource & Cost Profile:** (Optional) Details on the Model ID, Pricing (Input/Output costs), and Context Window size.
4.  **Governance & Safety:** (Optional) Risk Level and a list of active policies enforced on the Agent.
5.  **API Interface:** Markdown tables detailing the Input and Output schemas, including field names, types, requirements, and descriptions.
6.  **Evaluation Standards:** (Optional) Grading rubrics and Service Level Agreements (SLAs) defined for the agent.

## Example Output

```markdown
# ResearchAssistant (v1.0.0)
**Role:** Senior Researcher | **Created:** 2023-10-27

> You are an expert researcher capable of finding detailed information on any topic.

## 💰 Resource & Cost Profile
- **Model:** openai/gpt-4
- **Pricing:** $10.0 / 1M Input | $30.0 / 1M Output
- **Context Window:** 128000 tokens

## 🛡️ Governance & Safety
- **Risk Level:** standard
- **Active Policies:**
  - No PII allowed in output
  - Must cite sources

## 🔌 API Interface

### Inputs
| Field Name | Type | Required? | Description |
| --- | --- | --- | --- |
| `query` | `string` | Yes | The research topic |
| `depth` | `integer` | No | Search depth (1-5) |

### Outputs
| Field Name | Type | Required? | Description |
| --- | --- | --- | --- |
| `summary` | `string` | No | A summary of findings |

## 🧪 Evaluation Standards
- **Grading Rubric:**
  - **accuracy:** Must be factual (Threshold: 0.9)
- **SLA:** 5000ms latency
```
