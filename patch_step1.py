with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


# Refactor DocumentLayoutRegionState
old_literal = 'Literal["header", "paragraph", "figure", "table", "footnote", "caption", "equation"]'
new_literal = 'Literal[\n        "header", "paragraph", "figure", "table", "footnote",\n        "caption", "equation", "list_item", "code_block", "form_field"\n    ]'
content = content.replace(old_literal, new_literal)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
