with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

old_code = """        except SyntaxError as e:
            raise ValueError(f"Invalid syntax in constraint AST: {e}")"""
new_code = """        except SyntaxError as e:
            raise ValueError(f"Invalid syntax in constraint AST: {e}") from e"""
content = content.replace(old_code, new_code)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
