with open("src/coreason_manifest/utils/algebra.py") as f:
    content = f.read()

# Let's double check if we correctly replaced confidence_score logic in algebra.py as mandated
# "Implementation: Wherever edge.confidence_score is referenced, change the logic to check: if edge.belief_vector: weight = edge.belief_vector.semantic_distance (or lexical_confidence). If belief_vector is None (because it relies on an SLA), default the weight to 0.0 or handle it gracefully according to the function's math."
import re

print("Matches for confidence_score:")
for m in re.finditer(r".{0,50}confidence_score.{0,50}", content):
    print(m.group(0))

print("Matches for belief_vector:")
for m in re.finditer(r".{0,50}belief_vector.{0,50}", content):
    print(m.group(0))
