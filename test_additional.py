from coreason_manifest.spec.ontology import *
import pytest

def test_imports():
    try:
        from coreason_manifest.spec.ontology import StructuralCausalModelManifest
        print("StructuralCausalModelManifest imported")
    except ImportError:
        print("StructuralCausalModelManifest missing")

    try:
        from coreason_manifest.spec.ontology import AgentWorkingMemorySnapshot
        print("AgentWorkingMemorySnapshot imported")
    except ImportError:
        print("AgentWorkingMemorySnapshot missing")

    try:
        from coreason_manifest.spec.ontology import AgentMemorySnapshot
        print("AgentMemorySnapshot imported")
    except ImportError:
        print("AgentMemorySnapshot missing")

test_imports()
