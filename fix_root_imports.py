with open('src/coreason_manifest/__init__.py', 'r') as f:
    content = f.read()

# Replace coreason_manifest.workflow.markets with coreason_manifest.workflow
content = content.replace(
    "from coreason_manifest.workflow.markets import HypothesisStake, MarketResolution, PredictionMarketState\n",
    "from coreason_manifest.workflow import HypothesisStake, MarketResolution, PredictionMarketState\n"
)

# Replace coreason_manifest.oversight.governance import PredictionMarketPolicy with coreason_manifest.oversight
content = content.replace(
    "from coreason_manifest.oversight.governance import PredictionMarketPolicy\n",
    "from coreason_manifest.oversight import PredictionMarketPolicy\n"
)

with open('src/coreason_manifest/__init__.py', 'w') as f:
    f.write(content)
