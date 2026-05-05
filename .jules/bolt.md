## 2026-04-22 - Replacing isinstance with type() breaks polymorphic models
**Learning:** In Pydantic-heavy schemas or standard duck-typed APIs, replacing `isinstance()` checks with exact `type() is` checks is a functional regression. While `type() is` is faster because it skips MRO traversal, it breaks inheritance (e.g. `dict` vs `defaultdict`, or Pydantic subclasses). The minor speedup is not worth breaking codebase polymorphism.
**Action:** Do not replace `isinstance()` with `type() is` unless strict type constraints are mathematically proven to be required and no subclasses are ever passed. Opt to optimize loop structures or data ingestion over runtime type reflection constraints.

## 2026-05-05 - Direct dot product is much faster than np.linalg.norm
**Learning:** np.linalg.norm and np.errstate are surprisingly slow when called repeatedly on vectors. Using direct dot products to compute magnitude and avoiding the errstate context significantly improves performance for cosine similarity operations (~2.5x speedup).
**Action:** Avoid np.errstate in tight loops and prefer explicit dot products for calculating vector norms when doing manual cosine similarity.
