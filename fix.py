import re

with open("AGENTS.md") as f:
    text = f.read()

# Fix heading issues
text = re.sub(r"### ([^\n\*]+)", r"### **\1**", text)

# Fix double bold
text = re.sub(r"\*\*(\*\*[^\n]+\*\*)\*\*", r"\1", text)
text = re.sub(r"\*\*(###[^\n]+)\*\*", r"\1", text)

with open("AGENTS.md", "w") as f:
    f.write(text)
