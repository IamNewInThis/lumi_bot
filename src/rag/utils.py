# src/rag/utils.py
from src.rag.retriever import vs

async def get_rag_context(query: str, source: str | None = None) -> str:
    """
    Recupera contexto del RAG. Si 'source' es None, busca en todos los documentos
    y detecta el documento dominante automáticamente.
    """
    if source:
        # 🔎 Búsqueda restringida a un documento concreto
        docs = vs.similarity_search(query, k=5, filter={"source": source})
    else:
        # Paso 1: búsqueda en todos
        docs = vs.similarity_search(query, k=8)
        if not docs:
            return ""

        # Detectar documento dominante
        sources = {}
        for d in docs:
            src = d.metadata.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1

        main_source = max(sources, key=sources.get)
        print(f"🎯 Documento detectado: {main_source}")

        # Paso 2: repetir búsqueda filtrada en ese documento
        docs = vs.similarity_search(query, k=8, filter={"source": main_source})

    # Combinar chunks
    context = "\n\n".join([d.page_content for d in docs])
    return context