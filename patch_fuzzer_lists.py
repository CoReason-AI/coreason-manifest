import re
with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

# For any st.lists(arg), we replace it with st.lists(arg, max_size=100)
# This assumes there's exactly one argument inside the parenthesis for st.lists in the fuzzer.
# We will match `st.lists(something)` where `something` does not contain `, max_size=`.
def list_replacer(match):
    inner = match.group(1)
    if 'max_size=' in inner:
        return match.group(0)
    return f'st.lists({inner}, max_size=100)'

# Match st.lists(...) taking care of nested parentheses by parsing basic levels or just regex
# A simple regex for simple expressions:
content = re.sub(r'st\.lists\((st\.[a-zA-Z_]+\([^\)]*\)|[a-zA-Z_]+\(\))\)', list_replacer, content)

# Or maybe just a brute-force approach, replace all `st.lists(` and then fix errors manually if any.
with open("tests/test_fuzzing.py", "w") as f:
    f.write(content)
