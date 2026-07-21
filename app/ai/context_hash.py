from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


VOLATILE_METADATA_FIELDS = {
    "generated_at",
}


def prepare_context_for_hash(
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Remove metadata values that change on every execution but do not
    alter the analytical meaning of the context.
    """

    normalized = copy.deepcopy(context)

    metadata = normalized.get("context_metadata")

    if isinstance(metadata, dict):
        for field in VOLATILE_METADATA_FIELDS:
            metadata.pop(field, None)

    return normalized


def serialize_context(
    context: dict[str, Any],
) -> str:
    """
    Serialize context deterministically.
    """

    normalized = prepare_context_for_hash(context)

    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def generate_context_hash(
    context: dict[str, Any],
) -> str:
    """
    Generate a stable SHA-256 hash for an analysis context.
    """

    serialized = serialize_context(context)

    return hashlib.sha256(
        serialized.encode("utf-8"),
    ).hexdigest()