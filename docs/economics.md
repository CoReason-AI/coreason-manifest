## Part IV: Economics & Multi-Agent Systems (400-Level)

For academic researchers analyzing decentralized AI, the CoReason Manifest provides a rigorous mathematical framework for understanding how distributed computational nodes coordinate without a centralized trust broker. The swarm operates as a strict computational economy governed by Algorithmic Mechanism Design, Cooperative Game Theory, and Proof-of-Stake (PoS) physics.

### 4.1 Algorithmic Mechanism Design and Spot Markets

To dynamically allocate thermodynamic compute based on task complexity, the orchestrator utilizes decentralized Spot Market. This process initiates with a `TaskAnnouncementIntent`, which broadcasts a Request for Proposal (RFP) to the swarm. This intent physically caps the maximum expenditure via the `max_budget_magnitude` boundary (`le=18446744073709551615`), preventing economic overflow during allocation.

Participating agents evaluate their internal state and respond with an `AgentBidIntent`. Bids are probabilistic and multi-objective, requiring the agent to mathematically project its `estimated_cost_magnitude` (`le=18446744073709551615`), physical `estimated_latency_ms` (`ge=0`), and its epistemic `confidence_score` (`ge=0.0, le=1.0`).

The convergence of this market is mapped by the `AuctionState`, a declarative snapshot of the N-dimensional order book. Market liveness is physically bounded by a strict `clearing_timeout` (`gt=0`), preventing infinite deliberation. To guarantee cryptographic determinism during market clearing, a `@model_validator` structurally forces the `bids` array to be sorted first by cost (`estimated_cost_magnitude`), then by agent DID (`agent_cid`), preserving RFC 8785 hashing invariants and ensuring a mathematically perfect supply curve geometry.

### 4.2 Prediction Markets and Automated Market Makers (AMM)

When agents face epistemic uncertainty or deadlock over a factual claim, the system utilizes a `PredictionMarketState` to synthesize consensus via an Automated Market Maker (AMM).

This state leverages Robin Hanson's Logarithmic Market Scoring Rule (LMSR) to guarantee infinite liquidity, parameterized by the `lmsr_b_parameter` (restricted to a strict stringified decimal regex `^\d+\.\d+$`). Agents participate by submitting a `HypothesisStakeReceipt`, which acts as an economic vehicle to project their internal belief into the market.

By submitting this receipt, an agent locks a strictly positive PoS collateral (`staked_magnitude`, `gt=0`) to assert its `implied_probability` (`ge=0.0, le=1.0`). This explicitly penalizes hallucinating or Byzantine nodes by placing their locked computational budget at risk, incentivizing agents to reach a truthful Nash Equilibrium based on their actual epistemic certainty.

### 4.3 Cooperative Game Theory and Credit Assignment

Once a macroscopic swarm outcome is achieved, the orchestrator must solve the credit assignment problem—determining how to equitably distribute the reward (or compute budget) among the cooperating nodes. This factorization is executed via the `CausalExplanationEvent`.

The calculation of the reward relies on the `ShapleyAttributionReceipt`, which formalizes Cooperative Game Theory to compute the exact Shapley value ($\phi_i$) for each agent's marginal contribution. The receipt computes a `normalized_contribution_percentage` (strictly clamped between `ge=0.0, le=1.0`) alongside bootstrap confidence intervals (`confidence_interval_lower` and `confidence_interval_upper`, bounded by `le=18446744073709551615.0`). The resulting array of `agent_attributions` is deterministically sorted by `target_node_cid` prior to being committed to the immutable Epistemic Ledger, ensuring the reward distribution is cryptographically unassailable.

### 4.4 Practical Byzantine Fault Tolerance (pBFT) and Social Choice

When the swarm operates in high-risk environments, consensus cannot rely on simple majorities due to the risk of Sybil attacks or hallucinating cohorts. The `CouncilTopologyManifest` formalizes Social Choice Theory to mandate rigorous truth-synthesis.

The debate parameters are governed by the `ConsensusPolicy`. To mathematically solve the Halting Problem for runaway arguments, the policy enforces an absolute integer ceiling via `max_debate_rounds` (`le=18446744073709551615`).

If the consensus strategy is set to `pbft`, the swarm must adhere to a strict `QuorumPolicy`. The mathematical viability of the network is physically guaranteed at instantiation by the `enforce_bft_math` validator, which enforces the strict distributed systems invariant: $N \ge 3f + 1$ (where `min_quorum_size` is $N$, and `max_tolerable_faults` is $f$). If the ring detects a Byzantine fault, it executes the defined `byzantine_action` (e.g., `slash_escrow`).

To prevent economic paradoxes where an orchestrator attempts to slash a node that has no capital, the `CouncilTopologyManifest` employs the `enforce_funded_byzantine_slashing` constraint. This mathematically guarantees that if a pBFT strategy mandates slashing, execution is structurally forbidden unless a funded `council_escrow` is actively locked, perfectly aligning Proof of Stake mechanics with Byzantine security.
