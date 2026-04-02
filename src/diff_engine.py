from __future__ import annotations

from src.models import DiffResult


def diff_snapshot(old: dict[str, dict], new: dict[str, dict]) -> DiffResult:
    old_keys = set(old)
    new_keys = set(new)

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed: list[str] = []

    for path in sorted(old_keys & new_keys):
        old_item = old[path]
        new_item = new[path]
        if (
            old_item.get("modified") != new_item.get("modified")
            or old_item.get("file_size") != new_item.get("file_size")
            or old_item.get("sha256_sum") != new_item.get("sha256_sum")
            or old_item.get("node_type") != new_item.get("node_type")
        ):
            changed.append(path)

    return DiffResult(added=added, removed=removed, changed=changed)
