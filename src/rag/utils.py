from src.rag.retriever import vs
from collections import defaultdict

async def get_rag_context(query: str, k: int = 15, top_sources: int = 2) -> str:
    """
    Recupera contexto del RAG combinando los documentos más relevantes.
    Usa la similitud devuelta por Supabase para elegir los documentos dominantes.
    """

    # Paso 1: búsqueda global con similitud
    results = vs.similarity_search(query, k=k)
    if not results:
        return ""

    # OJO: SupabaseVectorStore devuelve documentos, pero en retriever.invoke(query)
    # puede traer (doc, score). Asegúrate de qué forma lo retorna.
    # Aquí asumimos que ya retorna docs con metadata.
    scores = defaultdict(list)

    for d in results:
        src = d.metadata.get("source", "unknown")
        sim = d.metadata.get("similarity", None)  # si tu integración añade similarity en metadata
        if sim is not None:
            scores[src].append(float(sim))

    # Calcular similitud promedio por source
    avg_scores = {src: sum(vals)/len(vals) for src, vals in scores.items()} if scores else {}

    # Si no hay similarity en metadata, fallback: contar ocurrencias
    if not avg_scores:
        for d in results:
            src = d.metadata.get("source", "unknown")
            scores[src].append(1)
        avg_scores = {src: sum(vals)/len(vals) for src, vals in scores.items()}

    # Elegir top fuentes
    best_sources = sorted(avg_scores, key=avg_scores.get, reverse=True)[:top_sources]
    print(f"🎯 Documentos dominantes detectados: {best_sources}")

    # Paso 2: búsqueda refinada en esas fuentes
    combined = []
    for src in best_sources:
        filtered = vs.similarity_search(query, k=5, filter={"source": src})
        # filtered = vs.similarity_search("desgaste, drama y desconexión", k=5, filter={"source": "disciplina_sin_lagrimas.pdf"})
        # print([d.page_content[:120] for d in filtered])
        combined.extend(filtered)

    # Fallback si no hubo nada
    if not combined:
        combined = results

    # Concatenar chunks
    context = "\n\n".join([d.page_content for d in combined])
    return context
