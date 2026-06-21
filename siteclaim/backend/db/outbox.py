"""Mock outbox for dispatched bundles — a JSON file, never the network.

``send_mock`` flips each bundle's status to ``sent_mock`` and appends a timestamped
record to ``backend/fixtures/out/outbox.json``. There is no SMTP, no socket, no
external call: "sending" is recording. The UI renders the outbox so the demo can
show that the right bundle went to the right firm.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from schemas.models import DispatchSet, DispatchStatus

OUTBOX_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "out" / "outbox.json"


def read_outbox(outbox_path: Path | str = OUTBOX_PATH) -> list[dict]:
    path = Path(outbox_path)
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def send_mock(dispatch_set: DispatchSet, outbox_path: Path | str = OUTBOX_PATH) -> DispatchSet:
    """Record the bundles as 'sent' and return the set with status ``sent_mock``."""
    sent = DispatchSet(
        bundles=[b.model_copy(update={"status": DispatchStatus.SENT_MOCK}) for b in dispatch_set.bundles]
    )
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    records = read_outbox(outbox_path)
    for bundle in sent.bundles:
        records.append({
            "firm_id": bundle.firm_id,
            "firm_name": bundle.firm_name,
            "trade": bundle.trade,
            "email_subject": bundle.email_subject,
            "bundle_doc_refs": bundle.bundle_doc_refs,
            "sent_at": timestamp,
        })
    path = Path(outbox_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return sent
