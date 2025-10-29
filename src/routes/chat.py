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
from ..services.chat_service import (
    handle_knowledge_confirmation,
    handle_routine_confirmation,
    detect_routine_in_user_message,
    detect_routine_in_response,
    detect_knowledge_in_message,
    build_system_prompt,
    ROUTINE_KEYWORDS,
    NIGHT_WEANING_KEYWORDS,
    PARTNER_KEYWORDS,
    BEHAVIOR_KEYWORDS
)

router = APIRouter()
today = datetime.now().strftime("%d/%m/%Y %H:%M")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

if not OPENAI_KEY:
    raise RuntimeError("Falta OPENAI_API_KEY en variables de entorno (.env)")

print(f"🤖 Usando modelo OpenAI: {OPENAI_MODEL}")

# Paths necesarios para funciones que permanecen en este archivo
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SECTIONS_DIR = PROMPTS_DIR / "sections"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
EXAMPLES_DIR = PROMPTS_DIR / "examples"

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
    travels_keywords = ["viajar", "viajes", "viaje", "destino", "destinos", "vacaciones", "mochila", "maleta"]
    if any(keyword in message_lower for keyword in travels_keywords):
        template_path = TEMPLATES_DIR / "travel_with_children.md"
        if template_path.exists():
            print(f"🚀 Cargando template de viajes con niños desde: {template_path}")
            with open(template_path, "r", encoding="utf-8") as f:
                return f"\n\n## TEMPLATE ESPECÍFICO PARA VIAJES CON NIÑOS:\n\n{f.read()}"
        else: 
            print(f"⚠️ Template de viajes con niños no encontrado: {template_path}")
    
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
                # f"alimentación: {b.get('feeding', 'N/A')}, "
                f"peso: {b.get('weight', 'N/A')} kg, "
                f"altura: {b.get('height', 'N/A')} cm"
            )

    context = ""
    if profile_texts:
        context += "Cuidador:\n" + "\n".join(profile_texts) + "\n\n"
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
    knowledge_confirmation_result = await handle_knowledge_confirmation(user_id, payload.message)
    if knowledge_confirmation_result:
        return knowledge_confirmation_result

    # Verificar si es una respuesta de confirmación de RUTINA
    routine_confirmation_result = await handle_routine_confirmation(user_id, payload.message)
    if routine_confirmation_result:
        return routine_confirmation_result

    message_text = payload.message.strip()
    simple_greeting = is_simple_greeting(message_text)
    message_lower = payload.message.lower()

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
        baby_id=selected_baby_id,
        filter_by_baby=filter_by_baby
    )  # 👈 historial del backend

    #print(f"📚 Contexto RAG recuperado:\n{rag_context[:500]}...\n")
    
    # Construir el prompt del sistema usando la función extraída
    formatted_system_prompt = await build_system_prompt(payload, user_context, routines_context, combined_rag_context)

    # Detectar tipo de consulta y agregar template específico
    specific_template = detect_consultation_type_and_load_template(payload.message)
    if specific_template:
        formatted_system_prompt += specific_template
        print(f"🎯 Template específico detectado y agregado")

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
    # Prompt completo para debug y analisis
    print("🧩 Prompt completo enviado a OpenAI:", messages)

    body = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "max_tokens": 2000,
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
        # Usar el mismo contexto de bebés
        babies = supabase.table("babies").select("*").eq("user_id", user_id).execute()
        babies_context = babies.data or []
        
        routine_confirmation_message = await detect_routine_in_user_message(
            user_id, 
            payload.message, 
            babies_context
        )
        
        if routine_confirmation_message:
            # Agregar la pregunta de confirmación a la respuesta
            assistant_with_routine_confirmation = f"{assistant}\n\n🕐 {routine_confirmation_message}"
            
            return {
                "answer": assistant_with_routine_confirmation, 
                "usage": usage
            }
        
    except Exception as e:
        print(f"Error en detección de rutinas: {e}")
        import traceback
        traceback.print_exc()
        # Continuar normalmente si falla la detección
        pass

    # NUEVA FUNCIONALIDAD: Detección SIMPLE de rutinas en la RESPUESTA de Lumi
    try:
        # Usar el mismo contexto de bebés
        babies = supabase.table("babies").select("*").eq("user_id", user_id).execute()
        babies_context = babies.data or []
        
        routine_confirmation_message = await detect_routine_in_response(
            user_id, 
            assistant, 
            babies_context
        )
        
        if routine_confirmation_message:
            assistant_with_routine_confirmation = f"{assistant}\n\n📋 {routine_confirmation_message}"
            
            return {
                "answer": assistant_with_routine_confirmation, 
                "usage": usage
            }
            
    except Exception as e:
        print(f"Error en detección simple de rutinas: {e}")
        # Continuar normalmente si falla
        pass

    # SEGUNDA PRIORIDAD: Detectar conocimiento importante en el mensaje del usuario
    try:
        selected_baby_id = payload.baby_id if "baby_id" in payload.__fields_set__ else None
        
        knowledge_confirmation_message = await detect_knowledge_in_message(
            user_id, 
            payload.message, 
            babies_context, 
            selected_baby_id
        )
        
        if knowledge_confirmation_message:
            # Agregar la pregunta de confirmación a la respuesta
            assistant_with_confirmation = f"{assistant}\n\n🧠 {knowledge_confirmation_message}"
            
            return {
                "answer": assistant_with_confirmation, 
                "usage": usage
            }
        
    except Exception as e:
        print(f"Error en detección de conocimiento: {e}")
        import traceback
        traceback.print_exc()
        # Continuar normalmente si falla la detección
        pass

    return {"answer": assistant, "usage": usage}
