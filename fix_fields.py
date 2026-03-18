import re

with open("src/coreason_manifest/spec/ontology.py") as f:
    text = f.read()

# For EscrowPolicy
text = re.sub(
    r'    escrow_locked_magnitude: int = Field\(\n        le=1000000000,\n        ge=0,\n        description="The strictly typed integer amount cryptographically locked prior to execution.",\n    \)',
    r'''    escrow_locked_magnitude: int = Field(
        le=1000000000,
        ge=0,
        description="The strictly typed integer amount cryptographically locked prior to execution.",
    )

    @model_validator(mode="before")
    def _clamp_escrow_magnitude(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values["escrow_locked_magnitude"] = max(0, min(values.get("escrow_locked_magnitude", 0), 1000000000))
        return values''', text)

# For ComputeProvisioningIntent
text = re.sub(
    r'    max_budget: int = Field\(\n        le=1000000000, description="The maximum atomic cost budget allowable for the provisioned compute."\n    \)',
    r'''    max_budget: int = Field(
        le=1000000000, description="The maximum atomic cost budget allowable for the provisioned compute."
    )

    @model_validator(mode="before")
    def _clamp_max_budget(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values["max_budget"] = max(0, min(values.get("max_budget", 0), 1000000000))
        return values''', text)

# For MarketContract
text = re.sub(
    r'    minimum_collateral: int = Field\(\n        le=1000000000, ge=0, description="The minimum atomic token collateral held in escrow."\n    \)',
    r'''    minimum_collateral: int = Field(
        le=1000000000, ge=0, description="The minimum atomic token collateral held in escrow."
    )''', text)
text = re.sub(
    r'    @model_validator\(mode="after"\)\n    def _enforce_economic_escrow_invariant\(self\) -> Self:\n        """Mathematically prove that a contract cannot penalize more than the escrowed amount."""\n        if self\.slashing_penalty > self\.minimum_collateral:\n            raise ValueError\("ECONOMIC INVARIANT VIOLATION: slashing_penalty cannot exceed minimum_collateral."\)\n        return self',
    r'''    @model_validator(mode="before")
    def _enforce_economic_escrow_invariant(cls, values: Any) -> Any:
        """Mathematically prove that a contract cannot penalize more than the escrowed amount."""
        if isinstance(values, dict):
            mc = values.get("minimum_collateral", 0)
            sp = values.get("slashing_penalty", 0)
            cmc = max(0, min(mc, 1000000000))
            csp = max(0, min(sp, cmc))
            values["minimum_collateral"] = cmc
            values["slashing_penalty"] = csp
        return values''', text)

# For TokenBurnReceipt
text = re.sub(
    r'    burn_magnitude: int = Field\(\n        le=1000000000, ge=0, description="The normalized economic cost magnitude representing thermodynamic burn."\n    \)',
    r'''    burn_magnitude: int = Field(
        le=1000000000, ge=0, description="The normalized economic cost magnitude representing thermodynamic burn."
    )

    @model_validator(mode="before")
    def _clamp_token_burn(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "input_tokens" in values: values["input_tokens"] = max(0, min(values["input_tokens"], 1000000000))
            if "output_tokens" in values: values["output_tokens"] = max(0, min(values["output_tokens"], 1000000000))
            if "burn_magnitude" in values: values["burn_magnitude"] = max(0, min(values["burn_magnitude"], 1000000000))
        return values''', text)

# For RoutingFrontierPolicy
text = re.sub(
    r'    max_carbon_intensity_gco2eq_kwh: float \| None = Field\(\n        le=10000.0,\n        default=None,\n        ge=0.0,\n        description="The maximum operational carbon intensity of the physical data center grid allowed for this agent\'s routing.",\n    \)',
    r'''    max_carbon_intensity_gco2eq_kwh: float | None = Field(
        le=10000.0,
        default=None,
        ge=0.0,
        description="The maximum operational carbon intensity of the physical data center grid allowed for this agent's routing.",
    )

    @model_validator(mode="before")
    def _clamp_frontier_bounds(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "max_latency_ms" in values: values["max_latency_ms"] = max(1, min(values["max_latency_ms"], 86400000))
            if "max_cost_magnitude_per_token" in values: values["max_cost_magnitude_per_token"] = max(1, min(values["max_cost_magnitude_per_token"], 1000000000))
            if "min_capability_score" in values: values["min_capability_score"] = max(0.0, min(values["min_capability_score"], 1.0))
            if values.get("max_carbon_intensity_gco2eq_kwh") is not None:
                values["max_carbon_intensity_gco2eq_kwh"] = max(0.0, min(values["max_carbon_intensity_gco2eq_kwh"], 10000.0))
        return values''', text)

# For PredictionMarketState probabilities, the type is dict[str, str], so it's best to validate as 'before' as well
text = re.sub(
    r'    current_market_probabilities: dict\[\n        Annotated\[str, StringConstraints\(max_length=255\)\], Annotated\[str, StringConstraints\(max_length=255\)\]\n    \] = Field\(\n        max_length=1000000000,\n        description="Mapping of hypothesis IDs to their current LMSR-calculated market price \(probability\) as stringified decimals.",\n    \)',
    r'''    current_market_probabilities: dict[
        Annotated[str, StringConstraints(max_length=255)], Annotated[str, StringConstraints(max_length=255)]
    ] = Field(
        max_length=1000000000,
        description="Mapping of hypothesis IDs to their current LMSR-calculated market price (probability) as stringified decimals.",
    )

    @model_validator(mode="before")
    def _clamp_market_probabilities(cls, values: Any) -> Any:
        if isinstance(values, dict) and "current_market_probabilities" in values:
            clamped_probs: dict[str, str] = {}
            total = 0.0

            import math
            for k, v in values["current_market_probabilities"].items():
                try:
                    prob = float(v)
                except ValueError:
                    prob = 0.0

                prob = max(0.0, min(prob, 1.0))
                total += prob
                clamped_probs[k] = str(prob)

            if total > 0.0 and not math.isclose(total, 1.0, abs_tol=1e-5):
                normalized_probs = {k: str(float(v) / total) for k, v in clamped_probs.items()}
            elif total == 0.0 and clamped_probs:
                uniform = 1.0 / len(clamped_probs)
                normalized_probs = {k: str(uniform) for k in clamped_probs.keys()}
            else:
                normalized_probs = clamped_probs

            values["current_market_probabilities"] = normalized_probs
        return values''', text)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(text)
