import pytest
from pathlib import Path
from coreason_manifest.utils.loader import CitadelLoader, safety_check

def test_safety_check_violation():
    data = {"some_key": "import subprocess; subprocess.Popen('ls')"}
    with pytest.raises(ValueError, match="Security Violation"):
        safety_check(data)

def test_loader_jail_violation(tmp_path):
    # Setup
    jail = tmp_path / "jail"
    jail.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("foo: bar", encoding="utf-8")

    inside = jail / "main.yaml"
    inside.write_text(f'$ref: "../outside.yaml"', encoding="utf-8")

    loader = CitadelLoader(root=jail)

    with pytest.raises(ValueError, match="Path traversal attempt denied"):
        loader.load_recursive(inside)

def test_loader_recursive_success(tmp_path):
    root = tmp_path / "app"
    root.mkdir()

    main = root / "main.yaml"
    child = root / "child.yaml"

    main.write_text('$ref: "./child.yaml"', encoding="utf-8")
    child.write_text("hello: world", encoding="utf-8")

    loader = CitadelLoader(root=root)
    result = loader.load_recursive(main)

    assert result == {"hello": "world"}

def test_circular_dependency(tmp_path):
    root = tmp_path / "app"
    root.mkdir()

    a = root / "a.yaml"
    b = root / "b.yaml"

    a.write_text('$ref: "./b.yaml"', encoding="utf-8")
    b.write_text('$ref: "./a.yaml"', encoding="utf-8")

    loader = CitadelLoader(root=root)

    with pytest.raises(ValueError, match="Circular dependency detected"):
        loader.load_recursive(a)
