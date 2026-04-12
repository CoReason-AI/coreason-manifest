with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

def print_lines(start, end):
    print(f"Lines {start}-{end}:")
    for i in range(start-1, end):
        print(f"{i+1}: {lines[i].rstrip()}")
    print("-" * 40)

print_lines(4115, 4125)
print_lines(5165, 5175)
print_lines(6580, 6605)
print_lines(6625, 6635)
print_lines(10585, 10600)

with open('src/coreason_manifest/utils/algebra.py', 'r') as f:
    lines_alg = f.readlines()
print("Algebra Lines 210-220:")
for i in range(209, 219):
    print(f"{i+1}: {lines_alg[i].rstrip()}")
