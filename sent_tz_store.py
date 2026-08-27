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

    async def save(self, buyer_id: int, data: Dict[str, Any], tz_id: Optional[str] = None) -> str:
        items = await self.list(buyer_id)
        now = time()
        if tz_id is None:
            tz_id = uuid4().hex[:8]
            items.append({"id": tz_id, "created_at": now, "updated_at": now, "data": data})
        else:
            for item in items:
                if item.get("id") == tz_id:
                    item.update({"updated_at": now, "data": data})
                    break
            else:
                items.append({"id": tz_id, "created_at": now, "updated_at": now, "data": data})

        self._memory[buyer_id] = items
        if self.collection is not None:
            await self.collection.replace_one({"_id": buyer_id}, {"_id": buyer_id, "items": items}, upsert=True)
        return tz_id


sent_tz_store = SentTZStore()
