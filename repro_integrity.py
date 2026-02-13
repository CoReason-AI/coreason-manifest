from coreason_manifest.utils.integrity import verify_merkle_proof

def test_missing():
    chain = [{"a": 1}, {"b": 2}]
    result = verify_merkle_proof(chain)
    print(f"Result for missing prev_hash: {result}")
    assert result is False

def test_obj_missing():
    class NoPrevHash:
        def compute_hash(self) -> str:
            return "hash"
    chain = [NoPrevHash(), NoPrevHash()]
    result = verify_merkle_proof(chain)
    print(f"Result for obj missing prev_hash: {result}")
    assert result is False

if __name__ == "__main__":
    try:
        test_missing()
        print("test_missing passed")
    except AssertionError:
        print("test_missing failed")

    try:
        test_obj_missing()
        print("test_obj_missing passed")
    except AssertionError:
        print("test_obj_missing failed")
