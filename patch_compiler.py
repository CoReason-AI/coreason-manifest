with open("scripts/enforce_cryptographic_determinism.py") as f:
    content = f.read()

target = """def is_list_type(annotation):
    origin = get_origin(annotation)
    if origin is list or annotation is list:
        return True
    if origin is Union or getattr(annotation, '__origin__', None) is Union:
        for arg in get_args(annotation):
            if is_list_type(arg):
                return True
    if origin is Annotated or getattr(annotation, '__origin__', None) is Annotated:"""

replacement = """import types

def is_list_type(annotation):
    origin = get_origin(annotation)
    if origin is list or annotation is list:
        return True
    if origin is Union or getattr(annotation, '__origin__', None) is Union or origin is types.UnionType or isinstance(annotation, types.UnionType):
        for arg in get_args(annotation):
            if is_list_type(arg):
                return True
    if origin is Annotated or getattr(annotation, '__origin__', None) is Annotated:"""

content = content.replace(target, replacement)

with open("scripts/enforce_cryptographic_determinism.py", "w") as f:
    f.write(content)
