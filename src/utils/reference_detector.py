# src/utils/reference_detector.py
import json
from typing import List, Dict, Any, Optional
from ..rag.utils import get_rag_context_with_sources
from .source_cache import source_cache

class ReferenceDetector:
    """
    Detector especializado para consultas sobre referencias de las respuestas que da Lumi.
    Busca en el RAG registros que contengan metadata 'ref: true' para obtener fuentes específicas.
    """
    
    REFERENCE_KEYWORDS = {
        "fuentes", "referencias", "bibliografía", "origen de la información", 
        "de dónde sacaste", "de donde sacaste", "dónde obtuviste", "donde obtuviste",
        "qué fuentes", "que fuentes", "basado en qué", "basado en que",
        "según qué autor", "segun que autor", "qué estudios", "que estudios", 
        "investigaciones", "papers", "artículos", "articulos", "libros", 
        "evidencia científica", "evidencia cientifica", "respaldo científico", "respaldo cientifico",
        "autores", "expertos", "especialistas", "pedagogos", "médicos", "medicos",
        "neurocientíficos", "neurocientificos", "investigadores", 
        "dónde leíste", "donde leiste", "en qué te basas", "en que te basas",
        "esa informacion", "esa información", "esta informacion", "esta información"
    }
    
    @staticmethod
    def detect_reference_query(message: str) -> bool:
        """
        Detecta si el usuario está preguntando por referencias o fuentes.
        """
        message_lower = message.lower()
        detected_keywords = [kw for kw in ReferenceDetector.REFERENCE_KEYWORDS if kw in message_lower]
        
        if detected_keywords:
            print(f"🔍 [REFERENCIAS] Keywords detectadas: {detected_keywords}")
            return True
        
        return False
    
    @staticmethod
    async def get_reference_chunks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene chunks específicos que contienen referencias (ref: true).
        """
        try:
            # Hacer búsqueda RAG especial para referencias
            context, reference_chunks = await get_rag_context_with_sources(
                query, 
                search_id="references_query"
            )
            
            print(f"📚 [REFERENCIAS] Búsqueda RAG completada para: {query}")
            print(f"📚 [REFERENCIAS] Encontrados {len(reference_chunks)} chunks con referencias")
            
            # Limitar la cantidad de chunks si es necesario
            if len(reference_chunks) > limit:
                reference_chunks = reference_chunks[:limit]
            
            return reference_chunks
            
        except Exception as e:
            print(f"❌ Error obteniendo chunks de referencias: {e}")
            return []
    
    @staticmethod
    def format_references_response(reference_chunks: List[Dict[str, Any]]) -> str:
        """
        Formatea la respuesta con las referencias encontradas.
        """
        if not reference_chunks:
            return """
📚 **Sobre las fuentes de información**

Mi conocimiento se basa en una amplia base de datos que incluye:

• **Textos de referencia pedagógica**: Investigaciones sobre desarrollo infantil y pedagogías respetuosas
• **Investigaciones neurocientíficas**: Estudios sobre desarrollo cerebral y emocional en la infancia
• **Literatura médica**: Pediatría del desarrollo, lactancia y nutrición infantil
• **Metodologías educativas**: Enfoques pedagógicos centrados en el niño y el desarrollo autónomo

Para obtener referencias específicas sobre un tema particular, puedes preguntarme sobre un área concreta (por ejemplo: "¿qué referencias tienes sobre sueño infantil?" o "¿en qué te basas para hablar de destete?").
"""
        
        # Agrupar por fuente/categoría
        sources_by_category = {}
        for chunk in reference_chunks:
            category = chunk.get("category", "General")
            source = chunk.get("source", "Documento desconocido")
            
            if category not in sources_by_category:
                sources_by_category[category] = {}
            
            if source not in sources_by_category[category]:
                sources_by_category[category][source] = []
            
            sources_by_category[category][source].append(chunk)
        
        # Formatear respuesta
        response = "📚 **Referencias y fuentes consultadas**\n\n"
        
        for category, sources in sources_by_category.items():
            response += f"### {category}\n\n"
            
            for source, chunks in sources.items():
                response += f"**📄 {source.replace('_ref.pdf', '').replace('_', ' ').title()}**\n"
                
                # Mostrar contenido del primer chunk (suele ser el resumen de referencias)
                if chunks:
                    content = chunks[0].get("content", "")
                    if content:
                        # Truncar si es muy largo
                        if len(content) > 500:
                            content = content[:500] + "..."
                        response += f"{content}\n\n"
                
                response += "---\n\n"
        
        response += """
💡 **Nota**: Estas son las fuentes principales para el tema que consultaste. Si necesitas referencias sobre otros temas específicos, no dudes en preguntarme.
"""
        
        return response
    
    @staticmethod
    async def handle_reference_query(message: str, user_id: str) -> str:
        """
        Maneja una consulta específica sobre referencias.
        Prioriza usar las fuentes de la respuesta anterior si están disponibles.
        """
        
        # PASO 1: Intentar usar fuentes de la respuesta anterior
        cached_sources = source_cache.get_sources(user_id)
        
        if cached_sources:
            print(f"📋 [REFERENCIAS] ✅ CACHE ENCONTRADO para usuario {user_id[:8]}...")
            print(f"📋 [REFERENCIAS] Consulta original en cache: '{cached_sources['original_query']}'")
            print(f"📋 [REFERENCIAS] Documentos en cache: {cached_sources['sources']}")
            print(f"📋 [REFERENCIAS] Timestamp cache: {cached_sources['timestamp']}")
            
            # Buscar referencias en los documentos específicos de la respuesta anterior
            all_reference_chunks = []
            
            for source_file, reference_query in cached_sources["processed_sources"].items():
                print(f"🔍 [REFERENCIAS] Buscando referencias en {source_file} con query: {reference_query}")
                
                # Buscar específicamente en este documento de referencias
                try:
                    context, chunks = await get_rag_context_with_sources(
                        reference_query,
                        search_id=f"references_{source_file.replace('.pdf', '').replace('_ref', '')}"
                    )
                    
                    # Filtrar chunks que pertenecen al documento específico de referencias
                    source_chunks = [
                        chunk for chunk in chunks 
                        if chunk.get("source", "").lower() == source_file.lower()
                    ]
                    
                    all_reference_chunks.extend(source_chunks)
                    print(f"📚 [REFERENCIAS] Encontrados {len(source_chunks)} chunks de referencia en {source_file}")
                    
                    if source_chunks:
                        print(f"✅ [REFERENCIAS] Primeros chunks encontrados: {[chunk.get('source') for chunk in source_chunks[:3]]}")
                    
                except Exception as e:
                    print(f"❌ Error buscando referencias en {source_file}: {e}")
            
            if all_reference_chunks:
                print(f"✅ [REFERENCIAS] Total chunks de referencia encontrados: {len(all_reference_chunks)}")
                response = ReferenceDetector.format_references_response(all_reference_chunks)
                
                # Agregar contexto sobre de dónde vienen las referencias
                original_query = cached_sources.get("original_query", "la consulta anterior")
                context_note = f"\n\n🔗 **Contexto**: Estas referencias corresponden a tu consulta anterior sobre: *\"{original_query}\"*"
                
                return response + context_note
            else:
                print("⚠️ [REFERENCIAS] No se encontraron chunks de referencia en documentos específicos")
        else:
            print(f"❌ [REFERENCIAS] NO hay cache disponible para usuario {user_id[:8]}...")
            cache_stats = source_cache.get_cache_stats()
            print(f"❌ [REFERENCIAS] Stats cache global: {cache_stats}")
        
        # PASO 2: Fallback - búsqueda genérica por tema (comportamiento anterior)
        print("🔄 [REFERENCIAS] Usando búsqueda genérica por tema")
        
        # Extraer el tema específico de la consulta
        topic_keywords = {
            "sueño": "sueño infantil desarrollo nocturno",
            "lactancia": "lactancia materna pecho destete",
            "alimentación": "alimentación complementaria BLW",
            "comida": "alimentación complementaria BLW",
            "desarrollo": "desarrollo motor cognitivo emocional",
            "rutinas": "rutinas horarios estructura día",
            "llanto": "llanto autorregulación emociones",
            "apego": "apego vínculo relación maternal",
            "disciplina": "disciplina positiva límites",
            "emociones": "desarrollo emocional autorregulación"
        }
        
        message_lower = message.lower()
        specific_topic = None
        
        for topic, keywords in topic_keywords.items():
            if topic in message_lower:
                specific_topic = keywords
                break
        
        # Si no hay tema específico, usar consulta general
        search_query = specific_topic if specific_topic else "referencias bibliográficas fuentes autores investigaciones"
        
        # Obtener chunks de referencias
        reference_chunks = await ReferenceDetector.get_reference_chunks(search_query)
        
        # Formatear y devolver respuesta
        return ReferenceDetector.format_references_response(reference_chunks)