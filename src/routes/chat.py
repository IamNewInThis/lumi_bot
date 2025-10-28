# src/routes/chat.py
import os
import httpx
import unicodedata
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pathlib import Path
from typing import List
from ..models.chat import ChatRequest, KnowledgeConfirmRequest
from ..auth import get_current_user
from src.rag.utils import get_rag_context, get_rag_context_simple
from src.utils.date_utils import calcular_edad, calcular_meses
from ..rag.retriever import supabase
from ..utils.knowledge_detector import KnowledgeDetector
from ..services.knowledge_service import BabyKnowledgeService
from ..utils.knowledge_cache import confirmation_cache
from ..utils.routine_detector import RoutineDetector
from ..services.routine_service import RoutineService
from ..utils.routine_cache import routine_confirmation_cache
from ..utils.reference_detector import ReferenceDetector
from ..utils.source_cache import source_cache

router = APIRouter()
today = datetime.now().strftime("%d/%m/%Y %H:%M")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

if not OPENAI_KEY:
    raise RuntimeError("Falta OPENAI_API_KEY en variables de entorno (.env)")

print(f"🤖 Usando modelo OpenAI: {OPENAI_MODEL}")

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SECTIONS_DIR = PROMPTS_DIR / "sections"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
EXAMPLES_DIR = PROMPTS_DIR / "examples"

# Establecer palabras clave para detección de temas
ROUTINE_KEYWORDS = {
    "organizar rutina", "organizar la rutina", "ajustar horarios", "cambiar horarios",
    "estructurar el día", "horarios de comida", "horarios de sueño",
    "rutina de sueño", "orden del día", "cronograma", "planificar el día",
    "horarios del bebé", "rutina diaria", "establecer rutina", "fijar horarios",
    "hacer una rutina", "hacer rutina", "quiero rutina", "crear rutina",
    "armar rutina", "armar una rutina", "necesito rutina", "rutina para",
    "una rutina para", "rutina", "horarios", "organizar el día"
}

NIGHT_WEANING_KEYWORDS = {
    "tomas nocturnas", "destete nocturno", "desmame nocturno", "disminuir tomas",
    "reducir tomas", "quitar tomas", "noches sin pecho", "lorena furtado"
}

PARTNER_KEYWORDS = {
    "pareja", "esposo", "papá", "padre", "dividir", "trabajo nocturno",
    "acompañar", "turno", "por turnos", "con mi pareja"
}

BEHAVIOR_KEYWORDS = {
    "llora", "llanto", "llorando", "ruido", "grita", "alega", "canta",
    "gruñe", "hace sonido", "vocaliza", "emite", "sonido raro", "llanto diferente",
    "se queja", "tararea", "canturrea", "murmura", "susurra"
}

GREETING_PHRASES = {
    "hola",
    "hola lumi",
    "hola hola",
    "buen dia",
    "buenos dias",
    "buenas",
    "buenas tardes",
    "buenas noches",
    "hello",
    "hi",
    "hey",
    "saludos",
    "hola buen dia",
    "hola buenos dias",
    "hola buenas",
    "hola buenas tardes",
    "hola buenas noches"
}

def normalize_for_greeting(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(
        ch
        if unicodedata.category(ch) != "Mn" and (ch.isalnum() or ch.isspace())
        else " "
        for ch in text
    )
    return " ".join(text.split())

def is_simple_greeting(message: str) -> bool:
    normalized = normalize_for_greeting(message)
    return normalized in GREETING_PHRASES

def load_instruction_dataset():
    """
    Carga el dataset de ejemplos, estos ejemplos fueron tomados desde el GPT de Sol
    Para darle un mejor contexto al modelo de como debe responder.
    ubicado en prompts/examples y lo incluye como guía semántica base.
    """
    candidate_paths = [
        EXAMPLES_DIR / "lumi_instruction_dataset_v1.md",
        PROMPTS_DIR / "system" / "lumi_instruction_dataset_v1.md",
    ]

    dataset_path = next((path for path in candidate_paths if path.exists()), None)
    if dataset_path:
        with open(dataset_path, "r", encoding="utf-8") as dataset_file:
            content = dataset_file.read().strip()
            header = "## DATASET DE INSTRUCCIONES LUMI (v1)\nUsar como guía semántica general para tono, estructura y progresión de respuesta.\n\n"
            return header + content
    return ""

def load_system_prompt(section_files=None):
    """
        Carga el prompt base y concatena secciones adicionales según sea necesario.
        `section_files` debe ser una lista de nombres de archivo (por ejemplo, ["style.md"]).
    """
    candidate_paths = [
        PROMPTS_DIR / "system_prompt_base.md",
        PROMPTS_DIR / "system" / "system_prompt_base.md",
    ]

    base_path = next((path for path in candidate_paths if path.exists()), None)
    if not base_path:
        raise RuntimeError(
            "No se encontró el archivo base del prompt. "
            f"Rutas probadas: {', '.join(str(p) for p in candidate_paths)}"
        )

    with open(base_path, "r", encoding="utf-8") as f:
        parts = [f.read().strip()]

    system_dir = base_path.parent
    additional_system_files = [
        "system_operational_rules.md",
        "system_style_guide.md",
    ]

    for filename in additional_system_files:
        system_path = system_dir / filename
        if system_path.exists():
            with open(system_path, "r", encoding="utf-8") as system_file:
                parts.append(system_file.read().strip())
        else:
            print(f"⚠️ Archivo de sistema no encontrado: {system_path}")

    if section_files:
        seen = set()
        for filename in section_files:
            if filename in seen:
                continue
            seen.add(filename)
            section_path = SECTIONS_DIR / filename
            if section_path.exists():
                with open(section_path, "r", encoding="utf-8") as section_file:
                    parts.append(section_file.read().strip())
            else:
                print(f"⚠️ Sección de prompt no encontrada: {section_path}")

    return "\n\n".join(parts)

def detect_consultation_type_and_load_template(message):
    """
        Detecta el tipo de consulta y carga el template específico correspondiente.
    """
    message_lower = message.lower()
    
    # Palabras clave para rutinas
    routine_keywords = ["rutina", "organizar", "horarios", "estructura", "día completo"]
    if any(keyword in message_lower for keyword in routine_keywords):
        template_path = TEMPLATES_DIR / "template_rutinas.md"
        if template_path.exists():
            print(f"🚀 Cargando template de rutinas desde: {template_path}")
            with open(template_path, "r", encoding="utf-8") as f:
                return f"\n\n## TEMPLATE ESPECÍFICO PARA RUTINAS MEJORADAS:\n\n{f.read()}"
        else:
            print(f"⚠️ Template de rutinas no encontrado: {template_path}")
    
    # Palabras clave para ideas creativas de alimentos
    creative_food_keywords = ["ideas creativas", "presentar", "verduras", "alimentos", "menú", "comida"]
    if any(keyword in message_lower for keyword in creative_food_keywords):
        template_path = TEMPLATES_DIR / "template_ideas_creativas_alimentos.md"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f"\n\n## TEMPLATE ESPECÍFICO PARA IDEAS CREATIVAS DE ALIMENTOS:\n\n{f.read()}"
            
    # Palabras clave para viajes con niños
    travels_keywords = ["viajar", "viajes", "viaje", "destino", "destinos", "vacaciones", "niños", "familia"]
    if any(keyword in message_lower for keyword in travels_keywords):
        template_path = TEMPLATES_DIR / "travel_with_children.md"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f"\n\n## TEMPLATE ESPECÍFICO PARA VIAJES CON NIÑOS:\n\n{f.read()}"
    
    # Palabras clave para destete y lactancia
    weaning_keywords = ["destete", "reducir tomas", "dejar pecho", "tomas nocturnas", "descansar mejor", 
                       "transición lactancia", "lactancia", "pecho", "mamar", "teta"]
    if any(keyword in message_lower for keyword in weaning_keywords):
        template_path = TEMPLATES_DIR / "template_destete_lactancia.md"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f"\n\n## TEMPLATE ESPECÍFICO PARA DESTETE Y LACTANCIA:\n\n{f.read()}"
            
    # Palabras claves para detectar solicitud de referencias de las respuesta
    references_keywords = ["fuentes", "referencias", "bibliografía", "origen de la información", "de dónde sacaste", "dónde obtuviste", "qué fuentes", "basado en qué"]
    if any(keyword in message_lower for keyword in references_keywords):
        template_path = TEMPLATES_DIR / "template_referencias.md"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                return f"\n\n## TEMPLATE ESPECÍFICO PARA REFERENCIAS:\n\n{f.read()}"

    return ""

def format_llm_output(text):
    """Limpia y formatea la salida del LLM para que sea más natural y legible."""
    # Limpiar exceso de símbolos de markdown
    text = text.replace("###", "##")
    text = text.replace("****", "**")
    
    # Remover líneas vacías excesivas
    import re
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    # Limpiar espacios al inicio y final
    text = text.strip()
    
    return text

async def get_user_profiles_and_babies(user_id, supabase_client, baby_id=None, babies_data=None):
    """
        Recupera perfiles y bebés del usuario y formatea el contexto.
        Si se proporciona baby_id, limita el contexto a ese bebé.
    """
    profiles = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
    if babies_data is None:
        babies_response = supabase_client.table("babies").select("*").eq("user_id", user_id).execute()
        babies_data = babies_response.data or []

    babies_data = babies_data or []
    selected_babies = babies_data
    if baby_id:
        selected_babies = [b for b in babies_data if b["id"] == baby_id]
        # Si no se encuentra el baby_id, mantener todos para no dejar sin contexto
        if not selected_babies:
            selected_babies = babies_data
        else:
            print(f"👶 Bebé seleccionado para contexto: {selected_babies[0]['name']} ({baby_id})")

    # Obtener conocimiento específico
    if baby_id and selected_babies:
        baby = selected_babies[0]
        knowledge_items = await BabyKnowledgeService.get_baby_knowledge(user_id, baby_id)
        knowledge_by_baby = {
            baby_id: {
                "baby_name": baby["name"],
                "knowledge": knowledge_items
            }
        }
    else:
        knowledge_by_baby = await BabyKnowledgeService.get_all_user_knowledge(user_id)
    knowledge_context = BabyKnowledgeService.format_knowledge_for_context(knowledge_by_baby)
    
    # Obtener rutinas
    if baby_id and selected_babies:
        baby = selected_babies[0]
        routines_list = await RoutineService.get_user_routines(user_id, baby_id)
        routines_by_baby = {
            baby["name"]: routines_list
        }
    else:
        routines_by_baby = await RoutineService.get_all_user_routines(user_id)
    routines_context = RoutineService.format_routines_for_context(routines_by_baby)

    profile_texts = [
        f"- Perfil: {p['name']}, fecha de nacimiento {p['birthdate']}, alimentación: {p.get('feeding', 'N/A')}"
        for p in profiles.data
    ] if profiles.data else []

    baby_texts = []
    if selected_babies:
        for b in selected_babies:
            edad_anios = calcular_edad(b["birthdate"])
            edad_meses = calcular_meses(b["birthdate"])

            # Determinar etapa de desarrollo
            etapa_desarrollo = ""
            if edad_meses <= 6:
                etapa_desarrollo = "lactante"
            elif edad_meses <= 12:
                etapa_desarrollo = "bebé"
            elif edad_meses <= 24:
                etapa_desarrollo = "caminador/toddler"
            elif edad_anios <= 5:
                etapa_desarrollo = "preescolar"
            elif edad_anios <= 12:
                etapa_desarrollo = "escolar"
            else:
                etapa_desarrollo = "adolescente"

            baby_texts.append(
                f"- Bebé: {b['name']}, fecha de nacimiento {b['birthdate']}, "
                f"edad: {edad_anios} años ({edad_meses} meses aprox.), "
                f"etapa de desarrollo: {etapa_desarrollo}, "
                f"alimentación: {b.get('feeding', 'N/A')}, "
                f"peso: {b.get('weight', 'N/A')} kg, "
                f"altura: {b.get('height', 'N/A')} cm"
            )

    context = ""
    if profile_texts:
        context += "Perfiles:\n" + "\n".join(profile_texts) + "\n\n"
    if baby_texts:
        context += "Bebés:\n" + "\n".join(baby_texts) + "\n\n"
    
    # Agregar conocimiento específico si existe
    if knowledge_context:
        context += knowledge_context + "\n\n"

    return context.strip(), routines_context.strip()

async def get_conversation_history(user_id, supabase_client, limit_per_role=4, baby_id=None, filter_by_baby=False, user_only=False):
    """
        Recupera los últimos mensajes del usuario y del asistente para mantener contexto en la conversación.
        Filtrando por el baby_id
        
        Args:
            user_only: Si es True, solo incluye mensajes del usuario para evitar copiar formatos de respuestas anteriores
    """
    user_query = supabase_client.table("conversations") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("role", "user")

    if not user_only:
        assistant_query = supabase_client.table("conversations") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("role", "assistant")

    if filter_by_baby:
        if baby_id is None:
            user_query = user_query.filter("baby_id", "is", "null")
            if not user_only:
                assistant_query = assistant_query.filter("baby_id", "is", "null")
        else:
            user_query = user_query.eq("baby_id", baby_id)
            if not user_only:
                assistant_query = assistant_query.eq("baby_id", baby_id)

    user_msgs = user_query \
        .order("created_at", desc=True) \
        .limit(limit_per_role if not user_only else limit_per_role * 2) \
        .execute()

    if user_only:
        # Solo mensajes del usuario para evitar copiar formatos
        history_sorted = sorted(user_msgs.data or [], key=lambda x: x["created_at"])
        print(f"📝 [DEBUG] Solo mensajes de usuario en historial: {len(history_sorted)}")
    else:
        assistant_msgs = assistant_query \
            .order("created_at", desc=True) \
            .limit(limit_per_role) \
            .execute()

        # Combinar y ordenar cronológicamente
        history = (user_msgs.data or []) + (assistant_msgs.data or [])
        history_sorted = sorted(history, key=lambda x: x["created_at"])
        print(f"📝 [DEBUG] Historial completo: {len(history_sorted)} mensajes")

    # Convertir al formato que espera OpenAI
    formatted_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history_sorted
    ]

    return formatted_history

@router.post("/api/chat")
async def chat_openai(payload: ChatRequest, user=Depends(get_current_user)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message required")

    user_id = user["id"]
    
    babies_response = supabase.table("babies").select("*").eq("user_id", user_id).execute()
    babies_context = babies_response.data or []
    print(f"👶 Bebés en contexto disponible: {len(babies_context)}")
    
    # Verificar si es una respuesta de confirmación de preferencias (KNOWLEDGE)
    confirmation_response = confirmation_cache.is_confirmation_response(payload.message)
    if confirmation_response is not None and confirmation_cache.has_pending_confirmation(user_id):
        print(f"🎯 Detectada respuesta de confirmación de conocimiento: {confirmation_response}")
        
        pending_data = confirmation_cache.get_pending_confirmation(user_id)
        if pending_data:
            if confirmation_response:  # Usuario confirmó
                try:
                    saved_items = []
                    
                    for knowledge_item in pending_data["knowledge"]:
                        # Buscar el baby_id basado en el nombre
                        baby_id = await BabyKnowledgeService.find_baby_by_name(
                            user_id, 
                            knowledge_item.get("baby_name", "")
                        )
                        
                        if baby_id:
                            # Preparar datos para guardar
                            knowledge_data = {
                                "category": knowledge_item["category"],
                                "subcategory": knowledge_item.get("subcategory"),
                                "title": knowledge_item["title"],
                                "description": knowledge_item["description"],
                                "importance_level": knowledge_item.get("importance_level", 1)
                            }
                            
                            # Guardar en la base de datos
                            saved_item = await BabyKnowledgeService.save_knowledge(
                                user_id, 
                                baby_id, 
                                knowledge_data
                            )
                            saved_items.append(saved_item)
                    
                    confirmation_cache.clear_pending_confirmation(user_id)
                    
                    response_text = f"✅ ¡Perfecto! He guardado {len(saved_items)} elemento(s) en el perfil. Ahora podré darte respuestas más personalizadas considerando esta información."
                    
                    return {"answer": response_text, "usage": {}}
                    
                except Exception as e:
                    print(f"Error guardando conocimiento confirmado: {e}")
                    confirmation_cache.clear_pending_confirmation(user_id)
                    return {"answer": "❌ Hubo un error guardando la información. Por favor intenta de nuevo.", "usage": {}}
                    
            else:  # Usuario rechazó
                confirmation_cache.clear_pending_confirmation(user_id)
                return {"answer": "👌 Entendido, no guardaré esa información.", "usage": {}}

    # Verificar si es una respuesta de confirmación de RUTINA
    routine_confirmation_response = routine_confirmation_cache.is_confirmation_response(payload.message)
    if routine_confirmation_response is not None and routine_confirmation_cache.has_pending_confirmation(user_id):
        print(f"🎯 Detectada respuesta de confirmación de rutina: {routine_confirmation_response}")
        
        pending_routine_data = routine_confirmation_cache.get_pending_confirmation(user_id)
        if pending_routine_data:
            if routine_confirmation_response:  # Usuario confirmó la rutina
                try:
                    routine_data = pending_routine_data["routine"]
                    
                    # Buscar el baby_id basado en el nombre
                    baby_id = await RoutineService.find_baby_by_name(
                        user_id, 
                        routine_data.get("baby_name", "")
                    )
                    
                    if baby_id:
                        # 1. GUARDAR LA RUTINA en tablas específicas
                        saved_routine = await RoutineService.save_routine(
                            user_id, 
                            baby_id, 
                            routine_data
                        )
                        
                        # 2. TAMBIÉN GUARDAR COMO CONOCIMIENTO GENERAL
                        try:
                            routine_name = routine_data.get("routine_name", "Rutina")
                            routine_summary = routine_data.get("context_summary", "Rutina establecida")
                            
                            # Crear entrada de conocimiento basada en la rutina
                            knowledge_data = {
                                "category": "rutinas",
                                "subcategory": "estructura diaria",
                                "title": routine_name,
                                "description": routine_summary,
                                "importance_level": 3
                            }
                            
                            # Guardar también en baby_knowledge
                            await BabyKnowledgeService.save_knowledge(
                                user_id, 
                                baby_id, 
                                knowledge_data
                            )
                            
                            print(f"✅ Rutina guardada en AMBOS sistemas: rutinas + conocimiento")
                            
                        except Exception as knowledge_error:
                            print(f"⚠️ Error guardando conocimiento de rutina: {knowledge_error}")
                            # No fallar si el conocimiento falla, la rutina ya se guardó
                        
                        routine_confirmation_cache.clear_pending_confirmation(user_id)
                        
                        activities_count = saved_routine.get("activities_count", 0)
                        
                        response_text = f"✅ ¡Excelente! He guardado la rutina **{routine_name}** con {activities_count} actividades en el sistema de rutinas y también como conocimiento general. Ahora podré ayudarte mejor con horarios y sugerencias personalizadas."
                        
                        return {"answer": response_text, "usage": {}}
                    else:
                        routine_confirmation_cache.clear_pending_confirmation(user_id)
                        return {"answer": "❌ No pude encontrar el bebé mencionado. Por favor intenta de nuevo.", "usage": {}}
                        
                except Exception as e:
                    print(f"Error guardando rutina confirmada: {e}")
                    routine_confirmation_cache.clear_pending_confirmation(user_id)
                    return {"answer": "❌ Hubo un error guardando la rutina. Por favor intenta de nuevo.", "usage": {}}
                    
            else:  # Usuario rechazó la rutina
                routine_confirmation_cache.clear_pending_confirmation(user_id)
                return {"answer": "👌 Entendido, no guardaré esa rutina.", "usage": {}}

    message_text = payload.message.strip()
    simple_greeting = is_simple_greeting(message_text)
    message_lower = payload.message.lower()

    diaper_tokens = [
        "pañal", "panal", "cambio de pañal", "cambiarle el pañal",
        "cambiar pañal", "cambiar el pañal", "diaper", "fralda"
    ]
    is_diaper_context = any(token in message_lower for token in diaper_tokens)

    # Contexto RAG, perfiles/bebés e historial de conversación
    rag_context = ""
    specialized_rag = ""
    needs_night_weaning = needs_partner = needs_behavior = needs_routine = False

    if not simple_greeting:
        print(f"📝 Mensaje del usuario: '{payload.message[:100]}...'")
        
        # Verificar si es una consulta de referencias ANTES de hacer búsqueda RAG
        is_reference_query = ReferenceDetector.detect_reference_query(payload.message)
        print(f"🔍 [DEBUG] ¿Es consulta de referencias? {is_reference_query}")
        
        if is_reference_query:
            print(f"🔍 [REFERENCIAS] Detectada consulta de referencias - NO se guardará en cache")
            # Para consultas de referencias, usar búsqueda simple sin guardar en cache
            rag_context = get_rag_context_simple(payload.message, search_id="reference_query")
            consulted_sources = []  # No guardar fuentes para consultas de referencias
        else:
            print(f"✅ [CACHE] Consulta normal - SÍ se guardará en cache")
            # Para consultas normales, usar búsqueda completa y guardar en cache
            rag_context, consulted_sources = get_rag_context(payload.message, search_id="user_query")
            
            # Guardar las fuentes consultadas en el cache para futuras consultas de referencias
            source_cache.store_sources(user_id, consulted_sources, payload.message, "user_query")
    else:
        is_reference_query = False
        print(f"👋 [DEBUG] Es saludo simple - no se procesa RAG ni cache")
        
        needs_night_weaning = any(keyword in message_lower for keyword in NIGHT_WEANING_KEYWORDS)
        needs_partner = any(keyword in message_lower for keyword in PARTNER_KEYWORDS)
        needs_behavior = any(keyword in message_lower for keyword in BEHAVIOR_KEYWORDS)
        needs_routine = any(keyword in message_lower for keyword in ROUTINE_KEYWORDS)

        # Debug detallado de keywords
        if needs_behavior:
            detected_behavior_keywords = [kw for kw in BEHAVIOR_KEYWORDS if kw in message_lower]
            print(f"🎭 BEHAVIOR keywords detectadas: {detected_behavior_keywords}")
        
        if needs_routine:
            detected_routine_keywords = [kw for kw in ROUTINE_KEYWORDS if kw in message_lower]
            print(f"📅 ROUTINE keywords detectadas: {detected_routine_keywords}")

        print(f"🔍 Keywords detectadas: night_weaning={needs_night_weaning}, partner={needs_partner}, behavior={needs_behavior}, routine={needs_routine}")

        if is_diaper_context:
            needs_partner = False
            needs_routine = False
            print("🚼 Contexto de pañales detectado - deshabilitando partner/routine")

        # TEMPORALMENTE DESHABILITADO PARA DEBUG
        if False and needs_night_weaning:
            specialized_rag = get_rag_context_simple("desmame nocturno etapas Lorena Furtado destete respetuoso", search_id="night_weaning")
            print("🌙 Búsqueda RAG especializada para desmame nocturno")
        elif False and needs_partner:
            specialized_rag = get_rag_context_simple("pareja acompañamiento neurociencia asociación materna trabajo nocturno firmeza tranquila", search_id="partner_support")
            print("👫 Búsqueda RAG especializada para trabajo con pareja")
        elif False and needs_behavior:
            specialized_rag = get_rag_context_simple("vocalizaciones autorregulación desarrollo emocional llanto descarga neurociencia infantil", search_id="behavior_analysis")
            print("🎵 Búsqueda RAG especializada para vocalizaciones y comportamientos")
        else:
            print("ℹ️ Búsquedas especializadas temporalmente deshabilitadas para debug")

    # Construir lista de secciones adicionales del prompt
    prompt_sections = []
    if not simple_greeting:
        if needs_behavior:
            prompt_sections.append("behavior.md")
        if needs_routine:
            prompt_sections.extend(["routines.md"])
        if needs_night_weaning:
            prompt_sections.append("night_weaning.md")
        if needs_partner:
            prompt_sections.append("partner_support.md")

    # Combinar contextos RAG
    combined_rag_context = f"{rag_context}\n\n--- CONTEXTO ESPECIALIZADO ---\n{specialized_rag}" if specialized_rag else rag_context
    selected_baby_id = payload.baby_id if "baby_id" in payload.__fields_set__ else None
    user_context, routines_context = await get_user_profiles_and_babies(
        user["id"],
        supabase,
        baby_id=selected_baby_id,
        babies_data=babies_context
    )
    filter_by_baby = selected_baby_id is not None
    history = await get_conversation_history(
        user["id"],
        supabase,
        limit_per_role=3,  # Reducido de 4 a 3 para menos influencia de patrones
        baby_id=selected_baby_id,
        filter_by_baby=filter_by_baby,
        user_only=True  # Solo mensajes del usuario para evitar copiar formatos
    )  # 👈 historial del backend

    print(f"📚 Historial de conversación ({len(history)} mensajes):")
    for i, msg in enumerate(history):
        content_preview = msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', '')
        print(f"  {i+1}. [{msg.get('role', 'unknown')}]: {content_preview}")

    #print(f"📚 Contexto RAG recuperado:\n{rag_context[:500]}...\n")
    
    # Formatear el perfil que viene en el payload
    profile_text = ""
    if payload.profile:
        profile_data = payload.profile
        profile_text = (
            "**Perfil actual en esta consulta:**\n"
            f"- Fecha de nacimiento: {profile_data.get('dob')}\n"
            f"- Alimentación: {profile_data.get('feeding')}\n"
        )

    # Cargar y formatear el prompt maestro
    system_prompt_template = load_system_prompt(prompt_sections)
    
    # Detectar tipo de consulta y agregar template específico
    specific_template = detect_consultation_type_and_load_template(payload.message)
    if specific_template:
        system_prompt_template += specific_template
        print(f"🎯 Template específico detectado y agregado")

    instruction_dataset = load_instruction_dataset()

    # Siempre agregar dataset general de instrucciones Lumi (v1)
    if instruction_dataset:
        system_prompt_template += "\n\n" + instruction_dataset
        print("📚 Dataset lumi_instruction_dataset_v1.md cargado correctamente")
    
    # Cantida de caracteres que se le pasara del rag al promp, de conocimiento
    max_rag_length = 5000
    if len(combined_rag_context) > max_rag_length:
        combined_rag_context = combined_rag_context[:max_rag_length] + "...\n[Contexto truncado por longitud]"
        # print(f"⚠️ Contexto RAG truncado por longitud")
    
    formatted_system_prompt = system_prompt_template.format(
        today=today,
        user_context=user_context if user_context else "No hay información específica del usuario disponible.",
        profile_context=profile_text if profile_text else "No se proporcionó perfil específico en esta consulta.",
        routines_context=routines_context if routines_context else "No hay rutinas específicas registradas.",
        rag_context=combined_rag_context if combined_rag_context else "No hay contexto especializado disponible para esta consulta."
    )
    
    # Agregar instrucción específica sobre originalidad de formato
    formatted_system_prompt += "\n\n" + """
## INSTRUCCIÓN CRÍTICA SOBRE FORMATO:
- NO copies la estructura, formato o estilo de mensajes anteriores en el historial
- Cada respuesta debe ser ORIGINAL y específica para la consulta actual
- Varía tu estructura: usa párrafos fluidos, listas simples, o formato según el contenido
- Evita patrones repetitivos como siempre usar "## 1. Título" o listas numeradas idénticas
- Responde de forma natural y conversacional, no como una plantilla rígida
"""
    
    # Log de longitud del prompt para debug
    prompt_length = len(formatted_system_prompt)
    print(f"📏 Longitud del prompt del sistema: {prompt_length} caracteres")

    # Si es una consulta de referencias, manejarla directamente sin pasar por LLM
    if not simple_greeting and is_reference_query:
        print(f"🔍 [REFERENCIAS] Procesando consulta de referencias")
        reference_response = await ReferenceDetector.handle_reference_query(payload.message, user_id)
        return {"answer": reference_response, "usage": {}}

    # Construcción del body con prompt unificado
    messages = [{"role": "system", "content": formatted_system_prompt}]
    
    # Agregar historial con contexto claro
    if history:
        messages.append({
            "role": "system", 
            "content": "=== CONTEXTO DE MENSAJES ANTERIORES DEL USUARIO (solo para entender el contexto, NO para copiar formato de respuestas) ==="
        })
        messages.extend(history)
        messages.append({
            "role": "system", 
            "content": "=== FIN DEL CONTEXTO - Responde de forma original y específica ==="
        })
    
    # Agregar mensaje actual
    messages.append({"role": "user", "content": payload.message})

    body = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "max_tokens": 1800,
        "temperature": 0.4,
        "top_p": 0.9,
    }

    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}

    # Retry logic con exponential backoff para manejar timeouts
    max_retries = 3
    base_timeout = 45.0
    
    for attempt in range(max_retries):
        try:
            current_timeout = base_timeout + (attempt * 15)  # 45s, 60s, 75s
            print(f"🔄 Intento {attempt + 1}/{max_retries} - Timeout: {current_timeout}s")
            
            async with httpx.AsyncClient(timeout=current_timeout) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers)
            
            if resp.status_code >= 300:
                error_detail = resp.text
                print(f"❌ Error OpenAI (intento {attempt + 1}): {error_detail}")
                if attempt == max_retries - 1:  # Último intento
                    raise HTTPException(status_code=502, detail={"openai_error": error_detail})
                continue
            
            # Si llegamos aquí, la llamada fue exitosa
            break
            
        except httpx.ReadTimeout as e:
            print(f"⏰ Timeout en intento {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:  # Último intento
                return {
                    "answer": "Lo siento, el sistema está experimentando demoras. Por favor, intenta reformular tu pregunta de manera más breve o inténtalo de nuevo en unos momentos.",
                    "usage": {}
                }
            # Esperar antes del siguiente intento
            import asyncio
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
            continue
        except Exception as e:
            print(f"❌ Error inesperado en intento {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {
                    "answer": "Hubo un problema técnico. Por favor, intenta de nuevo en unos momentos.",
                    "usage": {}
                }
            continue

    data = resp.json()
    assistant = data.get("choices", [])[0].get("message", {}).get("content", "")
    
    # Formatear la respuesta para mayor naturalidad
    assistant = format_llm_output(assistant)
    
    usage = data.get("usage", {})

    # Variables para controlar el flujo de detección dual
    routine_detected_and_saved = False
    assistant_with_routine_confirmation = ""

    # PRIMERA PRIORIDAD: Detectar rutinas en el mensaje del usuario
    try:
        #print(f"� Analizando mensaje para rutinas: {payload.message}")
        
        # Usar el mismo contexto de bebés
        babies = supabase.table("babies").select("*").eq("user_id", user_id).execute()
        babies_context = babies.data or []
        
        # Si hay baby_id seleccionado, usarlo como contexto prioritario
        if hasattr(payload, 'baby_id') and payload.baby_id and selected_baby_id:
            # Filtrar solo el bebé seleccionado para el detector de rutinas
            selected_baby = [b for b in babies_context if b.get("id") == selected_baby_id]
            if selected_baby:
                print(f"🎯 [RUTINA-DETECCION] Usando bebé seleccionado: {selected_baby[0].get('name', 'Unknown')}")
                routine_babies_context = selected_baby
            else:
                print(f"⚠️ [RUTINA-DETECCION] Baby ID {selected_baby_id} no encontrado, usando contexto completo")
                routine_babies_context = babies_context
        else:
            print(f"ℹ️ [RUTINA-DETECCION] No hay baby_id seleccionado, usando contexto completo")
            routine_babies_context = babies_context
        
        # Analizar el mensaje para detectar información de rutinas
        print("🔄 [RUTINA-DETECCION-1] Iniciando análisis de rutinas...")
        detected_routine = await RoutineDetector.analyze_message(
            payload.message, 
            routine_babies_context
        )
        print(f"🕐 [RUTINA-DETECCION-1] Rutina detectada: {detected_routine}")
        
        # Si se detecta una rutina, guardar en caché y preguntar confirmación
        if detected_routine and RoutineDetector.should_ask_confirmation(detected_routine):
            print("✅ [RUTINA-DETECCION-1] Se debe preguntar confirmación de rutina")
            
            # Guardar en caché para confirmación posterior
            routine_confirmation_cache.set_pending_confirmation(user_id, detected_routine, payload.message)
            
            confirmation_message = RoutineDetector.format_confirmation_message(detected_routine)
            
            # Agregar la pregunta de confirmación a la respuesta
            assistant_with_routine_confirmation = f"{assistant}\n\n� {confirmation_message}"
            
            return {
                "answer": assistant_with_routine_confirmation, 
                "usage": usage
            }
        else:
            print("❌ [RUTINA-DETECCION-1] No se debe preguntar confirmación de rutina")
        
    except Exception as e:
        print(f"Error en detección de rutinas: {e}")
        import traceback
        traceback.print_exc()
        # Continuar normalmente si falla la detección
        pass

    # NUEVA FUNCIONALIDAD: Detección SIMPLE de rutinas en la RESPUESTA de Lumi
    try:
        print(f"🔍 Analizando respuesta de Lumi para rutinas (método simple)...")
        
        # 1. Detectar horarios estructurados
        import re
        time_patterns = re.findall(r'\*\*\d{1,2}:\d{2}[–-]\d{1,2}:\d{2}\*\*', assistant)
        
        # 2. Detectar palabras clave de rutina
        routine_indicators = [
            "rutina diaria", "rutina para", "🧭", "🌅", "mañana", "mediodía", "tarde", "noche",
            "despertar", "desayuno", "almuerzo", "siesta", "cena", "baño",
            "resumen visual", "bloques", "actividad principal"
        ]
        found_indicators = sum(1 for indicator in routine_indicators if indicator in assistant.lower())
        
        # 3. Criterios simples para detectar rutina
        has_structured_times = len(time_patterns) >= 3
        has_routine_content = found_indicators >= 5
        
        print(f"⏰ Horarios encontrados: {len(time_patterns)}")
        print(f"📋 Indicadores de rutina: {found_indicators}")
        print(f"🎯 Es rutina estructurada: {has_structured_times and has_routine_content}")
        
        if has_structured_times and has_routine_content:
            print("✅ Rutina detectada con método simple - Agregando confirmación")
            
            # Obtener información de bebés
            babies = supabase.table("babies").select("*").eq("user_id", user_id).execute()
            babies_context = babies.data or []
            baby_name = babies_context[0]['name'] if babies_context else "tu bebé"
            
            # Crear rutina simple estructurada
            simple_routine = {
                "routine_name": f"Rutina diaria para {baby_name}",
                "baby_name": baby_name,
                "confidence": 0.9,  # Alta confianza para método simple
                "routine_type": "daily",
                "context_summary": "Rutina diaria detectada automáticamente",
                "activities": [
                    {
                        "time_start": pattern.replace('*', '').split('–')[0],
                        "time_end": pattern.replace('*', '').split('–')[1] if '–' in pattern else None,
                        "activity": f"Actividad {i+1}",
                        "details": "Actividad detectada automáticamente",
                        "activity_type": "care"
                    }
                    for i, pattern in enumerate(time_patterns[:10])  # Máximo 10 actividades
                ]
            }
            
            # Guardar en caché y pedir confirmación
            routine_confirmation_cache.set_pending_confirmation(user_id, simple_routine, assistant)
            
            confirmation_message = f"¿Te parece si guardo esta rutina para {baby_name} en su perfil para futuras conversaciones?"
            assistant_with_routine_confirmation = f"{assistant}\n\n📋 {confirmation_message}"
            
            return {
                "answer": assistant_with_routine_confirmation, 
                "usage": usage
            }
        else:
            print("❌ No es una rutina estructurada según criterios simples")
            
    except Exception as e:
        print(f"Error en detección simple de rutinas: {e}")
        # Continuar normalmente si falla
        pass

    # SEGUNDA PRIORIDAD: Detectar conocimiento importante en el mensaje del usuario
    # TEMPORALMENTE DESHABILITADO PARA DEBUG
    if False:
        try:
            print(f"🔄 [CONOCIMIENTO-DETECCION-1] Analizando mensaje para conocimiento: {payload.message}")
            
            # Analizar el mensaje para detectar información importante
            detected_knowledge = await KnowledgeDetector.analyze_message(
                payload.message, 
                babies_context
            )
            print(f"🧠 [CONOCIMIENTO-DETECCION-1] Conocimiento detectado: {detected_knowledge}")

            # Enriquecer nombres genéricos con nombres reales del contexto
            KnowledgeDetector.enrich_baby_names(
                detected_knowledge,
                babies_context=babies_context,
                original_message=payload.message
            )

            # Guardar automáticamente conocimiento general sin confirmación
            general_items = [item for item in detected_knowledge if item.get("category") == "general"]
            for general_item in general_items:
                baby_name = general_item.get("baby_name")
                auto_baby_id = None

                if baby_name:
                    auto_baby_id = await BabyKnowledgeService.find_baby_by_name(user_id, baby_name)

                if not auto_baby_id and selected_baby_id:
                    auto_baby_id = selected_baby_id

                if not auto_baby_id and babies_context:
                    auto_baby_id = babies_context[0]["id"]

                if not auto_baby_id:
                    print(f"⚠️ No se pudo determinar bebé para conocimiento general: {general_item}")
                    continue

                knowledge_payload = {
                    "category": general_item["category"],
                    "subcategory": general_item.get("subcategory"),
                    "title": general_item.get("title", general_item.get("description", "Contexto general")),
                    "description": general_item.get("description", general_item.get("title", "")),
                    "importance_level": general_item.get("importance_level", 2)
                }

                saved_general = await BabyKnowledgeService.save_or_update_general_knowledge(
                    user_id,
                    auto_baby_id,
                    knowledge_payload
                )

                if saved_general:
                    print(f"🏠 Conocimiento general guardado automáticamente: {knowledge_payload['title']} (baby_id={auto_baby_id})")
                else:
                    print(f"⚠️ No se pudo guardar conocimiento general: {knowledge_payload}")

            # Filtrar conocimientos generales para no pedir confirmación
            detected_knowledge = [item for item in detected_knowledge if item.get("category") != "general"]
            
            # Si se detecta conocimiento importante, guardar en caché y preguntar
            if detected_knowledge and KnowledgeDetector.should_ask_confirmation(detected_knowledge):
                print("✅ [CONOCIMIENTO-DETECCION-1] Se debe preguntar confirmación")
                
                # Guardar en caché para confirmación posterior
                confirmation_cache.set_pending_confirmation(user_id, detected_knowledge, payload.message)
                
                confirmation_message = KnowledgeDetector.format_confirmation_message(detected_knowledge)
                
                # Agregar la pregunta de confirmación a la respuesta
                assistant_with_confirmation = f"{assistant}\n\n� {confirmation_message}"
                
                return {
                    "answer": assistant_with_confirmation, 
                    "usage": usage
                }
            else:
                print("❌ [CONOCIMIENTO-DETECCION-1] No se debe preguntar confirmación de conocimiento")
            
        except Exception as e:
            print(f"Error en detección de conocimiento: {e}")
            import traceback
            traceback.print_exc()
            # Continuar normalmente si falla la detección
            pass
    else:
        print("ℹ️ [DEBUG] Detección de conocimiento temporalmente deshabilitada")

    return {"answer": assistant, "usage": usage}
