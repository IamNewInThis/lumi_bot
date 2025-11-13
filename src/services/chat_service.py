# src/services/chat_service.py
import json
import traceback
from datetime import datetime
from pathlib import Path
from ..rag.retriever import supabase
from ..services.knowledge_service import BabyKnowledgeService
from ..utils.knowledge_cache import confirmation_cache
from ..services.routine_service import RoutineService
from ..utils.routine_cache import routine_confirmation_cache
from ..utils.knowledge_detector import KnowledgeDetector

# Constantes necesarias para build_system_prompt
today = datetime.now().strftime("%d/%m/%Y %H:%M")

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SECTIONS_DIR = PROMPTS_DIR / "sections"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples" 

# Keywords copiadas de chat.py
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
    "reducir tomas", "eliminar tomas nocturnas", "dormir sin mamar",
    "dormir toda la noche", "no despertar para comer", "destete gradual",
    "quitar toma nocturna", "destetar por la noche", "no alimentar de noche"
}

BEHAVIOR_KEYWORDS = {
    "berrinche", "berrinches", "rabieta", "rabietas", "llanto excesivo",
    "llanto intenso", "llanto sin razón", "lloriqueo", "capricho", "caprichos",
    "no obedece", "rebelde", "desafiante", "comportamiento difícil",
    "conducta", "disciplina", "límites", "reglas", "portarse mal",
    "mal comportamiento", "agresivo", "agresividad", "golpea", "muerde",
    "pega", "empuja", "no hace caso", "desobediente"
}

PARTNER_KEYWORDS = {
    "pareja", "papá", "papá no", "mi esposo", "mi marido", "mi novio",
    "mi pareja", "padre", "abuelo", "suegra", "suegro", "familia",
    "no entiende", "no ayuda", "discutimos", "diferencias", "conflicto",
    "apoyo", "involucrar", "participar", "roles", "responsabilidades"
}

def load_example_dataset():
    """
    Carga el dataset de ejemplos JSONL desde src/examples.
    Convierte las conversaciones JSON a formato texto para el system prompt.
    """
    dataset_path = EXAMPLES_DIR / "lumi_instruction_dataset_v1.jsonl"
    
    if not dataset_path.exists():
        print(f"⚠️ Dataset no encontrado: {dataset_path}")
        return ""
    
    header = "## DATASET DE EJEMPLOS LUMI (v1)\nUsar como guía de referencia para la generación de respuestas.\n\n"
    
    try:
        examples_text = []
        with open(dataset_path, "r", encoding="utf-8") as jsonl_file:
            for line_num, line in enumerate(jsonl_file, 1):
                if line.strip():
                    data = json.loads(line)
                    if "messages" in data:
                        example_text = f"### Ejemplo {line_num}:\n"
                        for msg in data["messages"]:
                            role = msg.get("role", "unknown").upper()
                            content = msg.get("content", "").strip()
                            if content:
                                example_text += f"**{role}**: {content}\n\n"
                        examples_text.append(example_text)
        
        if examples_text:
            content = "\n".join(examples_text)
            print(f"📚 Cargados {len(examples_text)} ejemplos desde {dataset_path.name}")
            return header + content
        else:
            print(f"⚠️ No se pudieron cargar ejemplos desde {dataset_path.name}")
            return ""
                    
    except Exception as e:
        print(f"❌ Error cargando dataset JSONL: {e}")
        return ""

def load_base_system_prompt():
    """
    Carga solo el prompt base esencial, SIN ejemplos ni contexto dinámico.
    Esto mantiene el system prompt pequeño y estable.
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
        base_content = f.read().strip()

    # Solo agregar reglas operacionales básicas, NO ejemplos ni contexto dinámico
    system_dir = base_path.parent
    operational_rules_path = system_dir / "system_operational_rules.md"
    
    if operational_rules_path.exists():
        with open(operational_rules_path, "r", encoding="utf-8") as f:
            base_content += "\n\n" + f.read().strip()

    return base_content

def build_dynamic_context(user_context: str, profile_text: str, routines_context: str, 
                         combined_rag_context: str, specific_sections: list = None):
    """
    Construye el contexto dinámico que se enviará como parte del mensaje del usuario.
    Esto no cuenta contra el límite del system prompt.
    """
    context_parts = []
    
    # Información del usuario y bebés
    if user_context:
        context_parts.append(f"📋 INFORMACIÓN DEL USUARIO:\n{user_context}")
    
    # Perfil de los bebés (resumido)
    if profile_text:
        # Truncar si es muy largo
        if len(profile_text) > 2000:
            profile_text = profile_text[:2000] + "\n... [Perfil truncado]"
        context_parts.append(f"👶 PERFIL DE LOS BEBÉS:\n{profile_text}")
    
    # Rutinas (resumidas)
    if routines_context:
        if len(routines_context) > 1500:
            routines_context = routines_context[:1500] + "\n... [Rutinas truncadas]"
        context_parts.append(f"🕐 RUTINAS ESTABLECIDAS:\n{routines_context}")
    
    # Contexto RAG (limitado)
    if combined_rag_context:
        max_rag_length = 3000  # Reducido de 10000
        if len(combined_rag_context) > max_rag_length:
            combined_rag_context = combined_rag_context[:max_rag_length] + "\n... [Contexto RAG truncado]"
        context_parts.append(f"📚 CONOCIMIENTO RELEVANTE:\n{combined_rag_context}")
    
    # Secciones específicas (comportamiento, rutinas, etc.)
    if specific_sections:
        sections_text = load_specific_sections(specific_sections)
        if sections_text:
            context_parts.append(f"🎯 GUÍAS ESPECÍFICAS:\n{sections_text}")
    
    return "\n\n".join(context_parts) if context_parts else ""

def load_specific_sections(section_files: list) -> str:
    """Carga secciones específicas de forma compacta"""
    if not section_files:
        return ""
    
    parts = []
    seen = set()
    
    for filename in section_files:
        if filename in seen:
            continue
        seen.add(filename)
        
        section_path = SECTIONS_DIR / filename
        if section_path.exists():
            with open(section_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Limitar tamaño de cada sección
                if len(content) > 800:
                    content = content[:800] + "\n... [Sección truncada]"
                parts.append(f"### {filename.replace('.md', '').title()}\n{content}")
    
    return "\n\n".join(parts)
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
    
    # Mapeo de tipos de consulta y sus templates correspondientes
    consultation_types = {
        "pediatra": ["quiero ir al pediatra", "llevar al pediatra", "consulta médica", 
                    "visita médica", "cita con el doctor", "ir al doctor"],
        "feeding": ["no quiere comer", "problemas para comer", "rechazo comida", 
                   "alimentación", "blw", "baby led weaning", "destete"],
        "sleep": ["no duerme", "problemas de sueño", "dormir", "sueño", "insomnio bebé", 
                 "despertar nocturno", "regresión del sueño"],
        "development": ["desarrollo", "hitos", "cuándo camina", "cuándo habla", 
                       "gatear", "sentarse", "primeras palabras"]
    }
    
    # Detectar tipo de consulta
    detected_type = None
    for consultation_type, keywords in consultation_types.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_type = consultation_type
            break
    
    if not detected_type:
        return ""
    
    # Buscar template correspondiente
    template_path = TEMPLATES_DIR / f"{detected_type}.md"
    
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as template_file:
            template_content = template_file.read().strip()
            return f"\n\n## TEMPLATE ESPECÍFICO - {detected_type.upper()}\n{template_content}"
    
    return ""

def build_chat_prompt(base_system_prompt: str, dynamic_context: str, history: list, user_message: str):
    """
    Construye un prompt estructurado para Lumi optimizado para reducir tokens del system prompt.
    Separa el prompt base (estático) del contexto dinámico (perfiles, RAG, etc.)
    """
    
    # System prompt solo con instrucciones básicas (más pequeño)
    messages = [
        {"role": "system", "content": base_system_prompt}
    ]
    
    # Contexto dinámico como mensaje del usuario (no cuenta como system prompt)
    if dynamic_context:
        messages.append({
            "role": "user", 
            "content": f"CONTEXTO PARA ESTA CONSULTA:\n{dynamic_context}\n\n---\n\nMi consulta real es: {user_message}"
        })
    else:
        messages.append({"role": "user", "content": user_message})
    
    # Agregar historial si existe (con límite)
    if history:
        # Limitar historial a los últimos N mensajes para reducir tokens
        recent_history = history[-6:] if len(history) > 6 else history
        messages.extend(recent_history)
    
    return messages

async def handle_knowledge_confirmation(user_id: str, message: str):
    """
    Maneja la confirmación de conocimiento pendiente.
    Retorna None si no hay confirmación pendiente, o la respuesta si la hay.
    """
    confirmation_response = confirmation_cache.is_confirmation_response(message)
    if confirmation_response is None or not confirmation_cache.has_pending_confirmation(user_id):
        return None

    print(f"🎯 Detectada respuesta de confirmación de conocimiento: {confirmation_response}")

    pending_data = confirmation_cache.get_pending_confirmation(user_id)
    if not pending_data:
        return None

    if confirmation_response:
        try:
            saved_items = []

            for knowledge_item in pending_data["knowledge"]:
                baby_id = await BabyKnowledgeService.find_baby_by_name(
                    user_id,
                    knowledge_item.get("baby_name", ""),
                )

                if baby_id:
                    knowledge_data = {
                        "category": knowledge_item["category"],
                        "subcategory": knowledge_item.get("subcategory"),
                        "title": knowledge_item["title"],
                        "description": knowledge_item["description"],
                        "importance_level": knowledge_item.get("importance_level", 1),
                    }

                    saved_item = await BabyKnowledgeService.save_knowledge(
                        user_id,
                        baby_id,
                        knowledge_data,
                    )
                    saved_items.append(saved_item)

            confirmation_cache.clear_pending_confirmation(user_id)

            response_text = (
                f"✅ ¡Perfecto! He guardado {len(saved_items)} elemento(s) en el perfil. "
                "Ahora podré darte respuestas más personalizadas considerando esta información."
            )

            return {"answer": response_text, "usage": {}}

        except Exception as e:
            print(f"Error guardando conocimiento confirmado: {e}")
            confirmation_cache.clear_pending_confirmation(user_id)
            return {
                "answer": "❌ Hubo un error guardando la información. Por favor intenta de nuevo.",
                "usage": {},
            }

    confirmation_cache.clear_pending_confirmation(user_id)
    return {"answer": "👌 Entendido, no guardaré esa información.", "usage": {}}

async def handle_routine_confirmation(user_id: str, message: str):
    """
    Maneja la confirmación de rutinas pendientes.
    Retorna None si no hay confirmación pendiente, o la respuesta si la hay.
    """
    routine_confirmation_response = routine_confirmation_cache.is_confirmation_response(message)
    if routine_confirmation_response is None or not routine_confirmation_cache.has_pending_confirmation(user_id):
        return None

    print(f"🎯 Detectada respuesta de confirmación de rutina: {routine_confirmation_response}")
    
    pending_routine_data = routine_confirmation_cache.get_pending_confirmation(user_id)
    if not pending_routine_data:
        return None

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


async def detect_routine_in_response(user_id: str, assistant_response: str, babies_context: list):
    """
    Detecta rutinas estructuradas en la respuesta de Lumi usando método simple.
    Retorna None si no se detecta rutina, o mensaje de confirmación si se detecta.
    """
    try:
        print(f"🔍 Analizando respuesta de Lumi para rutinas (método simple)...")
        
        # 1. Detectar horarios estructurados
        import re
        time_patterns = re.findall(r'\*\*\d{1,2}:\d{2}[–-]\d{1,2}:\d{2}\*\*', assistant_response)
        
        # 2. Detectar palabras clave de rutina
        routine_indicators = [
            "rutina diaria", "rutina para", "🧭", "🌅", "mañana", "mediodía", "tarde", "noche",
            "despertar", "desayuno", "almuerzo", "siesta", "cena", "baño",
            "resumen visual", "bloques", "actividad principal"
        ]
        found_indicators = sum(1 for indicator in routine_indicators if indicator in assistant_response.lower())
        
        # 3. Criterios simples para detectar rutina
        has_structured_times = len(time_patterns) >= 3
        has_routine_content = found_indicators >= 5
        
        print(f"⏰ Horarios encontrados: {len(time_patterns)}")
        print(f"📋 Indicadores de rutina: {found_indicators}")
        print(f"🎯 Es rutina estructurada: {has_structured_times and has_routine_content}")
        
        if has_structured_times and has_routine_content:
            print("✅ Rutina detectada con método simple - Agregando confirmación")
            
            # Obtener información de bebés
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
            routine_confirmation_cache.set_pending_confirmation(user_id, simple_routine, assistant_response)
            
            confirmation_message = f"¿Te parece si guardo esta rutina para {baby_name} en su perfil para futuras conversaciones?"
            return confirmation_message
        else:
            print("❌ No es una rutina estructurada según criterios simples")
            return None
            
    except Exception as e:
        print(f"Error en detección simple de rutinas: {e}")
        return None

async def detect_knowledge_in_message(user_id: str, message: str, babies_context: list, selected_baby_id: str = None):
    """
    Detecta conocimiento importante en el mensaje del usuario.
    Retorna None si no se detecta conocimiento, o mensaje de confirmación si se detecta.
    """
    try:
        print(f"🧠 Analizando mensaje para conocimiento: {message}")
        
        # Analizar el mensaje para detectar información importante
        detected_knowledge = await KnowledgeDetector.analyze_message(
            message, 
            babies_context
        )
        print(f"🧠 Conocimiento detectado: {detected_knowledge}")

        # Enriquecer nombres genéricos con nombres reales del contexto
        KnowledgeDetector.enrich_baby_names(
            detected_knowledge,
            babies_context=babies_context,
            original_message=message
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
            print("✅ Se debe preguntar confirmación")
            
            # Guardar en caché para confirmación posterior
            confirmation_cache.set_pending_confirmation(user_id, detected_knowledge, message)
            
            confirmation_message = KnowledgeDetector.format_confirmation_message(detected_knowledge)
            return confirmation_message
        else:
            print("❌ No se debe preguntar confirmación de conocimiento")
            return None
        
    except Exception as e:
        print(f"Error en detección de conocimiento: {e}")
        import traceback
        traceback.print_exc()
        return None

async def get_baby_profile(user_id: str, baby_id: str = None):
    """
    Obtiene información detallada de un bebé específico del usuario incluyendo su perfil
    desde las tablas babies, baby_profile, baby_profile_value y profile_category.
    
    Args:
        user_id: ID del usuario
        baby_id: ID específico del bebé (opcional). Si no se proporciona, retorna el primer bebé.
    
    Retorna:
        Diccionario con información del bebé específico y su perfil detallado por categorías.
        Ejemplo de estructura retornada:
        {
            "id": "uuid",
            "name": "Jacinta", 
            "birthdate": "2025-05-08",
            "gender": "female",
            "profile": {
                "sleep and rest": {
                    "sleep_location": {"value_es": "cuna", "value_en": "crib"},
                    "day_night_difference": {"value_es": "comienza a distinguir", "value_en": "starting to distinguish"}
                },
                "daily cares": {
                    "dental_care_type": {"value_es": "pasta sin flúor", "value_en": "toothpaste without fluoride"}
                }
            }
        }
        
        Retorna None si no se encuentra el bebé específico.
    """
    try:
        # Usar función RPC optimizada para obtener bebés con perfil completo
        response = supabase.rpc('get_babies_with_profile_data', {
            'p_user_id': user_id
        }).execute()
        
        if response.data is None:
            print(f"👶 No se encontraron bebés para user_id: {user_id}")
            return None
        
        babies_data = response.data
        
        # Si se especificó un baby_id, buscar ese bebé específico
        if baby_id:
            selected_baby = next((baby for baby in babies_data if baby.get('id') == baby_id), None)
            if selected_baby:
                print(f"👶 Obtenido perfil del bebé específico: {selected_baby.get('name', 'Sin nombre')} (ID: {baby_id})")
                return selected_baby
            else:
                print(f"⚠️ No se encontró bebé con ID: {baby_id} para user_id: {user_id}")
                # Fallback al primer bebé si el baby_id no se encuentra
                if babies_data:
                    first_baby = babies_data[0]
                    print(f"🔄 Usando primer bebé disponible: {first_baby.get('name', 'Sin nombre')} (ID: {first_baby.get('id')})")
                    return first_baby
                return None
        else:
            # Si no se especificó baby_id, usar el primer bebé disponible
            if babies_data:
                first_baby = babies_data[0]
                print(f"👶 Usando primer bebé disponible: {first_baby.get('name', 'Sin nombre')} (ID: {first_baby.get('id')})")
                return first_baby
            
        print(f"👶 No se encontraron bebés para user_id: {user_id}")
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener el perfil del bebé: {e}")
        import traceback
        traceback.print_exc()
        return None

def format_baby_profile_for_context(baby_data, lang: str = 'es') -> str:
    """
    Formatea la información de perfil de un bebé específico para incluir en el system prompt.
    
    Args:
        baby_data: Puede ser un diccionario con información de un bebé individual, 
                  o una lista de bebés (para mantener compatibilidad)
        lang: Idioma para mostrar los valores ('es', 'en', 'pt')
    
    Returns:
        String formateado con la información de perfil del bebé específico
    """
    # Manejar tanto un bebé individual como una lista de bebés
    if baby_data is None:
        return "No hay información de perfil disponible."
    
    if isinstance(baby_data, dict):
        # Es un bebé individual
        babies_data = [baby_data]
    elif isinstance(baby_data, list):
        # Es una lista de bebés (compatibilidad)
        babies_data = baby_data
    else:
        return "Formato de datos de bebé no válido."
    
    if not babies_data:
        return "No hay información de perfil disponible."
    
    formatted_profiles = []
    
    for baby in babies_data:
        baby_name = baby.get('name', 'Bebé sin nombre')
        baby_age = baby.get('birthdate', '')
        profile_data = baby.get('profile', {})
        
        if not profile_data:
            # Si no hay perfil, al menos mostrar información básica
            formatted_profiles.append(f"👶 **{baby_name}** ({baby_age}) - Sin perfil detallado disponible")
            continue
        
        baby_profile_lines = [f"👶 **{baby_name}** ({baby_age})"]
        
        for category, category_data in profile_data.items():
            if category_data:  # Solo mostrar si hay datos
                baby_profile_lines.append(f"  📂 {category.title()}:")
                
                for key, values in category_data.items():
                    # Obtener valor en el idioma especificado, con fallback a español
                    value_key = f'value_{lang}'
                    display_value = values.get(value_key) or values.get('value_es') or 'N/A'
                    
                    # Formatear key para que sea más legible
                    formatted_key = key.replace('_', ' ').title()
                    baby_profile_lines.append(f"    • {formatted_key}: {display_value}")
        
        if len(baby_profile_lines) > 1:  # Solo agregar si tiene contenido además del nombre
            formatted_profiles.append('\n'.join(baby_profile_lines))
    
    if formatted_profiles:
        # Usar singular si es un solo bebé, plural si son múltiples
        header = "## PERFIL DETALLADO DEL BEBÉ:" if len(babies_data) == 1 else "## PERFILES DETALLADOS DE LOS BEBÉS:"
        return header + "\n\n" + '\n\n'.join(formatted_profiles)
    else:
        return "El bebé no tiene información de perfil detallada disponible."

async def build_system_prompt(payload, user_context, routines_context, combined_rag_context, user_id=None, baby_id=None):
    """
    Construye el prompt del sistema OPTIMIZADO - separa contenido base de contexto dinámico.
    Retorna tanto el system prompt base como el contexto dinámico por separado.
    
    Args:
        payload: Objeto de request con el mensaje del usuario
        user_context: Contexto general del usuario
        routines_context: Contexto de rutinas
        combined_rag_context: Contexto de knowledge/RAG
        user_id: ID del usuario
        baby_id: ID específico del bebé (opcional). Si no se proporciona, usa el primer bebé disponible.
    """
    message_lower = payload.message.lower()
    
    # Determinar qué secciones específicas necesitamos
    needed_sections = []
    if any(keyword in message_lower for keyword in BEHAVIOR_KEYWORDS):
        needed_sections.append("behavior.md")
    if any(keyword in message_lower for keyword in ROUTINE_KEYWORDS):
        needed_sections.append("routines.md")
    if any(keyword in message_lower for keyword in NIGHT_WEANING_KEYWORDS):
        needed_sections.append("night_weaning.md")
    if any(keyword in message_lower for keyword in PARTNER_KEYWORDS):
        needed_sections.append("partner_support.md")

    # 1. SYSTEM PROMPT BASE (pequeño y estático)
    base_system_prompt = load_base_system_prompt()
    
    # Agregar template específico al system prompt si es necesario
    specific_template = detect_consultation_type_and_load_template(payload.message)
    if specific_template:
        base_system_prompt += specific_template
        print(f"🎯 Template específico agregado al system prompt")

    # 2. CONTEXTO DINÁMICO (se enviará como parte del mensaje del usuario)
    profile_text = ""
    if user_id:
        try:
            # Obtener perfil del bebé específico si se proporciona baby_id
            baby_with_profile = await get_baby_profile(user_id, baby_id)
            if baby_with_profile:
                profile_text = format_baby_profile_for_context(baby_with_profile, lang='es')
                baby_name = baby_with_profile.get('name', 'Bebé')
                baby_selected_id = baby_with_profile.get('id', baby_id or 'N/A')
                print(f"✅ Perfil de bebé específico cargado: {baby_name} (ID: {baby_selected_id})")
            else:
                print(f"⚠️ No se pudo cargar perfil del bebé (user_id: {user_id}, baby_id: {baby_id})")
        except Exception as e:
            print(f"❌ Error obteniendo perfil del bebé: {e}")

    # Agregar perfil básico del payload como fallback
    if payload.profile and not profile_text:
        profile_data = payload.profile
        profile_text = f"Fecha de nacimiento: {profile_data.get('dob', 'N/A')}"

    # Construir contexto dinámico optimizado
    dynamic_context = build_dynamic_context(
        user_context=user_context,
        profile_text=profile_text,
        routines_context=routines_context,
        combined_rag_context=combined_rag_context,
        specific_sections=needed_sections
    )

    # Log de tamaños para optimización
    base_length = len(base_system_prompt)
    dynamic_length = len(dynamic_context)
    print(f"📏 System prompt base: {base_length} caracteres")
    print(f"📏 Contexto dinámico: {dynamic_length} caracteres")
    print(f"� Total optimizado: {base_length + dynamic_length}")

    return {
        "base_system_prompt": base_system_prompt,
        "dynamic_context": dynamic_context,
        "metadata": {
            "base_prompt_length": base_length,
            "dynamic_context_length": dynamic_length,
            "sections": needed_sections,
            "optimization_ratio": (base_length + dynamic_length) / 29273  # Comparación con el anterior
        }
    }
