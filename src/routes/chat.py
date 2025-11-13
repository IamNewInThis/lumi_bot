# src/routes/chat.py
import os
import httpx
import unicodedata
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pathlib import Path
from typing import List
from ..models.chat import ChatRequest, ProfileKeywordsConfirmRequest
from ..auth import get_current_user
from src.rag.utils import get_rag_context, get_rag_context_simple
from src.utils.date_utils import calcular_edad, calcular_meses
from src.utils.lang import detect_lang
from src.state.session_store import get_lang, set_lang
from src.extractors.profile_extractor import BabyProfile, extract_profile_info
from src.extractors.template_extractor import build_template_block
from ..rag.retriever import supabase
from ..utils.knowledge_detector import KnowledgeDetector
from ..services.knowledge_service import BabyKnowledgeService
from ..utils.knowledge_cache import confirmation_cache
from ..utils.routine_detector import RoutineDetector
from ..services.routine_service import RoutineService
from ..utils.routine_cache import routine_confirmation_cache
from ..utils.reference_detector import ReferenceDetector
from ..utils.source_cache import source_cache
from ..services.profile_service import BabyProfileService
from ..services.chat_service import (
    handle_knowledge_confirmation,
    handle_routine_confirmation,
    detect_routine_in_response,
    detect_knowledge_in_message,
    build_system_prompt,
    build_chat_prompt,
    ROUTINE_KEYWORDS,
    NIGHT_WEANING_KEYWORDS,
    PARTNER_KEYWORDS,
    BEHAVIOR_KEYWORDS
)
from src.utils.profile_triggers import should_trigger_profile_extraction, should_trigger_profile_extraction_llm

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

def detect_consultation_type_and_load_template(message: str) -> str:
    """
    Wrapper legado para mantener compatibilidad con código existente.
    """
    block, selection = build_template_block(message)

    if selection.template_key:
        print(
            f"🚀 Template detectado: {selection.template_key} "
            f"(source={selection.source}, confidence={selection.confidence:.2f})"
        )
        if selection.trigger_keyword:
            print(
                f"   Keyword: '{selection.trigger_keyword}' "
                f"({selection.trigger_language})"
            )
        elif selection.reason:
            print(f"   Motivo LLM: {selection.reason}")

    return block


async def detect_routine_in_user_message(user_id: str, message: str, babies_context: list) -> str | None:
    """
    Detecta rutinas directamente en el mensaje del usuario usando RoutineDetector.
    Retorna el texto de confirmación si se detecta y almacena la rutina en caché,
    o None si no corresponde preguntar.
    """
    try:
        print("🔎 Analizando mensaje del usuario para rutinas (LLM) …")
        detected_routine = await RoutineDetector.analyze_message(message, babies_context)

        if not detected_routine:
            print("ℹ️ No se detectó rutina en el mensaje del usuario.")
            return None

        if not RoutineDetector.should_ask_confirmation(detected_routine):
            print("ℹ️ Rutina detectada pero sin confianza suficiente para confirmar.")
            return None

        confirmation_message = RoutineDetector.format_confirmation_message(detected_routine)
        if not confirmation_message:
            print("ℹ️ Rutina detectada pero sin mensaje de confirmación válido.")
            return None

        routine_confirmation_cache.set_pending_confirmation(user_id, detected_routine, message)
        print("✅ Rutina almacenada en caché a la espera de confirmación del usuario.")
        return confirmation_message

    except Exception as exc:
        print(f"❌ Error ejecutando RoutineDetector en mensaje del usuario: {exc}")
        import traceback
        traceback.print_exc()
        return None

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

    # TODO: Agregar relacion con perfiles si es necesario
    profile_texts = [
        f"- {p['name']}, fecha de nacimiento {p['birthdate']}"
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

@router.post("/api/chat/confirm-profile-keywords")
async def confirm_profile_keywords(
    payload: ProfileKeywordsConfirmRequest,
    user=Depends(get_current_user)
):
    """
    Endpoint para confirmar y guardar keywords del perfil después de que el usuario 
    presione el botón de confirmación en el frontend.
    
    Args:
        payload: Objeto con baby_id y keywords a guardar
        user: Usuario autenticado
    
    Returns:
        Resultado del guardado con mensaje de confirmación
    """
    user_id = user["id"]
    
    try:
        # Verificar que el bebé pertenece al usuario
        baby_check = supabase.table("babies")\
            .select("id, name")\
            .eq("id", payload.baby_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not baby_check.data:
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar este bebé")
        
        baby_name = baby_check.data.get('name', 'tu bebé')
        
        keywords = payload.keywords or []
        is_profile_extractor_payload = any(
            kw.get("source") == "profile_extractor" for kw in keywords
        )

        if is_profile_extractor_payload:
            profile_payload = {}
            for kw in keywords:
                field_name = kw.get("profile_field") or kw.get("field_key")
                value = kw.get("profile_value") or kw.get("keyword")
                if field_name == "confidence":
                    continue
                if field_name and value:
                    profile_payload[field_name] = value

            if not profile_payload:
                raise HTTPException(status_code=400, detail="No se encontraron campos del perfil para guardar.")

            try:
                profile = BabyProfile(**profile_payload)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Datos inválidos del perfil: {e}")

            saved_count = await BabyProfileService.process_profile_extraction(
                baby_id=payload.baby_id,
                profile=profile
            )
        elif hasattr(BabyProfileService, "save_detected_keywords"):
            saved_count = await BabyProfileService.save_detected_keywords(
                baby_id=payload.baby_id,
                detected_keywords=payload.keywords,
                lang='es'  # Por ahora fijo, podría venir del request
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Guardar keywords no está disponible actualmente."
            )
        
        if saved_count > 0:
            print(f"✅ [PROFILE CONFIRM] Guardados {saved_count} keywords para {baby_name} (ID: {payload.baby_id})")
            
            return {
                "success": True,
                "saved_count": saved_count,
                "baby_name": baby_name,
                "message": f"✅ Guardé {saved_count} {'característica' if saved_count == 1 else 'características'} del perfil de {baby_name}"
            }
        else:
            return {
                "success": False,
                "saved_count": 0,
                "message": "No se pudo guardar la información. Por favor, intenta de nuevo."
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [PROFILE CONFIRM] Error guardando keywords: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error al guardar las características: {str(e)}"
        )


@router.post("/api/chat")
async def chat_openai(payload: ChatRequest, user=Depends(get_current_user)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message required")

    user_id = user["id"]
    
    # 1️⃣ Detectar idioma desde el primer mensaje
    conversation_id = payload.baby_id or str(user_id)
    lang = get_lang(conversation_id)
    lang_marker_info = None

    if not lang:
        lang, lang_marker_info = detect_lang(payload.message, return_matches=True)
        set_lang(conversation_id, lang)
    else:
        print(f"🌐 [LANG] Reutilizando idioma en cache para conversación: {lang}")

    print(f"🌐 Idioma detectado para la conversación: {lang}")
    
    # Obtener información de los bebés del usuario
    babies_response = supabase.table("babies").select("*").eq("user_id", user_id).execute()
    babies_context = babies_response.data or []
    # print(f"👶 Bebés en contexto disponible: {len(babies_context)}")
    
    # Determinar el bebé activo y calcular su edad en meses
    active_baby = None
    baby_age_months = None
    target_baby_id = None
    target_baby_name = "tu bebé"
    
    if payload.baby_id:
        # Buscar el bebé específico del payload
        active_baby = next((b for b in babies_context if b['id'] == payload.baby_id), None)
        target_baby_id = payload.baby_id
        if active_baby:
            target_baby_name = active_baby.get('name', target_baby_name)
    elif babies_context:
        # Usar el primer bebé si no se especificó
        active_baby = babies_context[0]
        target_baby_id = active_baby['id']
        target_baby_name = active_baby.get('name', target_baby_name)
    
    if active_baby and active_baby.get('birthdate'):
        from ..utils.date_utils import calcular_meses
        baby_age_months = calcular_meses(active_baby['birthdate'])
        print(f"👶 [AGE] Bebé activo: {active_baby.get('name', 'Sin nombre')} - Edad: {baby_age_months} meses")
    
    # Preparar keywords del perfil para confirmación (NO guardar automáticamente)
    profile_keywords_pending = None
    profile_extraction_result = None

    def with_profile_meta(response: dict) -> dict:
        """Adjunta información del perfil detectado a la respuesta."""
        enriched = dict(response)
        enriched.setdefault("profile_keywords", profile_keywords_pending)
        enriched.setdefault("profile_extraction", profile_extraction_result)
        return enriched

    # Verificar si es una respuesta de confirmación de preferencias (KNOWLEDGE)
    knowledge_confirmation_result = await handle_knowledge_confirmation(user_id, payload.message)
    if knowledge_confirmation_result:
        return with_profile_meta(knowledge_confirmation_result)

    # Verificar si es una respuesta de confirmación de RUTINA
    routine_confirmation_result = await handle_routine_confirmation(user_id, payload.message)
    if routine_confirmation_result:
        return with_profile_meta(routine_confirmation_result)

    message_text = payload.message.strip()
    simple_greeting = is_simple_greeting(message_text)
    message_lower = payload.message.lower()
    profile_trigger_method = None

    if not simple_greeting:
        if should_trigger_profile_extraction(payload.message):
            profile_trigger_method = "heuristic"
        elif should_trigger_profile_extraction_llm(payload.message):
            profile_trigger_method = "llm"

    if profile_trigger_method:
        try:
            extracted_profile = extract_profile_info(payload.message)
            profile_data = extracted_profile.model_dump()
            filtered_profile_fields = {
                field: value
                for field, value in profile_data.items()
                if field != "confidence" and value
            }

            if filtered_profile_fields:
                profile_extraction_result = {
                    "baby_id": target_baby_id,
                    "baby_name": target_baby_name,
                    "data": filtered_profile_fields,
                    "triggered_by": profile_trigger_method,
                }
                print(f"🧠 [PROFILE_EXTRACTOR] Datos detectados mediante {profile_trigger_method}.")
                for field, value in filtered_profile_fields.items():
                    print(f"   • Campo '{field}' = {value}")
                if not target_baby_id:
                    print("⚠️ [PROFILE_EXTRACTOR] No se encontró baby_id para asociar la extracción.")
                else:
                    keyword_entries = []
                    for field, value in filtered_profile_fields.items():
                        keyword_entries.append({
                            "category": "profile_extractor",
                            "subcategory": field,
                            "field": field,
                            "field_key": field,
                            "keyword": value,
                            "source": "profile_extractor",
                            "profile_field": field,
                            "profile_value": value,
                        })

                    if keyword_entries:
                        profile_keywords_pending = {
                            "baby_id": target_baby_id,
                            "baby_name": target_baby_name,
                            "keywords": keyword_entries,
                            "count": len(keyword_entries),
                            "source": "profile_extractor",
                        }
                        print(f"📝 [PROFILE_EXTRACTOR] Preparadas {len(keyword_entries)} entradas para confirmación.")
                    else:
                        print("ℹ️ [PROFILE_EXTRACTOR] Sin entradas válidas para confirmar.")
            else:
                print("ℹ️ [PROFILE_EXTRACTOR] Se activó el extractor pero no se encontraron campos.")
        except Exception as e:
            print(f"❌ [PROFILE_EXTRACTOR] Error ejecutando extractor: {e}")

    # Contexto RAG, perfiles/bebés e historial de conversación
    rag_context = ""
    specialized_rag = ""
    needs_night_weaning = needs_partner = needs_behavior = needs_routine = False

    if not simple_greeting:
        print(f"📝 Mensaje del usuario: '{payload.message[:100]}...'")
        
        # Verificar si es una consulta de referencias ANTES de hacer búsqueda RAG
        is_reference_query = ReferenceDetector.detect_reference_query(payload.message)
        # print(f"🔍 [DEBUG] ¿Es consulta de referencias? {is_reference_query}")
        
        if is_reference_query:
            # print(f"🔍 [REFERENCIAS] Detectada consulta de referencias - NO se guardará en cache")
            # Para consultas de referencias, usar búsqueda simple sin guardar en cache
            rag_context = get_rag_context_simple(payload.message, search_id="reference_query")
            consulted_sources = []  # No guardar fuentes para consultas de referencias
        else:
            # Para consultas normales, usar búsqueda completa y guardar en cache
            rag_context, consulted_sources = get_rag_context(payload.message, search_id="user_query")
            
            # Guardar las fuentes consultadas en el cache para futuras consultas de referencias
            source_cache.store_sources(user_id, consulted_sources, payload.message, "user_query")
    else:
        is_reference_query = False
        # print(f"👋 [DEBUG] Es saludo simple - no se procesa RAG ni cache")
        
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
    )

    # Construir el prompt optimizado (separa base de contexto dinámico)
    system_prompt_data = await build_system_prompt(
        payload, user_context, routines_context, combined_rag_context, user["id"], target_baby_id
    )
    base_system_prompt = system_prompt_data["base_system_prompt"]
    dynamic_context = system_prompt_data["dynamic_context"]

    # Si es una consulta de referencias, manejarla directamente sin pasar por LLM
    if not simple_greeting and is_reference_query:
        print(f"🔍 [REFERENCIAS] Procesando consulta de referencias")
        reference_response = await ReferenceDetector.handle_reference_query(payload.message, user_id)
        return with_profile_meta({"answer": reference_response, "usage": {}})

    # Construcción del body con prompt optimizado
    messages = build_chat_prompt(
        base_system_prompt=base_system_prompt,
        dynamic_context=dynamic_context,
        history=history,
        user_message=payload.message
    )
    
    # print(formatted_system_prompt)
    # print(messages)

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
                return with_profile_meta({
                    "answer": "Lo siento, el sistema está experimentando demoras. Por favor, intenta reformular tu pregunta de manera más breve o inténtalo de nuevo en unos momentos.",
                    "usage": {}
                })
            # Esperar antes del siguiente intento
            import asyncio
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
            continue
        except Exception as e:
            print(f"❌ Error inesperado en intento {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return with_profile_meta({
                    "answer": "Hubo un problema técnico. Por favor, intenta de nuevo en unos momentos.",
                    "usage": {}
                })
            continue

    data = resp.json()
    assistant = data.get("choices", [])[0].get("message", {}).get("content", "")
    
    # Formatear la respuesta para mayor naturalidad
    #assistant = format_llm_output(assistant)
    
    usage = data.get("usage", {})
    # Variables para controlar el flujo de detección dual
    routine_detected_and_saved = False
    assistant_with_routine_confirmation = ""

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
            
            return with_profile_meta({
                "answer": assistant_with_confirmation, 
                "usage": usage
            })
        
    except Exception as e:
        print(f"Error en detección de conocimiento: {e}")
        import traceback
        traceback.print_exc()
        # Continuar normalmente si falla la detección
        pass

    return with_profile_meta({
        "answer": assistant, 
        "usage": usage
    })
