"""JSON-file persistence for compositions.

Each composition is one file: data/compositions/<id>.json containing params,
rendered SVG (cached), validation report and review state. This keeps the
service stateless-friendly and easy to back up.
"""
from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import COMPOSITIONS_DIR

_LOCK = threading.Lock()
_ID_RE = re.compile(r"^[a-f0-9-]{8,36}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(cid: str) -> Path:
    if not _ID_RE.match(cid or ""):
        raise ValueError("invalid composition id")
    return COMPOSITIONS_DIR / f"{cid}.json"


def _write(cid: str, doc: dict) -> dict:
    p = _path(cid)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
    return doc


def create(doc: dict) -> dict:
    cid = uuid.uuid4().hex[:12]
    doc = dict(doc)
    doc.update({
        "id": cid,
        "created_at": _now(),
        "updated_at": _now(),
        "status": "draft",          # draft | pending_review | approved | rejected
        "review": None,
    })
    with _LOCK:
        return _write(cid, doc)


def get(cid: str) -> dict | None:
    p = COMPOSITIONS_DIR / f"{cid}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def update(cid: str, params: dict | None = None, review: dict | None = None,
           status: str | None = None) -> dict | None:
    with _LOCK:
        doc = get(cid)
        if doc is None:
            return None
        if params is not None:
            doc["params"] = params
        if status is not None:
            doc["status"] = status
        if review is not None:
            doc["review"] = review
            doc["review"]["at"] = _now()
        doc["updated_at"] = _now()
        return _write(cid, doc)


def list_all(status: str | None = None) -> list[dict]:
    docs = []
    for p in sorted(COMPOSITIONS_DIR.glob("*.json")):
        if p.suffix == ".tmp":
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if status and d.get("status") != status:
            continue
        # Keep list payloads small: no cached SVG in the list view.
        d.pop("svg", None)
        docs.append(d)
    docs.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
    return docs


def delete(cid: str) -> bool:
    p = _path(cid)
    if p.exists():
        p.unlink()
        return True
    return False
