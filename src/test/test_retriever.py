# tests/test_retriever.py
import asyncio
from src.rag.utils import get_rag_context

async def main():
    query = "río del bienestar"
    context = await get_rag_context(query)
    print("🔎 Resultado del retriever:")
    print(context)

if __name__ == "__main__":
    asyncio.run(main())
