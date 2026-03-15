1. **Insert function `reduce_ledger_to_active_state` into `src/coreason_manifest/utils/algebra.py`**
   - Place the function exactly between `project_manifest_to_markdown` and `get_ontology_schema`.
   - The function will use pure logic to collect quarantined event and invalidated node IDs.
   - It iterates through `ledger.history`, filtering out those directly impacted or sourced from invalidated nodes.
   - It will use `getattr(event, "source_node_id", None)` to handle events securely.
2. **Execute tests and validations**
   - Complete pre-commit steps to make sure proper testing, verifications, reviews and reflections are done.
   - Run `uv run ruff format src/coreason_manifest/utils/algebra.py`
   - Run `uv run ruff check src/coreason_manifest/utils/algebra.py --fix`
   - Run `uv run mypy src/coreason_manifest/utils/algebra.py`
   - Run `uv run pytest tests/contracts/`
