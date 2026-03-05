import re

with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

# I need to ensure draw_temporal_bounds is defined before it's used
# Or just move it to the top.

# find draw_temporal_bounds definition
pattern = r"(@st\.composite\ndef draw_temporal_bounds.*?return \{.*?\n    \}\n)"
match = re.search(pattern, content, re.DOTALL)
if match:
    func_def = match.group(1)
    content = content.replace(func_def, "")

    # insert after draw_any_tool call or somewhere at the top
    insert_target = "@st.composite\ndef draw_any_tool"
    content = content.replace(insert_target, func_def + "\n" + insert_target)

    with open("tests/test_fuzzing.py", "w") as f:
        f.write(content)
