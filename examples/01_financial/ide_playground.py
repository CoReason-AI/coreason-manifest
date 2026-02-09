# examples/ide_playground.py
import json
import os
import sys
from typing import Any

# Ensure the package is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pydantic import BaseModel, Field

from coreason_manifest.builder import AgentBuilder, CapabilityType, TypedCapability
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    InterfaceDefinition,
    ManifestMetadata,
    ManifestV2,
    Workflow,
)
from coreason_manifest.spec.v2.resources import (
    Currency,
    ModelProfile,
    PricingUnit,
    RateCard,
)
from coreason_manifest.utils.docs import render_agent_card
from coreason_manifest.utils.mock import generate_mock_output
from coreason_manifest.utils.viz import generate_mermaid_graph

# --- 1. Define Contracts (Pydantic Models) ---


class FinancialDataInput(BaseModel):
    company_ticker: str = Field(..., description="The stock ticker symbol (e.g., AAPL).")
    report_year: int = Field(..., description="The fiscal year for the report.")


class FinancialData(BaseModel):
    revenue: float = Field(..., description="Total revenue in millions.")
    net_income: float = Field(..., description="Net income in millions.")
    debt: float = Field(..., description="Total debt in millions.")
    currency: str = Field("USD", description="Currency of the financial data.")


class TrendAnalysis(BaseModel):
    growth_rate: float = Field(..., description="Year-over-year growth rate percentage.")
    sentiment: str = Field(..., description="Market sentiment (Bullish/Bearish/Neutral).")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 to 100.")


class InvestmentSummary(BaseModel):
    recommendation: str = Field(..., description="Investment recommendation (Buy/Sell/Hold).")
    summary_text: str = Field(..., description="Detailed markdown summary of the analysis.")
    disclaimer: str = Field(..., description="Legal disclaimer.")


# --- 2. Build the Agent System ---


def build_financial_analyst() -> ManifestV2:
    """
    Constructs the 'Financial Analyst' Agent System (Manifest).
    This simulates a developer using the Builder SDK to define a complex agent.
    """

    # -- Step 1: Fetcher Agent (Micro-agent for tool execution) --
    fetcher_builder = AgentBuilder(name="FetcherAgent")
    fetcher_builder.with_capability(
        TypedCapability(
            name="fetch_financial_data",
            description="Fetches raw financial data for a company.",
            input_model=FinancialDataInput,
            output_model=FinancialData,
            capability_type=CapabilityType.ATOMIC,
        )
    )
    # Extract the definition
    fetcher_def = fetcher_builder.build().definitions["FetcherAgent"]
    assert isinstance(fetcher_def, AgentDefinition)

    # -- Step 2: Analyzer Agent (LLM with Resources & Governance) --
    analyzer_builder = AgentBuilder(name="AnalyzerAgent")
    analyzer_builder.with_model("gpt-4-turbo")
    analyzer_builder.with_system_prompt(
        "You are a Senior Financial Analyst. Policy: No investment advice. Analyze the data neutrally."
    )
    analyzer_builder.with_capability(
        TypedCapability(
            name="analyze_trends",
            description="Analyzes financial trends and risk.",
            input_model=FinancialData,
            output_model=TrendAnalysis,
            capability_type=CapabilityType.GRAPH,
        )
    )
    # Extract definition
    analyzer_def = analyzer_builder.build().definitions["AnalyzerAgent"]
    assert isinstance(analyzer_def, AgentDefinition)

    # Add Resources (RateCard) to Analyzer
    # Note: AgentBuilder doesn't expose resources directly yet, so we modify the definition.
    # We must replace the object because Pydantic models are immutable/frozen by default in this codebase (frozen=True).
    # Wait, check if frozen=True.
    # Yes, ConfigDict(frozen=True). So we must use model_copy(update=...)

    rate_card = RateCard(unit=PricingUnit.TOKEN_1M, currency=Currency.USD, input_cost=5.00, output_cost=15.00)
    resources = ModelProfile(provider="openai", model_id="gpt-4-turbo", pricing=rate_card)

    analyzer_def = analyzer_def.model_copy(update={"resources": resources})

    # -- Step 3: Writer Agent (Summary Generation) --
    writer_builder = AgentBuilder(name="WriterAgent")
    writer_builder.with_model("claude-3-opus")
    writer_builder.with_capability(
        TypedCapability(
            name="generate_summary",
            description="Generates a final report.",
            input_model=TrendAnalysis,
            output_model=InvestmentSummary,
            capability_type=CapabilityType.ATOMIC,
        )
    )
    writer_def = writer_builder.build().definitions["WriterAgent"]
    assert isinstance(writer_def, AgentDefinition)

    # -- Step 4: Construct the Master Manifest (The Recipe) --

    # Define the workflow topology
    workflow = Workflow(
        start="step_fetch",
        steps={
            "step_fetch": AgentStep(id="step_fetch", agent="FetcherAgent", next="step_analyze"),
            "step_analyze": AgentStep(id="step_analyze", agent="AnalyzerAgent", next="step_write"),
            "step_write": AgentStep(
                id="step_write",
                agent="WriterAgent",
                next=None,  # End of workflow
            ),
        },
    )

    # Combine everything into ManifestV2
    return ManifestV2(
        kind="Recipe",  # It orchestrates multiple agents
        metadata=ManifestMetadata(
            name="Financial Analyst Agent",
            version="1.0.0",
        ),
        # The interface of the *Workflow* itself matches the input of the first step
        # and output of the last step.
        interface=InterfaceDefinition(inputs=fetcher_def.interface.inputs, outputs=writer_def.interface.outputs),
        definitions={"FetcherAgent": fetcher_def, "AnalyzerAgent": analyzer_def, "WriterAgent": writer_def},
        workflow=workflow,
    )


# --- 3. Simulation Logic ---


def simulate_execution(agent: ManifestV2, inputs: dict[str, Any]) -> None:
    """
    Simulates the local execution loop of the agent.
    """
    print(f"\n🚀 Starting Agent: {agent.metadata.name}...")
    print(f"📥 Inputs: {json.dumps(inputs, indent=2)}")

    current_step_id: str | None = agent.workflow.start
    total_cost = 0.0

    while current_step_id:
        step = agent.workflow.steps.get(current_step_id)
        if not step:
            print(f"❌ Error: Step '{current_step_id}' not found.")
            break

        print(f"\n🔄 Executing Step: {current_step_id}")

        # Resolve the Agent Definition for this step
        if isinstance(step, AgentStep):
            agent_id = step.agent
            agent_def = agent.definitions.get(agent_id)

            if isinstance(agent_def, AgentDefinition):
                print(f"   🤖 Agent: {agent_def.name} ({agent_def.role})")

                # Mock the output
                # In a real engine, we would pass the output of the previous step as input here.
                # For simulation, we just generate mock data conforming to the output schema.

                mock_result = generate_mock_output(agent_def, seed=42)  # Seed for consistency

                print(f"   ✅ Result: {json.dumps(mock_result, indent=2)}")

                # Calculate Mock Cost (if RateCard exists)
                if agent_def.resources and agent_def.resources.pricing:
                    pricing = agent_def.resources.pricing
                    # Fake usage
                    input_usage = 0.0005  # 500 tokens
                    output_usage = 0.0002  # 200 tokens
                    step_cost = (pricing.input_cost * input_usage) + (pricing.output_cost * output_usage)
                    total_cost += step_cost
                    # print(f"   💰 Step Cost: ${step_cost:.4f}")

            else:
                print(f"   ⚠️ Definition for {agent_id} not found or invalid.")
        else:
            print(f"   i️ Non-Agent Step Type: {step.type}")

        # Move to next step
        current_step_id = step.next if hasattr(step, "next") else None

    print(f"\n🏁 Execution Complete. Cost Estimate: ${total_cost:.4f}")


# --- 4. Main Entry Point ---


def main() -> None:
    # 1. Build
    print("🔨 Building Financial Analyst Agent...")
    agent_manifest = build_financial_analyst()

    # 2. Compile Artifacts
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Documentation
    doc_path = os.path.join(output_dir, "agent_card.md")
    print(f"📄 Generating Documentation: {doc_path}")
    with open(doc_path, "w") as f:
        f.write(render_agent_card(agent_manifest) + "\n")

    # Visualization
    viz_path = os.path.join(output_dir, "agent_flow.mmd")
    print(f"📊 Generating Visualization: {viz_path}")
    with open(viz_path, "w") as f:
        f.write(generate_mermaid_graph(agent_manifest) + "\n")

    # 3. Simulate
    input_data = {"company_ticker": "AAPL", "report_year": 2024}
    simulate_execution(agent_manifest, input_data)


if __name__ == "__main__":
    main()
