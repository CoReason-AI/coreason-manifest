import pytest
from coreason_manifest.spec.core.flow import EdgeSpec
from coreason_manifest.utils.io import SecurityViolationError
from pydantic import ValidationError

def test_edge_bounds():
    # Valid
    EdgeSpec(from_node="a", to_node="b", max_iterations=1, timeout=1)

    # Invalid < 1
    with pytest.raises(ValidationError):
        EdgeSpec(from_node="a", to_node="b", max_iterations=0)

    with pytest.raises(ValidationError):
        EdgeSpec(from_node="a", to_node="b", timeout=-1)

def test_ast_attributes():
    # Valid attribute
    EdgeSpec(from_node="a", to_node="b", condition="state.ok")

    # Valid subscript
    EdgeSpec(from_node="a", to_node="b", condition="data['key']")

    # Invalid dunder attribute
    with pytest.raises(SecurityViolationError):
        EdgeSpec(from_node="a", to_node="b", condition="obj.__class__")

    # Invalid dunder subscript
    with pytest.raises(SecurityViolationError):
        EdgeSpec(from_node="a", to_node="b", condition="obj['__class__']")

def test_ast_dynamic_bypass():
    with pytest.raises(SecurityViolationError):
        # BinOp in slice: "data['__' + 'class__']"
        # We need to simulate python code that produces this AST
        # AST for "data['__' + 'class__']":
        # Subscript(value=Name(id='data'), slice=BinOp(left=Constant('__'), op=Add(), right=Constant('class__')))
        EdgeSpec(from_node="a", to_node="b", condition="data['__' + 'class__']")

    with pytest.raises(SecurityViolationError):
        EdgeSpec(from_node="a", to_node="b", condition="data[f'__class__']")

    with pytest.raises(SecurityViolationError):
        EdgeSpec(from_node="a", to_node="b", condition="data[chr(95)]") # Call
