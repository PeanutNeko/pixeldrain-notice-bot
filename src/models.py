from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WatchRecord:
    id: int
    share_id: str
    label: str | None
    channel_id: int
    interval_sec: int
    enabled: int
    last_scan_ts: str | None
    last_error: str | None


@dataclass(slots=True)
class SnapshotEntry:
    path: str
    name: str | None
    node_type: str | None
    modified: str | None
    file_size: int | None
    sha256_sum: str | None


@dataclass(slots=True)
class DiffResult:
    added: list[str]
    removed: list[str]
    changed: list[str]


def row_to_watch(row: Any) -> WatchRecord:
    return WatchRecord(
        id=row["id"],
        share_id=row["share_id"],
        label=row["label"],
        channel_id=row["channel_id"],
        interval_sec=row["interval_sec"],
        enabled=row["enabled"],
        last_scan_ts=row["last_scan_ts"],
        last_error=row["last_error"],
    )
