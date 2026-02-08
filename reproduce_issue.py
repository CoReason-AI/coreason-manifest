
import random
import string

def _random_string(min_len: int = 5, max_len: int = 20) -> str:
    # Simulating the behavior in src/coreason_manifest/utils/mock.py
    rng = random.Random()
    length = rng.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits + " "
    return "".join(rng.choices(chars, k=length)).strip()

def reproduce():
    min_len = 25
    max_len = 35 # Derived from min_len + 10

    failure_count = 0
    trials = 1000

    for _ in range(trials):
        s = _random_string(min_len, max_len)
        if len(s) < min_len:
            print(f"Failure: len('{s}') = {len(s)} < {min_len}")
            failure_count += 1

    print(f"Failures: {failure_count}/{trials}")

if __name__ == "__main__":
    reproduce()
