# examples/02_pharma_launch/lipitor_strategy.py
import json
import os
import sys
from typing import Any, Literal

# Ensure the package is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pydantic import BaseModel, Field

from coreason_manifest.builder import AgentBuilder, CapabilityType, ManifestBuilder, TypedCapability
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    SwitchStep,
)

# --- 1. Define Contracts (The Domain Language) ---


class MarketData(BaseModel):
    """Raw market intelligence data."""
    region_code: str = Field(..., description="Geographic region code (e.g., 'US-EAST').")
    competitor_share: float = Field(..., description="Market share of Zocor/Pravachol (0.0-1.0).")
    cardiologist_density: int = Field(..., description="Number of cardiologists in the region.")


class StrategicAnalysis(BaseModel):
    """Analysis of the market situation."""
    opportunity_score: float = Field(..., description="0-100 score of potential revenue.")
    prescriber_sentiment: str = Field(..., description="Current sentiment (Skeptical/Open/Loyal).")
    knowledge_gap: bool = Field(..., description="True if physicians lack understanding of LDL potency.")


class EngagementStrategy(BaseModel):
    """The strategic decision for engagement."""
    action: Literal["DEPLOY_MSL", "DEPLOY_REP"] = Field(
        ..., description="The chosen engagement channel."
    )
    rationale: str = Field(..., description="Reasoning for the decision.")
    key_message: str = Field(..., description="The primary scientific or promotional message.")


class EngagementOutcome(BaseModel):
    """Result of the engagement."""
    prescriptions_lift: float = Field(..., description="Percentage increase in prescriptions.")
    feedback: str = Field(..., description="Qualitative feedback from the physician.")


# --- 2. Build the Agent System (The Manifest) ---


def build_launch_strategy_manifest():
    """
    Constructs the 'Lipitor Launch' Agent System.
    This encodes the strategic decision to use MSLs for high-knowledge-gap areas.
    """

    # -- Agent 1: Market Analyst --
    # Role: Ingests raw data and identifies the "Knowledge Gap".
    analyst_builder = AgentBuilder(name="MarketAnalyst")
    analyst_builder.with_system_prompt(
        "You are a pharmaceutical market analyst. "
        "Identify regions where physicians under-prescribe due to lack of scientific understanding."
    )
    analyst_builder.with_capability(
        TypedCapability(
            name="analyze_market",
            description="Analyzes market data to find knowledge gaps.",
            input_model=MarketData,
            output_model=StrategicAnalysis,
            capability_type=CapabilityType.ATOMIC,
        )
    )
    analyst_def = analyst_builder.build_definition()

    # -- Agent 2: Strategy Director --
    # Role: The Decision Maker. Decides between MSL (Science) and Rep (Promotion).
    director_builder = AgentBuilder(name="StrategyDirector")
    director_builder.with_system_prompt(
        "You are the Launch Director. POLICY: If 'knowledge_gap' is True, you MUST deploy 'DEPLOY_MSL'. "
        "Standard sales tactics are ineffective against scientific skepticism."
    )
    director_builder.with_capability(
        TypedCapability(
            name="decide_strategy",
            description="Decides the engagement channel based on analysis.",
            input_model=StrategicAnalysis,
            output_model=EngagementStrategy,
            capability_type=CapabilityType.ATOMIC,
        )
    )
    director_def = director_builder.build_definition()

    # -- Agent 3: Medical Science Liaison (MSL) --
    # Role: High-cost, high-value scientific peer.
    msl_builder = AgentBuilder(name="MedicalScienceLiaison")
    msl_builder.with_system_prompt(
        "You are a PhD-level scientist. Engage in deep peer-to-peer scientific dialogue about "
        "LDL-C reduction pathways. Do not 'sell'; educate."
    )
    msl_builder.with_capability(
        TypedCapability(
            name="engage_scientific",
            description="Conducts a scientific exchange.",
            input_model=EngagementStrategy,
            output_model=EngagementOutcome,
            capability_type=CapabilityType.ATOMIC,
        )
    )
    msl_def = msl_builder.build_definition()

    # -- Agent 4: Sales Representative --
    # Role: Standard promotional engagement.
    rep_builder = AgentBuilder(name="SalesRepresentative")
    rep_builder.with_system_prompt(
        "You are a professional sales representative. Focus on benefits, sampling, and relationship maintenance."
    )
    rep_builder.with_capability(
        TypedCapability(
            name="engage_promotional",
            description="Conducts a standard sales call.",
            input_model=EngagementStrategy,
            output_model=EngagementOutcome,
            capability_type=CapabilityType.ATOMIC,
        )
    )
    rep_def = rep_builder.build_definition()

    # -- Assemble the Manifest with Workflow --
    manifest_builder = ManifestBuilder("LipitorLaunchProtocol", version="1.0.0")

    # Add Agents
    manifest_builder.add_agent(analyst_def)
    manifest_builder.add_agent(director_def)
    manifest_builder.add_agent(msl_def)
    manifest_builder.add_agent(rep_def)

    # Add Steps
    # Step 1: Analyst
    manifest_builder.add_step(
        AgentStep(id="step_analyze", agent="MarketAnalyst", next="step_decide")
    )

    # Step 2: Director decides
    manifest_builder.add_step(
        AgentStep(id="step_decide", agent="StrategyDirector", next="step_route")
    )

    # Step 3: Router (SwitchStep)
    # This encodes the conditional logic into the graph structure.
    # The condition strings are interpreted by the runtime.
    manifest_builder.add_step(
        SwitchStep(
            id="step_route",
            cases={
                "action == 'DEPLOY_MSL'": "step_msl",
                "action == 'DEPLOY_REP'": "step_rep"
            },
            default="step_rep" # Fallback
        )
    )

    # Step 4a: MSL Engagement
    manifest_builder.add_step(
        AgentStep(id="step_msl", agent="MedicalScienceLiaison", next=None)
    )

    # Step 4b: Rep Engagement
    manifest_builder.add_step(
        AgentStep(id="step_rep", agent="SalesRepresentative", next=None)
    )

    # Set Entry Point
    manifest_builder.set_start_step("step_analyze")

    return manifest_builder.build()


# --- 3. Simulation Logic ---


def simulate_launch(scenario_name: str, input_data: dict[str, Any]):
    print(f"\n--- Simulation Scenario: {scenario_name} ---")
    manifest = build_launch_strategy_manifest()

    # Verify the manifest structure
    errors = manifest.verify()
    if errors:
        print("❌ Manifest Verification Failed:")
        for e in errors:
            print(f"  - {e}")
        return

    print(f"✅ Manifest '{manifest.metadata.name}' Verified.")

    # Execution Loop
    current_step_id = manifest.workflow.start
    context = {"inputs": input_data} # Shared context for simulation

    # To track the "action" for the router
    last_output = {}

    while current_step_id:
        step = manifest.workflow.steps.get(current_step_id)
        if not step:
            break

        print(f"👉 Step: {current_step_id} ({step.type})")

        if isinstance(step, AgentStep):
            agent = manifest.definitions[step.agent]
            # Mock Execution
            if isinstance(agent, AgentDefinition):
                print(f"   🤖 Agent: {agent.name} is working...")

                # Generate Mock Output based on the agent's capability
                # In a real engine, we'd use the LLM here.
                # For this mock, we force the StrategyDirector to follow the prompt policy
                # based on the input data context.

                mock_output = {}

                if agent.name == "MarketAnalyst":
                    # Simulate finding a knowledge gap if share is low
                    share = input_data.get("competitor_share", 0.5)
                    gap = share > 0.6 # If competitor is dominant, assume knowledge gap
                    mock_output = {
                        "opportunity_score": 85.0,
                        "prescriber_sentiment": "Skeptical" if gap else "Neutral",
                        "knowledge_gap": gap
                    }
                    context["analysis"] = mock_output

                elif agent.name == "StrategyDirector":
                    analysis = context.get("analysis", {})
                    if analysis.get("knowledge_gap"):
                        mock_output = {
                            "action": "DEPLOY_MSL",
                            "rationale": "High knowledge gap detected. Science-first approach required.",
                            "key_message": "Atorvastatin offers superior LDL reduction efficacy."
                        }
                    else:
                        mock_output = {
                            "action": "DEPLOY_REP",
                            "rationale": "Standard market conditions. Relationship maintenance sufficient.",
                            "key_message": "Remember to prescribe Lipitor."
                        }
                    context["strategy"] = mock_output
                    last_output = mock_output # Store for router

                elif agent.name == "MedicalScienceLiaison":
                    mock_output = {
                        "prescriptions_lift": 12.5,
                        "feedback": "Physician appreciated the mechanism of action data."
                    }

                elif agent.name == "SalesRepresentative":
                    mock_output = {
                        "prescriptions_lift": 3.2,
                        "feedback": "Physician accepted samples."
                    }

                print(f"   📄 Output: {json.dumps(mock_output, indent=2)}")

                # Move next
                current_step_id = step.next

        elif isinstance(step, SwitchStep):
            # Evaluate Conditions
            print("   🔀 Evaluating Route...")
            next_step = step.default

            # Simple mock evaluator
            action = last_output.get("action")

            if action == "DEPLOY_MSL" and "action == 'DEPLOY_MSL'" in step.cases:
                next_step = step.cases["action == 'DEPLOY_MSL'"]
                print(f"      Matched: DEPLOY_MSL -> {next_step}")
            elif action == "DEPLOY_REP" and "action == 'DEPLOY_REP'" in step.cases:
                next_step = step.cases["action == 'DEPLOY_REP'"]
                print(f"      Matched: DEPLOY_REP -> {next_step}")
            else:
                print(f"      No match, using default -> {next_step}")

            current_step_id = next_step

        else:
            print(f"   Unknown step type: {step.type}")
            break

    print("🏁 Workflow Complete.\n")


def main():
    # Scenario 1: High Competitor Share (Requires MSL)
    simulate_launch(
        scenario_name="Dominant Competitor (Zocor)",
        input_data={"region_code": "NY-01", "competitor_share": 0.75, "cardiologist_density": 120}
    )

    # Scenario 2: Low Competitor Share (Standard Rep)
    simulate_launch(
        scenario_name="Friendly Territory",
        input_data={"region_code": "TX-05", "competitor_share": 0.30, "cardiologist_density": 45}
    )

if __name__ == "__main__":
    main()
