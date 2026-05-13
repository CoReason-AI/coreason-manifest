import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

patterns = [
    'AdversarialEmulationProfile',
    'CognitiveRewardEvaluationReceipt',
    'EnvironmentalSpoofingProfile',
    'EpistemicRewardGradientPolicy',
    'KinematicNoiseProfile',
    'ProcessRewardContract'
]
for p in patterns:
    # Match the class definition until the next non-whitespace character at the start of a line, or end of file.
    # Note: re.sub with (?=\n\S|\Z) might match empty lines before the next block, which is fine.
    # We use (?:(?!\n\S).)* which matches any character except when followed by a non-whitespace at start of line
    # Alternatively, just use .*?(?=\n\S|\Z)
    content = re.sub(rf'^class {p}\(CoreasonBaseState\):.*?(?=\n\S|\Z)', '', content, flags=re.DOTALL | re.MULTILINE)
    # Remove model_rebuild calls
    content = re.sub(rf'{p}\.model_rebuild\(\)\n?', '', content)

# 2. Remove field references.
content = re.sub(r'\n\s+grpo_reward_policy:\s*EpistemicRewardGradientPolicy\s*\|\s*None\s*=\s*Field\([\s\S]*?\n\s+\)', '', content)
content = re.sub(r'\n\s+emulation_profile:\s*AdversarialEmulationProfile\s*\|\s*None\s*=\s*Field\([\s\S]*?\n\s+\)', '', content)
content = re.sub(r'\n\s+prm_evaluations:\s*list\[\"?ProcessRewardContract\"?\]\s*=\s*Field\([\s\S]*?\n\s+\)', '', content)
content = re.sub(r'\n\s+prm_policy:\s*ProcessRewardContract\s*\|\s*None\s*=\s*Field\([\s\S]*?\n\s+\)', '', content)
content = re.sub(r'\n\s*\|\s*CognitiveRewardEvaluationReceipt', '', content)
content = re.sub(r' Models \(prm_evaluations: list\[ProcessRewardContract\]\) at each topological node.', '.', content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
