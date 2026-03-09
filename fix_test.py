import hypothesis.strategies as st

print(st.characters(blacklist_characters=["\n", "\r"], blacklist_categories=("Cs",)).example())
