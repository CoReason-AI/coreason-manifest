# Enforcing Governance

Autonomous multi-agent systems require firm boundaries to mitigate security vulnerabilities, financial risks, and unpredictable behavior. `coreason_manifest` achieves this through strict, typed `Governance` models that act as an interceptor for every `Node` execution.

This guide demonstrates how to configure granular operational and access controls using `ToolAccessPolicy` and `OperationalPolicy`.

## The Governance Wrapper

Governance in `coreason_manifest` is fundamentally an immutable layer. By defining a `Governance` object and assigning it to an `AgentNode`, you establish strict conditions for execution that cannot be circumvented dynamically.

!!! warning "Arbitrary Execution Boundaries"
    When integrating third-party tools or dynamic LLM outputs, you are introducing the potential for arbitrary code execution. `ToolAccessPolicy` and `OperationalPolicy` must be rigidly defined to contain these risks.

## Implementing Tool Access Restrictions

The `ToolAccessPolicy` dictates which tools an agent can invoke. This prevents a "research agent" from inadvertently executing a "database drop" command.

```python
from coreason_manifest.core.oversight.governance import Governance, ToolAccessPolicy
from coreason_manifest.core.workflow.nodes import AgentNode

# Define allowed tools for a financial analyst
read_only_tools = ["fetch_market_data", "analyze_trends", "read_reports"]

policy = ToolAccessPolicy(
    allowed_tools=read_only_tools,
    require_approval=["execute_trade"] # Explicitly demands human intervention
)

analyst_node = AgentNode(
    id="market_analyst",
    system_prompt="Analyze market trends.",
    governance=Governance(tool_access=policy)
)
```

## Configuring Operational Limits

The `OperationalPolicy` enforces traffic limits, financial budgets, and payload sizes. It acts as a safety net against "runaway loops" where an agent repeatedly queries an API, consuming massive resources.

```python
from coreason_manifest.core.oversight.governance import OperationalPolicy

# Define constraints for a single execution cycle
ops_policy = OperationalPolicy(
    max_tokens=5000,          # Halt execution if exceeded
    max_duration_seconds=30,  # Timeout threshold
    max_api_calls=15,         # Throttle external tool invocations
    max_cost_usd=0.50         # Halt execution if LLM API cost exceeds budget
)

# Apply to a Node
scraper_node = AgentNode(
    id="web_scraper",
    system_prompt="Crawl the target URL for relevant articles.",
    governance=Governance(operational_limits=ops_policy)
)
```

## Handling Governance Exceptions

When an agent violates a governance policy, `coreason_manifest` throws a specific exception (e.g., `BudgetExceededException`, `UnauthorizedToolException`). These exceptions must be caught and handled gracefully by the `GraphFlow` architecture or a higher-level supervisor.

!!! tip "Resilience Strategies"
    You can map policy violations to specific error-handling routines. Proceed to [Resilience Strategies](resilience_strategies.md) to learn how to recover from governance-induced halts.