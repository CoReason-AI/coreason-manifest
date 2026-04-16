## 2026-04-14 - Fast Vector Norms
**Learning:** `np.linalg.norm` contains overhead from internal checks and generalized multi-dimensional handling. When you know you are dealing with flat 1D vector embeddings (very common in latent alignment for AI), manually computing the dot product `np.dot(v, v)` and taking the square root `math.sqrt()` is significantly faster (~35%).
**Action:** Always prefer `math.sqrt(np.dot(v, v))` over `np.linalg.norm(v)` in hot paths processing fixed 1D vector embeddings.

## 2026-04-14 - Replacing Numpy operations with Pure Python
**Learning:** In simple operations like checking sum of small dictionaries and arrays in validators, NumPy's startup overhead and object creation overhead (like `np.array`, `np.clip`, `np.isclose`) make it significantly slower (~8x slower) compared to list comprehensions and standard math library in pure Python.
**Action:** Always prefer standard math operations and list comprehensions over NumPy for small iterative transformations, such as data validations and clamp operations on dictionaries or lists, unless dealing with large multidimensional matrix transformations.
