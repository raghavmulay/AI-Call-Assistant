"""services/rag_service.py — RAG query service for HTTP endpoints."""

from backend.app.ai.rag.rag_pipeline import answer


async def query(text: str) -> dict:
    response = await answer(text)
    return {"query": text, "answer": response}
