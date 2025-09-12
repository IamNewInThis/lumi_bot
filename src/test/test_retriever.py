# tests/test_retriever.py
import asyncio
from src.rag.utils import get_rag_context

async def main():
    queries = [
        "desgaste, drama y desconexión",
        "río del bienestar",
        "presencia emocional de los padres",
        "cómo manejar las rabietas y mantener la conexión con el niño",
        "importancia de la empatía y la presencia emocional en la crianza",
        "naves espaciales en la crianza"
    ]

    for q in queries:
        context = await get_rag_context(q)
        print(f"\n🔎 Query: {q}")
        print("Resultado:")
        print(context[:800], "..." if len(context) > 800 else "")

if __name__ == "__main__":
    asyncio.run(main())
