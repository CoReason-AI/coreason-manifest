from typing import Annotated, Literal

from pydantic import BaseModel, Field


class A(BaseModel):
    type: Literal["a"] = "a"


class B(BaseModel):
    type: Literal["b"] = "b"


_UnionAB = Annotated[A | B, Field(discriminator="type")]


class C(BaseModel):
    type: Literal["c"] = "c"


# Try combining
Combined = Annotated[_UnionAB | C, Field(discriminator="type")]


class Container(BaseModel):
    node: Combined


print(Container(node={"type": "c"}).node)
print(Container(node={"type": "a"}).node)
