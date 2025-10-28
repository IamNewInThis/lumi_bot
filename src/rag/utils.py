from src.rag.retriever import vs
from collections import defaultdict
from typing import Tuple, List, Dict, Any

# Consultar hasta 3 documentos para contexto
def get_rag_context(query: str, k: int = 20, top_sources: int = 3, search_id: str = "main") -> Tuple[str, List[str]]:
    """
    Recupera contexto del RAG combinando los documentos más relevantes.
    Usa una estrategia híbrida para asegurar cobertura de documentos relevantes.
    
    Returns:
        Tuple[str, List[str]]: (contexto_texto, lista_de_fuentes_consultadas)
    """

    # Paso 1: búsqueda global más amplia
    results = vs.similarity_search(query, k=k)
      # 🔹 Paso 1: fallback con keywords si no hay resultados del vector store
    if not results:
        keyword_sources = []
        for keyword, docs in keyword_mapping.items():
            if keyword in query.lower():
                keyword_sources.extend(docs)

        if keyword_sources:
            # puedes simular resultados artificiales basados en keywords
            return " ".join(keyword_sources), keyword_sources

        # si tampoco hay keywords relevantes
        return "", []
    # Contar ocurrencias por fuente
    source_counts = defaultdict(int)
    for d in results:
        src = d.metadata.get("source", "unknown")
        source_counts[src] += 1

    # Elegir top fuentes basado en frecuencia
    best_sources = sorted(source_counts, key=source_counts.get, reverse=True)[:top_sources]
    
    # Paso 2: Búsqueda específica por palabras clave para asegurar cobertura
    keyword_sources = []
    
    # Mapeo de palabras clave a documentos específicos
    keyword_mapping = {
        # 🧠 DISCIPLINA Y LÍMITES
        'disciplina': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
        'limites': ['limites.pdf', 'libertad.pdf'],
        'normas': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
        'reglas': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],
        'obediencia': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
        'autoridad': ['limites.pdf', 'disciplina_sin_lagrimas.pdf'],


        # 🚫 CASTIGOS Y CONSECUENCIAS
        'castigos': ['disciplina_sin_lagrimas.pdf'],
        'consecuencias': ['disciplina_sin_lagrimas.pdf', 'limites.pdf'],
        'regaños': ['disciplina_sin_lagrimas.pdf'],
        'correcciones': ['disciplina_sin_lagrimas.pdf'],


        # 😡 RABIETAS Y EMOCIONES INTENSAS
        'rabietas': ['disciplina_sin_lagrimas.pdf'],
        'berrinches': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
        'pataletas': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
        'frustracion': ['emociones.pdf', 'disciplina_sin_lagrimas.pdf'],


        # ⚔️ CONFLICTOS / CELOS / HERMANOS
        'conflictos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'hermanos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'celos': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf', 'limites.pdf'],
        'rivalidad': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'peleas': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf', 'limites.pdf'],
        'discusiones': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf'],
        'compartir': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'territorialidad': ['disciplina_sin_lagrimas.pdf', 'emociones.pdf', 'el_cerebro_del_nino.pdf', 'limites.pdf'],
        'juguetes': ['el_cerebro_del_nino.pdf', 'emociones.pdf'],
        'posesion': ['el_cerebro_del_nino.pdf', 'emociones.pdf'],


        # 🧩 SOBREESTIMULACIÓN / EXCESOS
        'sobreestimulacion': ['simplicity_parenting.pdf'],
        'exceso': ['simplicity_parenting.pdf', 'limites.pdf', 'el_cerebro_del_nino.pdf'],
        'saturacion': ['simplicity_parenting.pdf'],
        'estres': ['simplicity_parenting.pdf', 'emociones.pdf'],
        'demasiado': ['simplicity_parenting.pdf'],


        # 🕒 RUTINA Y ACTIVIDADES
        'rutina': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
        'habitos': ['rutina_del_bebe.pdf', 'simplicity_parenting.pdf'],
        'horarios': ['rutina_del_bebe.pdf'],
        'actividades': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf', 'el_cerebro_del_nino.pdf'],
        'estructura': ['simplicity_parenting.pdf', 'rutina_del_bebe.pdf'],


        # 🌙 SUEÑO / DESCANSO - ES
        'sueno': ['sueño_infantil.pdf'],
        'dormir': ['sueño_infantil.pdf', 'bedtime.pdf', 'dormir_en_su_cuna.pdf'],
        'siestas': ['sueño_infantil.pdf', 'siestas.pdf'],
        'despertares': ['sueño_infantil.pdf', 'alteraciones_del_sueño.pdf'],
        'cuna': ['sueño_infantil.pdf', 'dormir_en_su_cuna.pdf'],
        'destete nocturno': ['sueño_infantil.pdf', 'destete_lumi.pdf'],
        
        # 🌙 SLEEP / REST - EN
        'sleepy': ['sueño_infantil.pdf'],
        'sleep': ['sueño_infantil.pdf', 'bedtime.pdf', 'dormir_en_su_cuna.pdf'],
        'nap': ['sueño_infantil.pdf', 'siestas.pdf'],
        'awaken': ['sueño_infantil.pdf', 'alteraciones_del_sueño.pdf'],
        'cradle': ['sueño_infantil.pdf', 'dormir_en_su_cuna.pdf'],
        'night weaning': ['sueño_infantil.pdf', 'destete_lumi.pdf'],


        # 🍎 ALIMENTACIÓN / INGESTA / COMIDA
        'alimentacion': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
        'alimentos': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
        'ingesta': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
        'comida': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
        'papillas': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
        'solidos': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],
        'lactancia': ['child_of_mine_feeding.pdf', 'el_cerebro_del_nino.pdf'],


        # ❤️ EMOCIONES / CRIANZA RESPETUOSA
        'emociones': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'crianza respetuosa': ['emociones.pdf', 'libertad.pdf', 'simplicity_parenting.pdf'],
        'respetuosa': ['emociones.pdf', 'libertad.pdf'],
        'vinculo': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'conexion': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],
        'empatia': ['emociones.pdf', 'el_cerebro_del_nino.pdf'],


        # ✈️ VIAJES / TRASLADOS / MOVILIDAD
        'viajes': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'vacaciones': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'traslados': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'salidas': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'paseos': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'avion': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'auto': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
        'bus': ['viajes_con_ninos_mc.pdf', 'tips_viajes_r.pdf'],
    }

    
    query_lower = query.lower()
    for keyword, sources in keyword_mapping.items():
        if keyword in query_lower:
            keyword_sources.extend(sources)
    
    # Combinar fuentes: priorizar keywords, luego frecuencia
    final_sources = []
    
    # Primero agregar fuentes de keywords (alta prioridad)
    for src in keyword_sources:
        if src not in final_sources:
            final_sources.append(src)
    
    # Luego agregar fuentes por frecuencia hasta completar top_sources
    for src in best_sources:
        if src not in final_sources and len(final_sources) < top_sources:
            final_sources.append(src)
    
    print(f"🎯 [{search_id.upper()}] Documentos dominantes detectados context: {final_sources}")

    # Paso 3: búsqueda refinada en esas fuentes
    combined = []
    for src in final_sources:
        filtered = vs.similarity_search(query, k=5, filter={"source": src})
        combined.extend(filtered)

    # Fallback si no hubo nada
    if not combined:
        combined = results

    # Concatenar chunks
    context = "\n\n".join([d.page_content for d in combined])
    return context, final_sources

def get_rag_context_simple(query: str, k: int = 20, top_sources: int = 3, search_id: str = "main") -> str:
    """
    Versión simple que solo retorna el contexto (para compatibilidad hacia atrás).
    """
    context, sources = get_rag_context(query, k, top_sources, search_id)
    return context

async def get_all_reference_chunks_from_file(source_file: str, search_id: str = "references") -> List[Dict[str, Any]]:
    """
    Obtiene chunks relevantes de un archivo específico para consultas de referencias.
    Prioriza chunks con ref=true, pero si no los encuentra, devuelve chunks relevantes del archivo.
    
    Args:
        source_file: Nombre del archivo (ej: 'ae_ref.pdf' o 'ae.pdf')
        search_id: ID para logging
    
    Returns:
        List[Dict]: Lista de chunks con metadata completa
    """
    try:
        # Buscar todos los chunks de este archivo específico usando un filtro amplio
        # Usamos una query muy genérica para obtener todos los chunks del archivo
        all_chunks = vs.similarity_search(
            "información contenido documento", 
            k=1000,  # Número alto para obtener todos los chunks
            filter={"source": source_file}
        )
        
        print(f"🔍 [{search_id.upper()}] Encontrados {len(all_chunks)} chunks totales en {source_file}")
        
        if not all_chunks:
            print(f"❌ [{search_id.upper()}] No se encontraron chunks en {source_file}")
            return []
        
        # Convertir a formato dict
        all_chunks_data = []
        for doc in all_chunks:
            chunk_data = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown"),
                "ref": doc.metadata.get("ref", False),
                "type": doc.metadata.get("type", "unknown"),
                "chunk": doc.metadata.get("chunk", 0),
                "version": doc.metadata.get("version", 1),
                "category": doc.metadata.get("category", "General")
            }
            all_chunks_data.append(chunk_data)
        
        # Filtrar chunks que tienen ref=true (prioridad)
        reference_chunks = [chunk for chunk in all_chunks_data if chunk.get("ref") is True]
        
        if reference_chunks:
            print(f"✅ [{search_id.upper()}] Encontrados {len(reference_chunks)} chunks con ref=true en {source_file}")
            return reference_chunks
        else:
            # Si no hay chunks con ref=true, devolver los primeros chunks del archivo como fallback
            print(f"⚠️ [{search_id.upper()}] No hay chunks con ref=true en {source_file}")
            print(f"🔄 [{search_id.upper()}] Usando chunks generales como fallback (primeros 3)")
            
            # Devolver máximo 3 chunks como muestra del contenido
            fallback_chunks = all_chunks_data[:3]
            return fallback_chunks
        
    except Exception as e:
        print(f"❌ Error obteniendo chunks de {source_file}: {e}")
        return []

async def get_rag_context_with_sources(query: str, k: int = 20, top_sources: int = 3, search_id: str = "references") -> Tuple[str, List[Dict[str, Any]]]:
    """
    Versión especial de get_rag_context que devuelve tanto el contexto como los chunks con metadata.
    Especialmente útil para consultas de referencias que necesitan acceso a metadata como 'ref: true'.
    
    Returns:
        Tuple[str, List[Dict]]: (contexto_texto, lista_de_chunks_con_metadata)
    """
    
    # Paso 1: búsqueda global más amplia
    results = vs.similarity_search(query, k=k)
    if not results:
        return "", []

    # Contar ocurrencias por fuente
    source_counts = defaultdict(int)
    for d in results:
        src = d.metadata.get("source", "unknown")
        source_counts[src] += 1

    # Elegir top fuentes basado en frecuencia
    best_sources = sorted(source_counts, key=source_counts.get, reverse=True)[:top_sources]
    
    print(f"🎯 [{search_id.upper()}] Documentos dominantes detectados sources: {best_sources}")

    # Paso 2: búsqueda refinada en esas fuentes
    combined = []
    for src in best_sources:
        filtered = vs.similarity_search(query, k=5, filter={"source": src})
        combined.extend(filtered)

    # Fallback si no hubo nada
    if not combined:
        combined = results

    # Preparar contexto y chunks con metadata
    context = "\n\n".join([d.page_content for d in combined])
    
    # Convertir chunks a formato dict con metadata completa
    chunks_with_metadata = []
    for doc in combined:
        chunk_data = {
            "content": doc.page_content,
            "metadata": doc.metadata,
            # Extraer campos específicos de metadata para fácil acceso
            "source": doc.metadata.get("source", "unknown"),
            "ref": doc.metadata.get("ref", False),
            "type": doc.metadata.get("type", "unknown"),
            "chunk": doc.metadata.get("chunk", 0),
            "version": doc.metadata.get("version", 1),
            "category": doc.metadata.get("category", "General")
        }
        chunks_with_metadata.append(chunk_data)
    
    # Filtrar chunks que tienen ref: true para referencias
    reference_chunks = [chunk for chunk in chunks_with_metadata if chunk.get("ref") is True]
    
    print(f"📚 [{search_id.upper()}] Total chunks: {len(chunks_with_metadata)}, Chunks con ref=true: {len(reference_chunks)}")
    
    return context, reference_chunks
