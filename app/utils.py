from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_value(value: object, case_insensitive: bool) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if case_insensitive:
        return text.lower()
    return text
