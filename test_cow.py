from pydantic import BaseModel


class TestModel(BaseModel, frozen=True):
    a: int
    b: str


def test():
    m = TestModel(a=1, b="two")
    print("Model:", m)
    m2 = m.model_copy(update={"a": 2})
    print("Copied Model:", m2)


test()
