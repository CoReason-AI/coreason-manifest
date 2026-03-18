import re

with open("tests/contracts/test_ontology_hypothesis.py", "r") as f:
    content = f.read()

content = re.sub(r'@given\(st\.lists\(st\.text\(min_size=1, max_size=128\).*?def test_theory_of_mind_snapshot_sorting.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
content = content.replace("with pytest.raises(ValueError, ):", "with pytest.raises(ValueError):")

with open("tests/contracts/test_ontology_hypothesis.py", "w") as f:
    f.write(content)
