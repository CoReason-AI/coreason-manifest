class MockOp:
    def __init__(self, op, path, value=None):
        self.op = op
        self.path = path
        self.value = value

    def model_dump(self, exclude_unset=True):
        d = {"op": self.op, "path": self.path}
        if self.value is not None:
            d["value"] = self.value
        return d


patch = MockOp("add", "/a/b", 5)

match patch.model_dump():
    case {"op": "add", "path": path, "value": val}:
        print(f"Added {val} at {path}")
    case _:
        print("Other")
