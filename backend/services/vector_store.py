import re
from uuid import UUID, uuid4

import httpx

from backend.config import get_settings

VECTOR_SIZE = 1536


def collection_name(notebook_id: UUID | str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", f"notebook_{notebook_id}".lower())


class VectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def embed(self, text: str) -> list[float]:
        if not self.settings.openai_api_key:
            return [0.0] * VECTOR_SIZE
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": "text-embedding-3-small", "input": text},
            )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    async def ensure_collection(self, notebook_id: UUID) -> None:
        name = collection_name(notebook_id)
        async with httpx.AsyncClient(timeout=20) as client:
            existing = await client.get(f"{self.settings.qdrant_url}/collections/{name}")
            if existing.status_code == 200:
                return
            response = await client.put(
                f"{self.settings.qdrant_url}/collections/{name}",
                json={"vectors": {"size": VECTOR_SIZE, "distance": "Cosine"}},
            )
            response.raise_for_status()

    async def upsert_memory(self, notebook_id: UUID, content: str, memory_id: UUID) -> str:
        await self.ensure_collection(notebook_id)
        vector = await self.embed(content)
        point_id = str(uuid4())
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.put(
                f"{self.settings.qdrant_url}/collections/{collection_name(notebook_id)}/points",
                json={
                    "points": [
                        {
                            "id": point_id,
                            "vector": vector,
                            "payload": {"memory_id": str(memory_id), "content": content},
                        }
                    ]
                },
            )
            response.raise_for_status()
        return point_id

    async def search(self, notebook_id: UUID, query: str, top_k: int = 3) -> list[dict]:
        await self.ensure_collection(notebook_id)
        vector = await self.embed(query)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.settings.qdrant_url}/collections/{collection_name(notebook_id)}/points/search",
                json={"vector": vector, "limit": top_k, "with_payload": True},
            )
        if response.status_code >= 400:
            return []
        return response.json().get("result", [])

    async def delete_point(self, notebook_id: UUID, qdrant_id: str) -> None:
        async with httpx.AsyncClient(timeout=20) as client:
            await client.post(
                f"{self.settings.qdrant_url}/collections/{collection_name(notebook_id)}/points/delete",
                json={"points": [qdrant_id]},
            )


vector_store = VectorStore()
