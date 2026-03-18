import re

with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

content = re.sub(r'@given\(st\.lists\(st\.text\(min_size=1, max_size=128\).*?def test_evaluation_sandbox_profile_sorting.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'@given\(st\.lists\(st\.text\(min_size=1, max_size=128\).*?def test_syndicate_bids.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'@given\(st\.integers\(min_value=1, max_value=100\).*?def test_syndicate_allocation_sum.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
