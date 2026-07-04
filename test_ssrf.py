from coreason_manifest.utils.algebra import _validate_ssrf_safety

try:
    _validate_ssrf_safety("http://127.1/")
    print("FAILED")
except ValueError:
    print("PASSED")

try:
    _validate_ssrf_safety("http://0x7f000001/")
    print("FAILED")
except ValueError:
    print("PASSED")
