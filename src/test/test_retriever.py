# tests/test_retriever.py
import asyncio
from src.rag.utils import get_rag_context

async def main():
    queries = [
        ("río del bienestar", None),
        ("desgaste, drama y desconexión", None),
    ]

    for q, source in queries:
        print(f"\n🔎 Query: {q}")
        context = await get_rag_context(q, source=source)
        print("Resultado del retriever:")
        print(context[:500], "..." if len(context) > 500 else "")

if __name__ == "__main__":
    asyncio.run(main())
