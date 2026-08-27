from typing import Any, Dict, Optional


class SentTZStore:
    def __init__(self, collection=None):
        self.collection = collection
        self._memory: Dict[int, Dict[str, Any]] = {}

    async def save(self, buyer_id: int, data: Dict[str, Any]) -> None:
        record = {"_id": buyer_id, "data": data}
        self._memory[buyer_id] = data
        if self.collection is not None:
            await self.collection.replace_one({"_id": buyer_id}, record, upsert=True)

    async def get(self, buyer_id: int) -> Optional[Dict[str, Any]]:
        if self.collection is not None:
            record = await self.collection.find_one({"_id": buyer_id})
            if record:
                return record.get("data")
        return self._memory.get(buyer_id)


sent_tz_store = SentTZStore()
