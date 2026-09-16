from time import time
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SentTZStore:
    def __init__(self, collection=None):
        self.collection = collection
        self._memory: Dict[int, List[Dict[str, Any]]] = {}

    async def list(self, buyer_id: int) -> List[Dict[str, Any]]:
        items = None
        if self.collection is not None:
            record = await self.collection.find_one({"_id": buyer_id})
            if record:
                items = record.get("items")
                if items is None and record.get("data"):
                    items = [{"id": "legacy", "created_at": 0, "data": record["data"]}]

        if items is None:
            items = self._memory.get(buyer_id, [])

        self._memory[buyer_id] = items
        return sorted(items, key=lambda item: item.get("updated_at", item.get("created_at", 0)), reverse=True)

    async def get(self, buyer_id: int, tz_id: str) -> Optional[Dict[str, Any]]:
        for item in await self.list(buyer_id):
            if item.get("id") == tz_id:
                return item
        return None

    async def get_by_id(self, tz_id: str) -> Optional[Dict[str, Any]]:
        """Find a saved TZ by ID across all buyers."""
        for items in self._memory.values():
            for item in items:
                if item.get("id") == tz_id:
                    return item

        if self.collection is not None:
            async for record in self.collection.find({}):
                items = record.get("items") or []
                if not items and record.get("data"):
                    items = [{"id": "legacy", "created_at": 0, "data": record["data"]}]
                for item in items:
                    if item.get("id") == tz_id:
                        return item
        return None

    async def weekly_stats(self, since: float) -> List[Dict[str, Any]]:
        """Count newly created TZs since the given timestamp by buyer and flow."""
        records = []
        if self.collection is not None:
            async for record in self.collection.find({}):
                records.append(record)
        else:
            records = [
                {"_id": buyer_id, "items": items}
                for buyer_id, items in self._memory.items()
            ]

        stats: Dict[int, Dict[str, Any]] = {}
        for record in records:
            buyer_id = record.get("_id")
            if buyer_id is None:
                continue
            for item in record.get("items") or []:
                if item.get("created_at", 0) < since:
                    continue
                data = item.get("data") or {}
                buyer_stats = stats.setdefault(
                    buyer_id,
                    {
                        "buyer_id": buyer_id,
                        "buyer_label": item.get("buyer_label") or f"ID {buyer_id}",
                        "flows": {},
                        "total": 0,
                    },
                )
                flow = data.get("flow") or "unknown"
                buyer_stats["flows"][flow] = buyer_stats["flows"].get(flow, 0) + 1
                buyer_stats["total"] += 1

        return sorted(stats.values(), key=lambda item: item["buyer_label"].lower())

    async def save(
        self,
        buyer_id: int,
        data: Dict[str, Any],
        tz_id: Optional[str] = None,
        buyer_label: Optional[str] = None,
    ) -> str:
        items = await self.list(buyer_id)
        now = time()
        if tz_id is None:
            tz_id = uuid4().hex[:8]
            items.append({
                "id": tz_id,
                "created_at": now,
                "updated_at": now,
                "buyer_label": buyer_label or f"ID {buyer_id}",
                "data": data,
            })
        else:
            for item in items:
                if item.get("id") == tz_id:
                    item.update({"updated_at": now, "data": data})
                    break
            else:
                items.append({
                    "id": tz_id,
                    "created_at": now,
                    "updated_at": now,
                    "buyer_label": buyer_label or f"ID {buyer_id}",
                    "data": data,
                })

        self._memory[buyer_id] = items
        if self.collection is not None:
            await self.collection.replace_one({"_id": buyer_id}, {"_id": buyer_id, "items": items}, upsert=True)
        return tz_id


sent_tz_store = SentTZStore()
