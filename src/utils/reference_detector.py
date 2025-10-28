# src/utils/reference_detector.py
import json
from typing import List, Dict, Any, Optional
from ..rag.utils import get_rag_context_with_sources, get_all_reference_chunks_from_file
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
        "esa informacion", "esa información", "esta informacion", "esta información", "de donde es esa info"
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
        Formatea la respuesta con las referencias encontradas de forma resumida y general.
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
        
        # Recopilar información de todas las fuentes
        has_ref_chunks = any(chunk.get("ref") is True for chunk in reference_chunks)
        sources = list(set(chunk.get("source", "").replace('_ref.pdf', '').replace('.pdf', '') for chunk in reference_chunks))
        
        # Extraer autores y referencias mencionadas en los chunks
        all_content = " ".join([chunk.get("content", "") for chunk in reference_chunks])
        
        # Buscar patrones de referencias comunes
        reference_patterns = {
            "autores": [],
            "instituciones": [],
            "estudios": [],
            "publicaciones": []
        }
        
        # Buscar autores mencionados (nombres propios seguidos de apellidos)
        import re
        
        # Patrones mejorados para detectar referencias académicas
        # Buscar nombres de autores (nombre + apellido, evitando falsos positivos)
        author_patterns = [
            r'\bde\s+([A-Z][a-záéíóúñ]{2,})\s+([A-Z][a-záéíóúñ]{2,})\b',  # de Nombre Apellido  
            r'\bdel\s+([A-Z][a-záéíóúñ]{2,})\s+([A-Z][a-záéíóúñ]{2,})\b', # del Nombre Apellido
            r'\b([A-Z][a-záéíóúñ]{2,})\s+([A-Z][a-záéíóúñ]{2,})\b',  # Nombre Apellido general
            r'\b([A-Z][a-záéíóúñ]{2,})\s+y\s+([A-Z][a-záéíóúñ]{2,})\b'  # Nombre y Apellido
        ]
        
        # Palabras a excluir (no son nombres de autores)
        excluded_words = {
            'Essential', 'Oil', 'Safety', 'Guide', 'Health', 'Care', 'Professionals',
            'European', 'Medicines', 'Agency', 'American', 'Herbal', 'Products', 'Association',
            'Council', 'International', 'National', 'Alliance', 'Aromatherapy', 'Holistic'
        }
        
        authors_found = []
        for pattern in author_patterns:
            matches = re.findall(pattern, all_content)
            for match in matches:
                if isinstance(match, tuple):
                    # Para el patrón "Nombre y Apellido", crear dos autores separados
                    if ' y ' in f"{match[0]} {match[1]}":
                        authors_found.append(match[0])
                        authors_found.append(match[1])
                    else:
                        full_name = f"{match[0]} {match[1]}"
                        # Verificar que no sea una palabra excluida
                        words = full_name.split()
                        if not any(word in excluded_words for word in words) and len(full_name) > 5:
                            authors_found.append(full_name)
                else:
                    full_name = match
                    words = full_name.split()
                    if not any(word in excluded_words for word in words) and len(full_name) > 5:
                        authors_found.append(full_name)
        
        # Limpiar duplicados y limitar
        authors_found = list(set(authors_found))[:5]
        
        # Buscar instituciones y organizaciones
        institution_patterns = [
            r'\b(European Medicines Agency)\s*\([^)]*\)?',
            r'\b(American Herbal Products Association)\s*\([^)]*\)?', 
            r'\b(National Association for Holistic Aromatherapy)\s*\([^)]*\)?',
            r'\b(Alliance of International Aromatherapists)\s*\([^)]*\)?',
            r'\b([A-Z][a-záéíóúñ\s]{15,60}(?:Agency|Association|Council|Institute|Organization|Academy))\b'
        ]
        
        institutions_found = []
        for pattern in institution_patterns:
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 5:
                    inst_clean = match.strip()
                    # Remover siglas entre paréntesis al final
                    inst_clean = re.sub(r'\s*\([^)]*\)$', '', inst_clean)
                    if len(inst_clean) > 50:
                        inst_clean = inst_clean[:50] + "..."
                    institutions_found.append(inst_clean)
        
        # Limpiar duplicados y limitar
        institutions_found = list(set(institutions_found))[:4]
        
        # Construir respuesta resumida
        response = "📚 **Referencias y fuentes consultadas**\n\n"
        
        response += "La información proporcionada se basa en documentación científica y técnica que incluye:\n\n"
        
        # Agregar autores si se encontraron
        if authors_found:
            response += f"**👥 Autores y especialistas mencionados:**\n"
            for author in authors_found:
                response += f"• {author}\n"
            response += "\n"
        
        # Agregar instituciones si se encontraron
        if institutions_found:
            response += f"**🏛️ Instituciones y organismos de referencia:**\n"
            for institution in institutions_found:
                response += f"• {institution}\n"
            response += "\n"
        
        # Describir el tipo de evidencia
        if has_ref_chunks:
            response += "**📖 Tipos de evidencia consultada:**\n"
            response += "• Estudios científicos revisados por pares\n"
            response += "• Investigaciones en neurociencia del desarrollo\n"
            response += "• Guías de organismos internacionales de salud\n"
            response += "• Literatura especializada en pediatría y desarrollo infantil\n"
            response += "• Enfoques de crianza respetuosa basados en evidencia\n\n"
        else:
            response += "**📖 Fuentes de información:**\n"
            response += "• Documentación especializada en desarrollo infantil\n"
            response += "• Textos de referencia en pediatría y crianza\n"
            response += "• Enfoques pedagógicos centrados en el niño\n\n"
        
        # Nota explicativa
        if has_ref_chunks:
            response += "💡 **Nota**: Estas referencias representan la base científica y técnica que fundamenta la información proporcionada.\n"
        else:
            response += "💡 **Nota**: Esta información proviene de documentación especializada. Las referencias específicas se están actualizando en el sistema.\n"
        
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
                print(f"🔍 [REFERENCIAS] Obteniendo TODOS los chunks de referencia de {source_file}")
                
                # Usar la nueva función que obtiene TODOS los chunks de referencia sin query semántica
                try:
                    source_chunks = await get_all_reference_chunks_from_file(
                        source_file, 
                        search_id=f"all_refs_{source_file.replace('.pdf', '').replace('_ref', '')}"
                    )
                    
                    # FALLBACK: Si no encontramos chunks en archivo _ref, buscar en archivo original
                    if not source_chunks and source_file.endswith('_ref.pdf'):
                        original_file = source_file.replace('_ref.pdf', '.pdf')
                        print(f"🔄 [REFERENCIAS] No encontrado en {source_file}, buscando en {original_file}")
                        
                        source_chunks = await get_all_reference_chunks_from_file(
                            original_file, 
                            search_id=f"fallback_{original_file.replace('.pdf', '')}"
                        )
                        
                        if source_chunks:
                            print(f"✅ [REFERENCIAS] FALLBACK exitoso: encontrados chunks en {original_file}")
                    
                    all_reference_chunks.extend(source_chunks)
                    print(f"📚 [REFERENCIAS] Encontrados {len(source_chunks)} chunks de referencia en {source_file}")
                    
                    if source_chunks:
                        print(f"✅ [REFERENCIAS] Primeros chunks encontrados: {[chunk.get('source') for chunk in source_chunks[:3]]}")
                    
                except Exception as e:
                    print(f"❌ Error obteniendo chunks de referencia de {source_file}: {e}")
            
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