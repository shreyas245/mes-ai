"""Store-and-forward buffer (plan decision 5).

Patterns:
- **Proxy** — ``StoreAndForwardPublisher`` stands in for the real (NATS) publisher
  and transparently buffers when the link is down.
- SQLite-backed FIFO so buffered readings survive a gateway restart and replay in
  order once the core is reachable (NFR: no tag values lost across a 5-min outage).
"""

from __future__ import annotations

import abc
import json
import sqlite3
from dataclasses import dataclass


class Publisher(abc.ABC):
    @abc.abstractmethod
    async def publish(self, topic: str, payload: dict) -> None: ...


@dataclass
class LocalBuffer:
    """Ordered on-disk queue backed by SQLite."""

    path: str = "edge_buffer.db"

    def __post_init__(self) -> None:
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS buffer ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, payload TEXT)"
        )
        self._conn.commit()

    def enqueue(self, topic: str, payload: dict) -> None:
        self._conn.execute(
            "INSERT INTO buffer(topic, payload) VALUES(?, ?)",
            (topic, json.dumps(payload)),
        )
        self._conn.commit()

    def peek_batch(self, limit: int = 500) -> list[tuple[int, str, dict]]:
        rows = self._conn.execute(
            "SELECT id, topic, payload FROM buffer ORDER BY id LIMIT ?", (limit,)
        ).fetchall()
        return [(r[0], r[1], json.loads(r[2])) for r in rows]

    def ack(self, last_id: int) -> None:
        self._conn.execute("DELETE FROM buffer WHERE id <= ?", (last_id,))
        self._conn.commit()

    def depth(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM buffer").fetchone()[0]


class StoreAndForwardPublisher(Publisher):
    """Proxy over a real publisher with local durability + ordered replay."""

    def __init__(self, target: Publisher, buffer: LocalBuffer | None = None) -> None:
        self._target = target
        self._buffer = buffer or LocalBuffer()

    async def publish(self, topic: str, payload: dict) -> None:
        # Always durably record first, then try to drain in order.
        self._buffer.enqueue(topic, payload)
        await self.flush()

    async def flush(self) -> None:
        batch = self._buffer.peek_batch()
        for row_id, topic, payload in batch:
            try:
                await self._target.publish(topic, payload)
            except Exception:
                return  # link down; keep everything from row_id onward, retry later
            self._buffer.ack(row_id)
