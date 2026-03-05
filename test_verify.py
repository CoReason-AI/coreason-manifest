with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

assert "def draw_distribution_profile" in content
assert "draw_temporal_bounds" in content
assert "def draw_execution_span" in content
print("Fuzzer aligned")
