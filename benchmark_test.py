import timeit

from coreason_manifest.utils.mcp_adapters import _canonicalize_payload


def bench_canonicalize():
    payload = {"a": 1, "b": None, "c": [1, 2, None, 4], "d": {"e": 5, "f": None, "g": [None, None, 7]}}
    _canonicalize_payload(payload)


t = timeit.timeit(bench_canonicalize, number=10000)
print(f"_canonicalize_payload: {t:.4f}s")
