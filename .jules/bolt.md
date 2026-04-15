## 2026-04-14 - Fast Vector Norms
**Learning:** `np.linalg.norm` contains overhead from internal checks and generalized multi-dimensional handling. When you know you are dealing with flat 1D vector embeddings (very common in latent alignment for AI), manually computing the dot product `np.dot(v, v)` and taking the square root `math.sqrt()` is significantly faster (~35%).
**Action:** Always prefer `math.sqrt(np.dot(v, v))` over `np.linalg.norm(v)` in hot paths processing fixed 1D vector embeddings.
