# src/services/chat_service.py
import json
import traceback
from datetime import datetime
from pathlib import Path
from ..rag.retriever import supabase

# Constantes necesarias para build_system_prompt
today = datetime.now().strftime("%d/%m/%Y %H:%M")

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SECTIONS_DIR = PROMPTS_DIR / "sections"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples" 

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

async def build_system_prompt(payload, user_context, combined_rag_context, user_id=None):
    """
    Construye el prompt del sistema completo con todas las secciones necesarias.
    """
    
    # Cargar y formatear el prompt maestro
    system_prompt_template = load_system_prompt()
    
    # Cargar dataset de ejemplos Lumi
    instruction_dataset = load_example_dataset()

    # Siempre agregar dataset general de ejemplos Lumi (v1)
    if instruction_dataset:
        system_prompt_template += "\n\n" + instruction_dataset
        print(f"📚 Dataset de ejemplos Lumi cargado correctamente - {len(instruction_dataset)} caracteres")
    else:
        print("⚠️ No se pudo cargar el dataset de ejemplos Lumi")

    # Obtener y formatear el perfil detallado de los bebés
    profile_text = ""
    if user_id:
        try:
            # Obtener información completa de los bebés con sus perfiles
            babies_with_profiles = await get_baby_profile(user_id)
            if babies_with_profiles:
                # Usar la función existente para formatear el contexto del perfil
                profile_text = format_baby_profile_for_context(babies_with_profiles, lang='es')
                print(f"✅ Perfil de bebé cargado: {len(babies_with_profiles)} bebe")
            else:
                print("⚠️ No se encontraron bebés con perfiles para este usuario")
        except Exception as e:
            print(f"❌ Error obteniendo perfil de bebés: {e}")
            profile_text = ""
    
    # Agregar perfil básico del payload si existe (como fallback)
    if payload.profile and not profile_text:
        profile_data = payload.profile
        profile_text = (
            "**Perfil básico en esta consulta:**\n"
            f"- Fecha de nacimiento: {profile_data.get('dob')}\n"
        )
    
    # Cantidad de caracteres que se le pasará del rag al prompt, de conocimiento
    max_rag_length = 10000
    if len(combined_rag_context) > max_rag_length:
        combined_rag_context = combined_rag_context[:max_rag_length] + "...\n[Contexto truncado por longitud]"
    
    formatted_system_prompt = system_prompt_template.format(
        today=today,
        user_context=user_context if user_context else "No hay información específica del usuario disponible.",
        profile_context=profile_text if profile_text else "No se proporcionó perfil específico en esta consulta.",
        rag_context=combined_rag_context if combined_rag_context else "No hay contexto especializado disponible para esta consulta."
    )

    # Agregar instrucción específica sobre originalidad de formato
    formatted_system_prompt += "\n\n" + """
        ## INSTRUCCIÓN CRÍTICA SOBRE FORMATO:
        - NO copies la estructura, formato o estilo de mensajes anteriores en el historial
        - Cada respuesta debe ser ORIGINAL y específica para la consulta actual
        - Varía tu estructura: usa párrafos fluidos, listas simples, o formato según el contenido
        - Responde de forma natural y conversacional, no como una plantilla rígida
    """
        
    # Log de longitud del prompt para debug
    prompt_length = len(formatted_system_prompt)
    print(f"📏 Longitud del prompt del sistema: {prompt_length} caracteres")
        
    return formatted_system_prompt
