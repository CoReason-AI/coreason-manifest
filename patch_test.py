with open("tests/contracts/test_epistemic_zero_trust.py", "r") as f:
    content = f.read()

content = content.replace(
    'match="Topological Collapse: Firewall breach detected. Receipt invalid."',
    'match=r"Topological Collapse: Firewall breach detected\. Receipt invalid\."'
)

with open("tests/contracts/test_epistemic_zero_trust.py", "w") as f:
    f.write(content)
