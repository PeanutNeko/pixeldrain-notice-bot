from __future__ import annotations

import aiosqlite

from config import DATABASE_PATH, DEFAULT_CHANNEL_ID, DEFAULT_INTERVAL_SEC, SEED_WATCH_IDS
from src.models import WatchRecord, row_to_watch

CREATE_WATCHES = '''
CREATE TABLE IF NOT EXISTS watches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_id TEXT NOT NULL UNIQUE,
    label TEXT,
    channel_id INTEGER NOT NULL,
    interval_sec INTEGER NOT NULL DEFAULT 300,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_scan_ts TEXT,
    last_error TEXT
)
'''

CREATE_SNAPSHOTS = '''
CREATE TABLE IF NOT EXISTS snapshots (
    watch_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    name TEXT,
    node_type TEXT,
    modified TEXT,
    file_size INTEGER,
    sha256_sum TEXT,
    PRIMARY KEY (watch_id, path)
)
'''


async def connect() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await connect()
    try:
        await db.execute(CREATE_WATCHES)
        await db.execute(CREATE_SNAPSHOTS)
        await db.commit()

        if DEFAULT_CHANNEL_ID and SEED_WATCH_IDS:
            for share_id in SEED_WATCH_IDS:
                await db.execute(
                    '''
                    INSERT OR IGNORE INTO watches (share_id, label, channel_id, interval_sec, enabled)
                    VALUES (?, ?, ?, ?, 1)
                    ''',
                    (share_id, share_id, DEFAULT_CHANNEL_ID, DEFAULT_INTERVAL_SEC),
                )
            await db.commit()
    finally:
        await db.close()


async def list_watches(enabled_only: bool = False) -> list[WatchRecord]:
    query = "SELECT * FROM watches"
    if enabled_only:
        query += " WHERE enabled = 1"
    query += " ORDER BY id"

    db = await connect()
    try:
        async with db.execute(query) as cur:
            rows = await cur.fetchall()
        return [row_to_watch(row) for row in rows]
    finally:
        await db.close()


async def get_watch_by_id(watch_id: int) -> WatchRecord | None:
    db = await connect()
    try:
        async with db.execute("SELECT * FROM watches WHERE id = ?", (watch_id,)) as cur:
            row = await cur.fetchone()
        return row_to_watch(row) if row else None
    finally:
        await db.close()


async def upsert_watch(
    share_id: str,
    label: str | None,
    channel_id: int,
    interval_sec: int,
) -> int:
    db = await connect()
    try:
        await db.execute(
            '''
            INSERT INTO watches (share_id, label, channel_id, interval_sec, enabled)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(share_id)
            DO UPDATE SET
                label = excluded.label,
                channel_id = excluded.channel_id,
                interval_sec = excluded.interval_sec,
                enabled = 1
            ''',
            (share_id, label, channel_id, interval_sec),
        )
        await db.commit()

        async with db.execute("SELECT id FROM watches WHERE share_id = ?", (share_id,)) as cur:
            row = await cur.fetchone()
        return int(row["id"])
    finally:
        await db.close()


async def delete_watch(watch_id: int) -> bool:
    db = await connect()
    try:
        await db.execute("DELETE FROM snapshots WHERE watch_id = ?", (watch_id,))
        cur = await db.execute("DELETE FROM watches WHERE id = ?", (watch_id,))
        await db.commit()
        return cur.rowcount > 0
    finally:
        await db.close()


async def set_watch_enabled(watch_id: int, enabled: bool) -> bool:
    db = await connect()
    try:
        cur = await db.execute(
            "UPDATE watches SET enabled = ? WHERE id = ?",
            (1 if enabled else 0, watch_id),
        )
        await db.commit()
        return cur.rowcount > 0
    finally:
        await db.close()


async def update_last_scan(watch_id: int, last_scan_ts: str, last_error: str | None) -> None:
    db = await connect()
    try:
        await db.execute(
            "UPDATE watches SET last_scan_ts = ?, last_error = ? WHERE id = ?",
            (last_scan_ts, last_error, watch_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_snapshot(watch_id: int) -> dict[str, dict]:
    db = await connect()
    try:
        async with db.execute(
            "SELECT * FROM snapshots WHERE watch_id = ?",
            (watch_id,),
        ) as cur:
            rows = await cur.fetchall()

        return {
            row["path"]: {
                "name": row["name"],
                "node_type": row["node_type"],
                "modified": row["modified"],
                "file_size": row["file_size"],
                "sha256_sum": row["sha256_sum"],
            }
            for row in rows
        }
    finally:
        await db.close()


async def replace_snapshot(watch_id: int, snapshot: dict[str, dict]) -> None:
    db = await connect()
    try:
        await db.execute("DELETE FROM snapshots WHERE watch_id = ?", (watch_id,))
        await db.executemany(
            '''
            INSERT INTO snapshots
            (watch_id, path, name, node_type, modified, file_size, sha256_sum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            [
                (
                    watch_id,
                    path,
                    info.get("name"),
                    info.get("node_type"),
                    info.get("modified"),
                    info.get("file_size"),
                    info.get("sha256_sum"),
                )
                for path, info in snapshot.items()
            ],
        )
        await db.commit()
    finally:
        await db.close()
