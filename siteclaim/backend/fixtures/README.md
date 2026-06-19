# fixtures/

Serialised stage objects (JSON) used for tests and local development — the
plain-data handoffs between pipeline stages, captured to disk.

Because every model in `schemas/models.py` is JSON-serialisable, a stage
boundary can be a file here:

```python
from pathlib import Path
from schemas.models import ExtractedFacts

facts = ExtractedFacts.model_validate_json(Path("fixtures/example_facts.json").read_text())
```

Naming convention: `<scenario>_<object>.json` (e.g. `subcontract_extracted_facts.json`).
Keep fixtures small and self-explanatory; they double as documentation of the
contract shape. No real personal data — use synthetic examples only.
