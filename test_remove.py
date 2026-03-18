with open("src/coreason_manifest/spec/ontology.py") as f:
    text = f.read()

# Look for unreachable code in ONLY these 6 classes:
# MarketContract
# PredictionMarketState
# TokenBurnReceipt
# RoutingFrontierPolicy
# EscrowPolicy
# ComputeProvisioningIntent

# None of these currently have mathematically unreachable `if` statements except the ones that were just removed by clamping constraints (since we no longer raise ValueError in validators due to bounding manually).
# However, Pydantic type hints enforce that list parameters (like required_capabilities, order_book) can't be None.
# Let's inspect `PredictionMarketState` for `order_book`:
# order_book: list[HypothesisStakeReceipt] = Field(description="The immutable ledger of all stakes placed by the swarm.")
# It has no `None` type, so checking `if getattr(self, "order_book", None) is not None:` would be dead code. But `PredictionMarketState` does NOT have that check, it just sorts:
# object.__setattr__(self, "order_book", sorted(self.order_book, key=lambda x: x.agent_id))

# So there are NO MORE unreachable code branches in the 6 target classes. I will report this to complete the step.
