# src/routes/chat.py
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from ..models.chat import ChatRequest, KnowledgeConfirmRequest
from ..auth import get_current_user
from src.rag.utils import get_rag_context
from src.utils.date_utils import calcular_edad, calcular_meses
from ..rag.retriever import supabase
from ..utils.knowledge_detector import KnowledgeDetector
from ..services.knowledge_service import BabyKnowledgeService
from ..utils.knowledge_cache import confirmation_cache
from ..utils.routine_detector import RoutineDetector
from ..services.routine_service import RoutineService
from ..utils.routine_cache import routine_confirmation_cache

router = APIRouter()
today = datetime.now().strftime("%d/%m/%Y %H:%M")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

if not OPENAI_KEY:
    raise RuntimeError("Falta OPENAI_API_KEY en variables de entorno (.env)")

async def get_user_profiles_and_babies(user_id, supabase_client):
    profiles = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
    babies = supabase_client.table("babies").select("*").eq("user_id", user_id).execute()

    # Obtener conocimiento específico de todos los bebés
    knowledge_by_baby = await BabyKnowledgeService.get_all_user_knowledge(user_id)
    knowledge_context = BabyKnowledgeService.format_knowledge_for_context(knowledge_by_baby)
    
    # Obtener rutinas de todos los bebés
    routines_by_baby = await RoutineService.get_all_user_routines(user_id)
    routines_context = RoutineService.format_routines_for_context(routines_by_baby)

    profile_texts = [
        f"- Perfil: {p['name']}, fecha de nacimiento {p['birthdate']}, alimentación: {p.get('feeding', 'N/A')}"
        for p in profiles.data
    ] if profiles.data else []

    baby_texts = []
    if babies.data:
        for b in babies.data:
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

async def get_conversation_history(user_id, supabase_client, limit_per_role=5):
    """
    Recupera los últimos mensajes del usuario y del asistente para mantener contexto en la conversación.
    """
    user_msgs = supabase_client.table("conversations") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("role", "user") \
        .order("created_at", desc=True) \
        .limit(limit_per_role) \
        .execute()

    assistant_msgs = supabase_client.table("conversations") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("role", "assistant") \
        .order("created_at", desc=True) \
        .limit(limit_per_role) \
        .execute()

    # Combinar y ordenar cronológicamente
    history = (user_msgs.data or []) + (assistant_msgs.data or [])
    history_sorted = sorted(history, key=lambda x: x["created_at"])

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

    # Contexto RAG, perfiles/bebés e historial de conversación
    rag_context = await get_rag_context(payload.message)
    user_context, routines_context = await get_user_profiles_and_babies(user["id"], supabase)
    history = await get_conversation_history(user["id"], supabase)  # 👈 historial del backend

    #print(f"📚 Contexto RAG recuperado:\n{rag_context[:500]}...\n")
    
    # Prompt de sistema
    system_prompt = (
        "Eres Lumi, un acompañante especializado en crianza respetuosa para madres y padres. "
        "Tu estilo es cálido, cercano y profesional, con respuestas estructuradas y específicas. "
        
        "## METODOLOGÍA DE RESPUESTA:\n"
        "1. **CONTEXTUALIZACIÓN**: Siempre inicia mencionando la edad específica del niño/a y explica por qué es relevante para la consulta\n"
        "2. **FUNDAMENTOS**: Explica brevemente el 'por qué' desde el desarrollo neurológico, emocional o conductual\n"
        "3. **PUNTOS CLAVE**: Organiza la información en secciones claras con emojis (🔎 Puntos clave, ✅ Estrategias, 📌 Cuándo consultar)\n"
        "4. **ESTRATEGIAS CONCRETAS**: Proporciona acciones específicas y realistas, no generalidades\n"
        "5. **PREGUNTA DE SEGUIMIENTO**: Termina con una pregunta que profundice en la situación específica\n\n"
        
        "## DIRECTRICES ESPECÍFICAS:\n"
        "- Usa SIEMPRE la información del contexto de documentos cuando sea relevante\n"
        "- Menciona conceptos como 'división de responsabilidades', 'autorregulación', 'etapas del desarrollo' cuando aplique\n"
        "- Estructura tus respuestas con subsecciones claras usando emojis\n"
        "- Sé específico sobre rangos de edad y ventanas de desarrollo\n"
        "- Incluye cuándo es normal vs cuándo consultar a un profesional\n"
        "- Usa ejemplos de frases concretas cuando sea útil\n"
        "- Prioriza el vínculo y la comprensión sobre las técnicas de control\n\n"
        
        "## FORMATO ESPECIAL PARA RUTINAS:\n"
        "- Cuando el usuario pregunte sobre rutinas o horarios, SIEMPRE proporciona la información en formato de tabla markdown\n"
        "- Usa este formato exacto: | Hora | Actividad | Detalles |\n"
        "- Incluye horarios específicos en formato HH:MM o rangos HH:MM-HH:MM\n"
        "- Sé específico en los detalles de cada actividad\n"
        "- Ejemplo de formato correcto:\n"
        "  | 15:00-15:20 | Matemáticas | Ejercicios de suma y resta |\n"
        "  | 15:20-15:25 | Descanso | Estirarse y tomar agua |\n\n"
        
        "## TONO Y ESTILO:\n"
        "- Cálido pero informativo, evita ser demasiado casual\n"
        "- No empieces siempre con saludos salvo que el usuario salude primero\n"
        "- Evita el lenguaje académico excesivo pero mantén rigor en los conceptos\n"
        "- Usa markdown para estructura (negritas, listas, emojis)\n\n"
        
        f"La fecha de hoy es {today}. "
        "Cuando analices la edad del niño/a, considera las etapas de desarrollo específicas: "
        "lactantes (0-6m), bebés (6-12m), caminadores (12-24m), preescolares (2-5a), escolares (6-12a), adolescentes (12+a)."
    )

    # Formatear el perfil que viene en el payload
    profile_text = ""
    if payload.profile:
        profile_data = payload.profile
        profile_text = (
            "Perfil actual:\n"
            f"- Fecha de nacimiento: {profile_data.get('dob')}\n"
            f"- Alimentación: {profile_data.get('feeding')}\n"
        )

    # Construcción del body con separación clara de roles
    body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"INFORMACIÓN ESPECÍFICA DEL USUARIO:\n{user_context}"},
            {"role": "system", "content": f"PERFIL ENVIADO EN ESTA CONSULTA:\n{profile_text}"},
            {"role": "system", "content": f"CONTEXTO DE RUTINAS:\n{routines_context}"},
            {"role": "system", "content": f"CONOCIMIENTO DE DOCUMENTOS EXPERTOS (úsalo como base teórica cuando sea relevante):\n\n{rag_context}\n\nIMPORTANTE: Este contexto proviene de libros especializados en crianza. Úsalo para fundamentar tus respuestas con conceptos como división de responsabilidades, autorregulación, desarrollo neurológico, etc."},
            *history,  
            {"role": "user", "content": payload.message},
        ],
        "max_tokens": 1200,
        "temperature": 0.3,
    }

    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers)

    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail={"openai_error": resp.text})

    data = resp.json()
    assistant = data.get("choices", [])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})

    # Variables para controlar el flujo de detección dual
    routine_detected_and_saved = False
    assistant_with_routine_confirmation = ""

    # PRIMERA PRIORIDAD: Detectar rutinas en el mensaje del usuario
    try:
        print(f"� Analizando mensaje para rutinas: {payload.message}")
        
        # Usar el mismo contexto de bebés
        babies = supabase.table("babies").select("*").eq("user_id", user_id).execute()
        babies_context = babies.data or []
        
        # Analizar el mensaje para detectar información de rutinas
        detected_routine = await RoutineDetector.analyze_message(
            payload.message, 
            babies_context
        )
        print(f"🕐 Rutina detectada: {detected_routine}")
        
        # Si se detecta una rutina, guardar en caché y preguntar confirmación
        if detected_routine and RoutineDetector.should_ask_confirmation(detected_routine):
            print("✅ Se debe preguntar confirmación de rutina")
            
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
            print("❌ No se debe preguntar confirmación de rutina")
        
    except Exception as e:
        print(f"Error en detección de rutinas: {e}")
        import traceback
        traceback.print_exc()
        # Continuar normalmente si falla la detección
        pass

    # SEGUNDA PRIORIDAD: Detectar conocimiento importante en el mensaje del usuario
    try:
        print(f"� Analizando mensaje para conocimiento: {payload.message}")
        
        # Obtener información de bebés para el contexto
        babies = supabase.table("babies").select("*").eq("user_id", user_id).execute()
        babies_context = babies.data or []
        print(f"👶 Bebés encontrados: {len(babies_context)}")
        
        # Analizar el mensaje para detectar información importante
        detected_knowledge = await KnowledgeDetector.analyze_message(
            payload.message, 
            babies_context
        )
        print(f"🧠 Conocimiento detectado: {detected_knowledge}")
        
        # Si se detecta conocimiento importante, guardar en caché y preguntar
        if detected_knowledge and KnowledgeDetector.should_ask_confirmation(detected_knowledge):
            print("✅ Se debe preguntar confirmación")
            
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
            print("❌ No se debe preguntar confirmación de conocimiento")
        
    except Exception as e:
        print(f"Error en detección de conocimiento: {e}")
        import traceback
        traceback.print_exc()
        # Continuar normalmente si falla la detección
        pass

    return {"answer": assistant, "usage": usage}


